# PostgreSQL Setup Guide

## Installation (macOS)

### 1. Install PostgreSQL via Homebrew

```bash
# Install PostgreSQL
brew install postgresql@15

# Add PostgreSQL to PATH (add to ~/.zshrc or ~/.bash_profile)
echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 2. Start PostgreSQL Service

```bash
# Start PostgreSQL service
brew services start postgresql@15

# Verify it's running
brew services list | grep postgresql
```

### 3. Verify Installation

```bash
# Check PostgreSQL version
psql --version
# Should output: psql (PostgreSQL) 15.x
```

## Database Setup

### 1. Create Database User (Optional)

By default, Homebrew PostgreSQL creates a user with your macOS username. You can use this or create a dedicated user:

```bash
# Connect to PostgreSQL as superuser
psql postgres

# Create user (optional - if you want a dedicated logbook user)
CREATE USER logbook_user WITH PASSWORD 'your_secure_password';
ALTER USER logbook_user CREATEDB;

# Exit
\q
```

### 2. Create Logbook Database

```bash
# Option A: Using your macOS user (simpler for development)
createdb logbook

# Option B: Using dedicated logbook user
createdb -U logbook_user logbook
```

### 3. Verify Database Creation

```bash
# List all databases
psql -l

# Connect to logbook database
psql logbook

# List tables (should be empty for now)
\dt

# Exit
\q
```

## Environment Configuration

### 1. Create .env File

Create `.env` file in project root:

```bash
cp .env.example .env
```

### 2. Update DATABASE_URL

Edit `.env` and set the DATABASE_URL:

**Option A: Using your macOS user (recommended for local development)**
```bash
DATABASE_URL=postgresql://localhost:5432/logbook
```

**Option B: Using dedicated user**
```bash
DATABASE_URL=postgresql://logbook_user:your_secure_password@localhost:5432/logbook
```

**Full format:**
```
postgresql://[user[:password]@][host][:port][/database]
```

### 3. Verify Connection String Format

Valid examples:
- `postgresql://localhost/logbook` - Uses default user and port
- `postgresql://user:pass@localhost/logbook` - With credentials
- `postgresql://user:pass@localhost:5432/logbook` - With explicit port

## Testing Connection

### 1. Install Python Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies (if not already installed)
pip install -r requirements.txt
```

### 2. Test Connection with Python

```python
# test_db_connection.py
from sqlalchemy import create_engine, text
from app.core.config import settings

# Create engine
engine = create_engine(settings.DATABASE_URL)

# Test connection
with engine.connect() as conn:
    result = conn.execute(text("SELECT version();"))
    print("PostgreSQL version:")
    print(result.fetchone()[0])
    print("\n✅ Database connection successful!")
```

Run the test:
```bash
python test_db_connection.py
```

### 3. Test with psql

```bash
# Connect using the DATABASE_URL from .env
psql $DATABASE_URL

# Or connect directly
psql -d logbook

# Run a test query
SELECT version();

# Exit
\q
```

## Troubleshooting

### PostgreSQL Service Not Starting

```bash
# Check PostgreSQL logs
tail -f /opt/homebrew/var/log/postgresql@15.log

# Stop and restart service
brew services stop postgresql@15
brew services start postgresql@15
```

### Connection Refused

1. **Check if PostgreSQL is running:**
   ```bash
   brew services list | grep postgresql
   ```

2. **Check port (default is 5432):**
   ```bash
   lsof -i :5432
   ```

3. **Verify DATABASE_URL format** in `.env`

### Permission Denied

If you get "permission denied" errors:

```bash
# Reset PostgreSQL data directory permissions
chmod 700 /opt/homebrew/var/postgresql@15
```

### Database Does Not Exist

```bash
# List all databases
psql -l

# Create database if it doesn't exist
createdb logbook
```

## PostgreSQL Useful Commands

### Command Line

```bash
# List databases
psql -l

# Connect to database
psql logbook

# Create database
createdb database_name

# Drop database
dropdb database_name

# Dump database (backup)
pg_dump logbook > backup.sql

# Restore database
psql logbook < backup.sql
```

### Inside psql Console

```sql
-- List databases
\l

-- Connect to database
\c logbook

-- List tables
\dt

-- Describe table
\d table_name

-- List users/roles
\du

-- Show current database
SELECT current_database();

-- Show current user
SELECT current_user;

-- Quit
\q
```

## Next Steps

After PostgreSQL is set up:

1. ✅ PostgreSQL installed and running
2. ✅ Database created
3. ✅ .env configured with DATABASE_URL
4. ✅ Connection tested
5. ⬜ Set up Alembic migrations
6. ⬜ Create database models
7. ⬜ Run migrations

## Uninstallation (if needed)

```bash
# Stop PostgreSQL service
brew services stop postgresql@15

# Uninstall PostgreSQL
brew uninstall postgresql@15

# Remove data directory (WARNING: This deletes all databases!)
rm -rf /opt/homebrew/var/postgresql@15
```
