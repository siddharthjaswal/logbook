# Development Environment Setup

## Prerequisites

- Python 3.8+ (you have Python 3.13.5 ✅)
- PostgreSQL 15+
- Homebrew (macOS)

## Step-by-Step Setup

### 1. Create Virtual Environment

```bash
# Navigate to project directory
cd /Users/sid/Projects/Backend/logbook

# Create virtual environment
python3 -m venv venv

# Verify venv folder was created
ls -la venv
```

### 2. Activate Virtual Environment

```bash
# Activate virtual environment (macOS/Linux)
source venv/bin/activate

# Your prompt should change to show (venv)
# Example: (venv) sid@danube logbook %
```

**Important:** Always activate the virtual environment before working on the project!

### 3. Install Python Dependencies

```bash
# Make sure venv is activated (you should see (venv) in prompt)
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
# Check installed packages
pip list

# Should see: fastapi, sqlalchemy, psycopg2-binary, etc.
```

### 5. Install PostgreSQL

```bash
# Install PostgreSQL 15
brew install postgresql@15

# Add to PATH
echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Start PostgreSQL service
brew services start postgresql@15

# Verify it's running
brew services list | grep postgresql
```

### 6. Create Database

```bash
# Create logbook database
createdb logbook

# Verify database was created
psql -l | grep logbook
```

### 7. Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env file (use nano, vim, or VS Code)
nano .env
```

Update these values in `.env`:
```bash
# Database
DATABASE_URL=postgresql://localhost:5432/logbook

# Google OAuth (get from Google Cloud Console)
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# JWT (generate with: openssl rand -hex 32)
SECRET_KEY=your_generated_secret_key_here
```

Generate SECRET_KEY:
```bash
openssl rand -hex 32
```

### 8. Test Database Connection

```bash
# Make sure venv is activated
python scripts/test_db_connection.py
```

Expected output:
```
✅ Connection successful!
Database: logbook
User: sid
PostgreSQL Version: ...
✅ Database is ready for use!
```

## Daily Development Workflow

### Starting Work

```bash
# 1. Navigate to project
cd /Users/sid/Projects/Backend/logbook

# 2. Activate virtual environment
source venv/bin/activate

# 3. Pull latest changes (if working in a team)
git pull origin main

# 4. Start development server
uvicorn app.main:app --reload
```

### Ending Work

```bash
# 1. Deactivate virtual environment
deactivate

# 2. Stop PostgreSQL (optional, or leave it running)
brew services stop postgresql@15
```

## Common Commands

### Virtual Environment

```bash
# Activate
source venv/bin/activate

# Deactivate
deactivate

# Delete and recreate (if corrupted)
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Python Dependencies

```bash
# Install new package
pip install package-name

# Update requirements.txt after adding packages
pip freeze > requirements.txt

# Install from requirements.txt
pip install -r requirements.txt

# Upgrade all packages (use with caution)
pip list --outdated
pip install --upgrade package-name
```

### FastAPI Server

```bash
# Start development server with auto-reload
uvicorn app.main:app --reload

# Start on different port
uvicorn app.main:app --reload --port 8080

# Start with specific host
uvicorn app.main:app --reload --host 0.0.0.0

# View logs
# Logs appear in terminal where server is running
```

### Database

```bash
# Connect to database
psql logbook

# List databases
psql -l

# Run SQL file
psql logbook < file.sql

# Dump database (backup)
pg_dump logbook > backup.sql

# Test connection
python scripts/test_db_connection.py
```

### Alembic Migrations (After setup)

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history
```

### Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_trips.py

# Run with coverage
pytest --cov=app tests/

# Run specific test
pytest tests/test_trips.py::test_create_trip
```

## Troubleshooting

### "pip: command not found"

✅ **Solution:** Make sure virtual environment is activated
```bash
source venv/bin/activate
```

### "ModuleNotFoundError"

✅ **Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### "Database connection failed"

✅ **Solution:** Check PostgreSQL is running
```bash
brew services list | grep postgresql
# If not running:
brew services start postgresql@15
```

### "createdb: command not found"

✅ **Solution:** Add PostgreSQL to PATH
```bash
echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### "Port 8000 already in use"

✅ **Solution:** Kill process on port 8000 or use different port
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --reload --port 8001
```

## VS Code Setup (Optional)

### Recommended Extensions

- Python
- Pylance
- Python Debugger
- SQLTools
- Thunder Client (API testing)

### Python Interpreter

1. Open Command Palette (Cmd+Shift+P)
2. Type "Python: Select Interpreter"
3. Choose: `./venv/bin/python`

### Launch Configuration

Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "jinja": true
    }
  ]
}
```

## Next Steps

After completing this setup:

1. ✅ Set up Alembic migrations
2. ✅ Create database models (User, Trip, TripDay)
3. ✅ Run migrations
4. ✅ Implement authentication
5. ✅ Test APIs with Bruno
