#!/bin/bash

# Setup script for creating and initializing the PostgreSQL database

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Portfolio Database Setup${NC}"
echo "======================================"
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo -e "${RED}PostgreSQL is not installed.${NC}"
    echo "Please install PostgreSQL first:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install postgresql postgresql-contrib"
    exit 1
fi

# Get database credentials
echo "Please enter database configuration:"
read -p "Database name (default: portfolio_db): " DB_NAME
DB_NAME=${DB_NAME:-portfolio_db}

read -p "Database user (default: postgres): " DB_USER
DB_USER=${DB_USER:-postgres}

read -sp "Database password: " DB_PASSWORD
echo ""

read -p "Database host (default: localhost): " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "Database port (default: 5432): " DB_PORT
DB_PORT=${DB_PORT:-5432}

echo ""
echo -e "${YELLOW}Creating database...${NC}"

# Create database (if it doesn't exist)
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "CREATE DATABASE $DB_NAME"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Database created or already exists.${NC}"
else
    echo -e "${RED}Failed to create database.${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Initializing schema...${NC}"

# Run schema file
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/schema.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Schema initialized successfully.${NC}"
else
    echo -e "${RED}Failed to initialize schema.${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Creating .env file...${NC}"

# Create .env file
cat > .env << EOF
# Database Configuration
DB_HOST=$DB_HOST
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_PORT=$DB_PORT

# Application Settings
STATEMENTS_DIR=statements
REPORTS_DIR=reports
LOG_LEVEL=INFO
EOF

echo -e "${GREEN}.env file created.${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Database setup completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Install Python dependencies: pip install -r requirements.txt"
echo "2. Process your statements: python process_statements.py process"
echo "3. Generate reports: python process_statements.py report"
echo ""
