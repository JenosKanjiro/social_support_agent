# 🇦🇪 UAE Social Support Application Processing System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/dependency%20manager-poetry-blue.svg)](https://python-poetry.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Social Support Application Processing System

A comprehensive AI-powered system for processing social support applications in the UAE. The system extracts information from various documents, validates the data, makes eligibility decisions using machine learning, and provides personalized recommendations.

## Features

- **Document Processing**: Automated extraction from Emirates IDs, bank statements, credit reports, resumes, and asset/liability statements
- **Data Validation**: Cross-validation of information across multiple documents
- **ML-Driven Decisions**: XGBoost model for eligibility determination
- **Personalized Recommendations**: Tailored economic enablement suggestions
- **Interactive Chatbot**: Query interface for applicants
- **Vector-Based Search**: Context-aware responses using document embeddings

## System Architecture

The system uses a multi-agent workflow with the following components:

- **Supervisor Agent**: Coordinates workflow and routes tasks
- **Extractor Agent**: Processes and extracts document information
- **Validator Agent**: Validates extracted data for consistency
- **Decision Maker Agent**: Makes eligibility decisions using ML models
- **Recommender Agent**: Generates personalized recommendations
- **Chatbot Agent**: Handles user queries and interactions

## Prerequisites

Before setting up the system, ensure you have the following installed:

- **Python 3.10+**
- **PostgreSQL 12+**
- **pgAdmin4** (for database management)
- **Git**
- **Poetry** (Python dependency management)
- **Ollama** (for running local LLMs)

## Installation Guide

### 1. Clone the Repository

```bash
git clone <repository-url>
cd social-support-processing-system
```

### 2. Install Poetry

Poetry is used for dependency management and virtual environment handling.

#### On Windows:

```powershell
# Using PowerShell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

#### On macOS/Linux:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

#### Alternative installation via pip:

```bash
pip install poetry
```

**Note**: After installation, you may need to add Poetry to your PATH. Follow the instructions displayed after installation.

### 3. Install Dependencies with Poetry

```bash
# Navigate to the project directory
cd social-support-processing-system

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell
```

### 4. Database Setup

#### 4.1. Install PostgreSQL and pgAdmin4

**Windows:**

- Download and install PostgreSQL from [official website](https://www.postgresql.org/download/windows/)
- pgAdmin4 is included with PostgreSQL installation

**macOS:**

```bash
# Using Homebrew
brew install postgresql
brew install --cask pgadmin4
```

**Linux (Ubuntu/Debian):**

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo apt install pgadmin4
```

#### 4.2. Start PostgreSQL Service

**Windows:**

- PostgreSQL service should start automatically after installation
- Check Windows Services if needed

**macOS:**

```bash
brew services start postgresql
```

**Linux:**

```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### 4.3. Create Database using pgAdmin4

1. **Open pgAdmin4**

   - Launch pgAdmin4 from your applications
   - Set up a master password when first opening

2. **Connect to PostgreSQL Server**

   - Right-click on "Servers" in the left panel
   - Select "Create" > "Server"
   - Fill in the connection details:
     - **Name**: Local PostgreSQL
     - **Host**: localhost
     - **Port**: 5432
     - **Username**: postgres
     - **Password**: [your PostgreSQL password]

3. **Create the Database**

   - Right-click on the server connection
   - Select "Create" > "Database"
   - **Database name**: `social_support`
   - Click "Save"

4. **Create Database Schema**

   The application will automatically create the required tables when first run, but you can also create them manually:

   ```sql
   -- Connect to social_support database and run these queries

   CREATE TABLE IF NOT EXISTS applicant (
       id SERIAL PRIMARY KEY,
       applicant_id TEXT,
       created_at TEXT,
       updated_at TEXT,
       first_name TEXT,
       last_name TEXT,
       date_of_birth TEXT,
       gender TEXT,
       nationality TEXT,
       emirates_id TEXT,
       address TEXT
   );

   CREATE TABLE IF NOT EXISTS application (
       id SERIAL PRIMARY KEY,
       applicant_id TEXT,
       created_at TEXT,
       support_type TEXT,
       status TEXT,
       processing_completed_at TEXT,
       decision TEXT,
       decision_reason TEXT,
       decision_explanation TEXT,
       decision_date TEXT,
       enablement_recommendations TEXT,
       documents TEXT,
       validation_results TEXT
   );
   ```

### 5. Setup Ollama and Models

#### 5.1. Install Ollama

**Windows:**

- Download from [Ollama website](https://ollama.ai/download/windows)
- Run the installer

**macOS:**

```bash
# Using Homebrew
brew install ollama

# Or download from website
curl -fsSL https://ollama.ai/install.sh | sh
```

**Linux:**

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

#### 5.2. Start Ollama Service

```bash
# Start Ollama service
ollama serve
```

**Note**: Keep this terminal window open or run as a service

#### 5.3. Pull Required Models

Open a new terminal and run:

```bash
# Pull the required models
ollama pull llama3.2:1b
ollama pull qwen3:0.6b
ollama pull nomic-embed-text:latest
```

#### 5.4. Verify Models Installation

```bash
# List installed models
ollama list
```

You should see the three models listed above.

### 6. Environment Configuration

#### 6.1. Create Environment File

Create a `.env` file in the project root:

```bash
# Database Configuration
DB_PASSWORD=your_postgresql_password

# Optional: Customize other settings
# OLLAMA_BASE_URL=http://localhost:11434
# VECTOR_STORE_DIR=./storage/llama_index_storage
```

#### 6.2. Update Configuration

Edit `config.py` if needed to match your setup:

```python
# Update database password
DB_CONFIG = {
    "database": "social_support",
    "user": "postgres",
    "host": "localhost",
    "password": os.environ.get("DB_PASSWORD", "your_password_here"),
}
```

### 7. Prepare Sample Data

Create a `data` directory and add sample documents:

Add the following sample files to the `data` directory:

- Emirates ID file (image/pdf)
- Bank statement file (pdf)
- Credit report file (image/pdf)
- Resume file (pdf)
- Asset/liability spreadsheet

## Running the Application

### 1. Start Required Services

Make sure the following services are running:

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start PostgreSQL (if not running as service)
# This varies by OS - see database setup section
```

### 2. Run the Main Application

```bash
# Activate poetry environment
poetry shell

# Run the main application
python app.py
```

## Project Structure

```
social_support/
├── main.py                          # Main application entry point
├── config.py                        # Configuration settings
├── sample_usage.py                  # Usage examples
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Poetry configuration
├── README.md                        # This file
├── .env                            # Environment variables
├── models/                         # ML models and data structures
│   ├── __init__.py
│   ├── data_models.py              # Pydantic models
│   ├── agent_state.py              # Workflow state definition
│   ├── model.xgb                   # Trained XGBoost model
│   └── label_encoder.pkl           # Label encoder
├── data/                           # Sample data files
│   ├── eida.png
│   ├── BankStatement.pdf
│   ├── credit-report.png
│   ├── Resume.pdf
│   └── Assets-Liabilities.xlsx
├── database/
│   ├── __init__.py
│   └── db_operations.py            # Database operations
├── document_processing/
│   ├── __init__.py
│   ├── extraction.py               # Document extraction logic
│   ├── prompts.py                  # LLM prompts
│   └── ocr.py                      # OCR functionality
├── vector_store/
│   ├── __init__.py
│   └── operations.py               # Vector store operations
├── inference/
│   ├── __init__.py
│   └── decision_model.py           # ML model inference
├── agents/
│   ├── __init__.py
│   ├── supervisor.py               # Supervisor agent
│   ├── extractor.py                # Document extractor agent
│   ├── validator.py                # Validation agent
│   ├── decision_maker.py           # Decision making agent
│   ├── recommender.py              # Recommendation agent
│   └── chatbot.py                  # Chatbot agent
├── workflow/
│   ├── __init__.py
│   └── graph.py                    # Workflow graph construction
└── storage/                        # Generated files and cache
    ├── llama_index_storage/        # Vector store data
    └── cached_extraction_data_file_path.pkl
```

## Troubleshooting

### Common Issues

#### 1. Poetry Installation Issues

```bash
# If poetry command not found
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

#### 2. PostgreSQL Connection Issues

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS

# Reset PostgreSQL password if needed
sudo -u postgres psql
\password postgres
```

#### 3. Ollama Model Issues

```bash
# Check Ollama service
curl http://localhost:11434/api/tags

# Restart Ollama service
pkill ollama
ollama serve
```

#### 4. Python Package Issues

```bash
# Reinstall dependencies
poetry install --no-cache

# Or install specific packages
poetry add package_name
```

#### 5. Database Permission Issues

```sql
-- Grant permissions to postgres user
GRANT ALL PRIVILEGES ON DATABASE social_support TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
```

### Performance Optimization

1. **Use SSD storage** for better I/O performance
2. **Allocate sufficient RAM** (minimum 8GB recommended)
3. **Use GPU acceleration** for Ollama models if available
4. **Enable caching** for document extraction to avoid reprocessing

### Logging and Debugging

Logs are written to /logs folder. To increase logging verbosity:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License

This project is proprietary.

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review the logs in `social_support.log`
3. Create an issue in the repository
4. Contact the development team

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Write comprehensive docstrings
- Add tests for new functionality
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Open-source community for the amazing tools and libraries
- Contributors and maintainers of the project

## 📞 Support

For questions, issues, or support:

1. **Check the troubleshooting section** above
2. **Search existing issues** in the GitHub repository
3. **Create a new issue** with detailed information
4. **Contact the development team** for urgent matters

---

**Happy Coding! 🚀**

_This project is part of the UAE Government's initiative to modernize social support services through AI automation._
