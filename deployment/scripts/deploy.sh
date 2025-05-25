#!/bin/bash

# Social Support Application Deployment Script
# Universal deployment script for multiple cloud platforms

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
PLATFORM="docker-compose"
IMAGE_TAG="latest"
REGISTRY=""
NAMESPACE="social-support"
CONFIG_FILE=""

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

Deploy the Social Support Application to various platforms

OPTIONS:
    -e, --environment   Environment (development|production) [default: development]
    -p, --platform      Deployment platform (docker-compose|kubernetes|aws|azure|gcp) [default: docker-compose]
    -t, --tag          Image tag [default: latest]
    -r, --registry     Container registry URL
    -n, --namespace    Kubernetes namespace [default: social-support]
    -c, --config       Configuration file path
    -h, --help         Show this help message

PLATFORMS:
    docker-compose     Deploy using Docker Compose (local development)
    kubernetes         Deploy to Kubernetes cluster
    aws               Deploy to AWS ECS
    azure             Deploy to Azure Container Apps
    gcp               Deploy to Google Cloud Run

EXAMPLES:
    $0 -e development -p docker-compose
    $0 -e production -p kubernetes -t v1.0.0 -r your-registry.com
    $0 -e production -p aws -t latest -r 123456789.dkr.ecr.us-east-1.amazonaws.com

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -p|--platform)
            PLATFORM="$2"
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
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -c|--config)
            CONFIG_FILE="$2"
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

# Validate platform
if [[ ! "$PLATFORM" =~ ^(docker-compose|kubernetes|aws|azure|gcp)$ ]]; then
    print_error "Invalid platform: $PLATFORM"
    show_usage
    exit 1
fi

print_status "Deploying Social Support Application"
print_status "Environment: $ENVIRONMENT"
print_status "Platform: $PLATFORM"
print_status "Image Tag: $IMAGE_TAG"

# Load environment variables
if [[ -n "$CONFIG_FILE" && -f "$CONFIG_FILE" ]]; then
    print_status "Loading configuration from: $CONFIG_FILE"
    source "$CONFIG_FILE"
elif [[ -f "$DEPLOYMENT_DIR/config/.env.$ENVIRONMENT" ]]; then
    print_status "Loading environment configuration..."
    source "$DEPLOYMENT_DIR/config/.env.$ENVIRONMENT"
else
    print_warning "No configuration file found. Using defaults."
fi

# Function to deploy with Docker Compose
deploy_docker_compose() {
    print_status "Deploying with Docker Compose..."
    
    cd "$DEPLOYMENT_DIR/docker"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        COMPOSE_FILE="docker-compose.prod.yml"
    else
        COMPOSE_FILE="docker-compose.yml"
    fi
    
    # Export environment variables
    export IMAGE_TAG
    export REGISTRY
    
    # Pull latest images if registry is specified
    if [[ -n "$REGISTRY" ]]; then
        print_status "Pulling latest images..."
        docker-compose -f "$COMPOSE_FILE" pull
    fi
    
    # Deploy
    print_status "Starting services..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Check health
    if curl -f http://localhost:7860/health > /dev/null 2>&1; then
        print_success "Application deployed successfully!"
        print_status "Application URL: http://localhost:7860"
    else
        print_error "Health check failed"
        docker-compose -f "$COMPOSE_FILE" logs app
        exit 1
    fi
}

# Function to deploy to Kubernetes
deploy_kubernetes() {
    print_status "Deploying to Kubernetes..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    cd "$DEPLOYMENT_DIR/cloud/kubernetes"
    
    # Create namespace
    print_status "Creating namespace: $NAMESPACE"
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply configurations
    print_status "Applying Kubernetes configurations..."
    
    # Replace image references
    if [[ -n "$REGISTRY" ]]; then
        sed -i.bak "s|your-registry/social-support-app:latest|$REGISTRY/social-support-app:$IMAGE_TAG|g" deployment.yml
    fi
    
    # Apply manifests
    kubectl apply -f namespace.yml
    kubectl apply -f configmap.yml
    kubectl apply -f secret.yml
    kubectl apply -f deployment.yml
    kubectl apply -f service.yml
    kubectl apply -f ingress.yml
    
    # Wait for deployment
    print_status "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/social-support-app -n "$NAMESPACE"
    
    # Get service URL
    SERVICE_URL=$(kubectl get service social-support-app-lb -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")
    
    print_success "Kubernetes deployment completed!"
    print_status "Service URL: $SERVICE_URL (may take a few minutes to be available)"
    
    # Show pods status
    kubectl get pods -n "$NAMESPACE"
}

# Function to deploy to AWS ECS
deploy_aws() {
    print_status "Deploying to AWS ECS..."
    
    # Check if AWS CLI is available
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed or not in PATH"
        exit 1
    fi
    
    cd "$DEPLOYMENT_DIR/cloud/aws"
    
    # Run AWS deployment script
    if [[ -f "deploy-aws.sh" ]]; then
        chmod +x deploy-aws.sh
        ./deploy-aws.sh -e "$ENVIRONMENT" -t "$IMAGE_TAG" -r "$REGISTRY"
    else
        print_error "AWS deployment script not found"
        exit 1
    fi
}

# Function to deploy to Azure Container Apps
deploy_azure() {
    print_status "Deploying to Azure Container Apps..."
    
    # Check if Azure CLI is available
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed or not in PATH"
        exit 1
    fi
    
    cd "$DEPLOYMENT_DIR/cloud/azure"
    
    # Run Azure deployment script
    if [[ -f "deploy-azure.sh" ]]; then
        chmod +x deploy-azure.sh
        ./deploy-azure.sh -e "$ENVIRONMENT" -t "$IMAGE_TAG" -r "$REGISTRY"
    else
        print_error "Azure deployment script not found"
        exit 1
    fi
}

# Function to deploy to Google Cloud Run
deploy_gcp() {
    print_status "Deploying to Google Cloud Run..."
    
    # Check if gcloud is available
    if ! command -v gcloud &> /dev/null; then
        print_error "Google Cloud SDK is not installed or not in PATH"
        exit 1
    fi
    
    cd "$DEPLOYMENT_DIR/cloud/gcp"
    
    # Run GCP deployment script
    if [[ -f "deploy-gcp.sh" ]]; then
        chmod +x deploy-gcp.sh
        ./deploy-gcp.sh -e "$ENVIRONMENT" -t "$IMAGE_TAG" -r "$REGISTRY"
    else
        print_error "GCP deployment script not found"
        exit 1
    fi
}

# Function to run pre-deployment checks
pre_deployment_checks() {
    print_status "Running pre-deployment checks..."
    
    # Check if image exists
    if [[ -n "$REGISTRY" ]]; then
        IMAGE_NAME="$REGISTRY/social-support-app:$IMAGE_TAG"
    else
        IMAGE_NAME="social-support-app:$IMAGE_TAG"
    fi
    
    if ! docker image inspect "$IMAGE_NAME" > /dev/null 2>&1; then
        print_warning "Image $IMAGE_NAME not found locally. Attempting to pull..."
        if ! docker pull "$IMAGE_NAME"; then
            print_error "Failed to pull image: $IMAGE_NAME"
            print_status "Please build the image first using: ./build.sh -e $ENVIRONMENT -t $IMAGE_TAG"
            exit 1
        fi
    fi
    
    print_success "Pre-deployment checks passed"
}

# Function to run post-deployment checks
post_deployment_checks() {
    print_status "Running post-deployment checks..."
    
    case $PLATFORM in
        docker-compose)
            # Docker Compose health check already done in deploy function
            ;;
        kubernetes)
            # Check pod status
            kubectl get pods -n "$NAMESPACE" -l app=social-support-app
            ;;
        aws|azure|gcp)
            # Cloud-specific health checks handled by individual scripts
            ;;
    esac
    
    print_success "Post-deployment checks completed"
}

# Main deployment flow
main() {
    # Run pre-deployment checks
    pre_deployment_checks
    
    # Deploy to the specified platform
    case $PLATFORM in
        docker-compose)
            deploy_docker_compose
            ;;
        kubernetes)
            deploy_kubernetes
            ;;
        aws)
            deploy_aws
            ;;
        azure)
            deploy_azure
            ;;
        gcp)
            deploy_gcp
            ;;
    esac
    
    # Run post-deployment checks
    post_deployment_checks
    
    print_success "Deployment completed successfully!"
}

# Trap to handle cleanup on script exit
cleanup() {
    if [[ $? -ne 0 ]]; then
        print_error "Deployment failed. Check the logs above for details."
    fi
}

trap cleanup EXIT

# Run main function
main