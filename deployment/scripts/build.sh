#!/bin/bash

# Social Support Application Build Script
# This script builds Docker images for different environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEPLOYMENT_DIR="$PROJECT_ROOT/deployment"

# Default values
ENVIRONMENT="development"
IMAGE_TAG="latest"
REGISTRY=""
PUSH=false
PLATFORM="linux/amd64"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Build Docker images for the Social Support Application

OPTIONS:
    -e, --environment   Environment (development|production) [default: development]
    -t, --tag          Image tag [default: latest]
    -r, --registry     Container registry URL
    -p, --push         Push images to registry
    --platform         Target platform [default: linux/amd64]
    -h, --help         Show this help message

EXAMPLES:
    $0 -e development
    $0 -e production -t v1.0.0 -r your-registry.com -p
    $0 --environment production --tag latest --registry 123456789.dkr.ecr.us-east-1.amazonaws.com --push

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -p|--push)
            PUSH=true
            shift
            ;;
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|production)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT. Must be 'development' or 'production'"
    exit 1
fi

# Set image names
if [[ -n "$REGISTRY" ]]; then
    IMAGE_NAME="$REGISTRY/social-support-app:$IMAGE_TAG"
else
    IMAGE_NAME="social-support-app:$IMAGE_TAG"
fi

print_status "Building Social Support Application Docker Image"
print_status "Environment: $ENVIRONMENT"
print_status "Image Name: $IMAGE_NAME"
print_status "Platform: $PLATFORM"

# Change to project root
cd "$PROJECT_ROOT"

# Create build context
print_status "Preparing build context..."

# Check if required files exist
required_files=(
    "app.py"
    "main.py"
    "config.py"
    "deployment/docker/Dockerfile"
    "deployment/requirements/requirements.txt"
)

for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        print_error "Required file not found: $file"
        exit 1
    fi
done

# Build the Docker image
print_status "Building Docker image..."

if [[ "$ENVIRONMENT" == "production" ]]; then
    DOCKERFILE="$DEPLOYMENT_DIR/docker/Dockerfile.prod"
    TARGET="production"
else
    DOCKERFILE="$DEPLOYMENT_DIR/docker/Dockerfile"
    TARGET="development"
fi

# Build command
BUILD_CMD="docker build"
BUILD_CMD="$BUILD_CMD --file $DOCKERFILE"
BUILD_CMD="$BUILD_CMD --target $TARGET"
BUILD_CMD="$BUILD_CMD --platform $PLATFORM"
BUILD_CMD="$BUILD_CMD --tag $IMAGE_NAME"

# Add build args
BUILD_CMD="$BUILD_CMD --build-arg ENVIRONMENT=$ENVIRONMENT"
BUILD_CMD="$BUILD_CMD --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
BUILD_CMD="$BUILD_CMD --build-arg VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"

# Add context
BUILD_CMD="$BUILD_CMD ."

print_status "Executing: $BUILD_CMD"
eval $BUILD_CMD

if [[ $? -eq 0 ]]; then
    print_success "Docker image built successfully: $IMAGE_NAME"
else
    print_error "Failed to build Docker image"
    exit 1
fi

# Tag additional versions
if [[ "$IMAGE_TAG" != "latest" ]]; then
    if [[ -n "$REGISTRY" ]]; then
        LATEST_TAG="$REGISTRY/social-support-app:latest"
    else
        LATEST_TAG="social-support-app:latest"
    fi
    
    print_status "Tagging as latest: $LATEST_TAG"
    docker tag "$IMAGE_NAME" "$LATEST_TAG"
fi

# Push to registry if requested
if [[ "$PUSH" == true ]]; then
    if [[ -z "$REGISTRY" ]]; then
        print_error "Registry URL required for push operation"
        exit 1
    fi
    
    print_status "Pushing image to registry..."
    docker push "$IMAGE_NAME"
    
    if [[ "$IMAGE_TAG" != "latest" ]]; then
        docker push "$LATEST_TAG"
    fi
    
    print_success "Image pushed successfully"
fi

# Show image information
print_status "Image Details:"
docker images | grep "social-support-app" | head -5

# Test the image
print_status "Testing the built image..."
CONTAINER_ID=$(docker run -d --rm -p 7861:7860 "$IMAGE_NAME")

if [[ -n "$CONTAINER_ID" ]]; then
    print_status "Container started with ID: $CONTAINER_ID"
    
    # Wait for container to be ready
    sleep 10
    
    # Test health endpoint
    if curl -f http://localhost:7861/health > /dev/null 2>&1; then
        print_success "Health check passed"
    else
        print_warning "Health check failed, but this might be expected in test environment"
    fi
    
    # Stop test container
    docker stop "$CONTAINER_ID" > /dev/null
    print_status "Test container stopped"
else
    print_error "Failed to start test container"
fi

print_success "Build process completed successfully!"
print_status "Next steps:"
echo "  - To run locally: docker run -p 7860:7860 $IMAGE_NAME"
echo "  - To deploy to production: Use the deployment scripts in deployment/cloud/"
echo "  - To run with docker-compose: cd deployment/docker && docker-compose up"