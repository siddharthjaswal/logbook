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

## Connecting with Database GUI Clients

### DBeaver (Recommended)

DBeaver is a free, cross-platform database tool that works great with PostgreSQL.

#### 1. Install DBeaver

**Option A: Using Homebrew**
```bash
brew install --cask dbeaver-community
```

**Option B: Download from Website**
- Visit [https://dbeaver.io/download/](https://dbeaver.io/download/)
- Download DBeaver Community Edition
- Install the application

#### 2. Create New Connection

1. Open DBeaver
2. Click **Database** → **New Database Connection** (or press `⌘N` on Mac)
3. Select **PostgreSQL** and click **Next**

#### 3. Configure Connection Settings

**Main Tab:**
- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `logbook`
- **Authentication**: Database Native
- **Username**: Your macOS username (e.g., `sid`) or `logbook_user` if you created a dedicated user
- **Password**: Leave blank if using macOS user, or enter password if using dedicated user
- **Save password**: ✓ (check this for convenience)

**Example Configuration:**
```
Host:     localhost
Port:     5432
Database: logbook
Username: sid
Password: (leave empty for local macOS user)
```

#### 4. Test Connection

1. Click **Test Connection** button
2. If first time, DBeaver will offer to download PostgreSQL JDBC driver - click **Download**
3. You should see "Connected" with PostgreSQL version information
4. Click **Finish**

#### 5. View Your Database

Once connected, you can:
- **Browse Tables**: Expand `logbook` → `Schemas` → `public` → `Tables`
- **View Data**: Right-click a table → **View Data**
- **Run Queries**: Click **SQL Editor** button or press `⌘]` (Mac) / `Ctrl+]` (Windows)
- **View Schema**: Right-click a table → **View Diagram**

#### Sample Queries to Try

```sql
-- List all tables
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- Show all enum types
SELECT typname FROM pg_type WHERE typtype = 'e' ORDER BY typname;

-- Count records in each table
SELECT 'users' as table_name, COUNT(*) FROM users
UNION ALL
SELECT 'trips', COUNT(*) FROM trips
UNION ALL
SELECT 'trip_days', COUNT(*) FROM trip_days
UNION ALL
SELECT 'activities', COUNT(*) FROM activities
UNION ALL
SELECT 'bookings', COUNT(*) FROM bookings;

-- View table structure
\d users
\d trips
\d trip_days
\d activities
\d bookings
```

### Other Popular Database Clients

#### TablePlus

A modern, native macOS database client with a beautiful UI.

**Install:**
```bash
brew install --cask tableplus
```

**Connection Settings:**
- **Name**: Logbook
- **Type**: PostgreSQL
- **Host**: localhost
- **Port**: 5432
- **User**: your_username
- **Password**: (if applicable)
- **Database**: logbook

#### pgAdmin 4

Official PostgreSQL administration tool with advanced features.

**Install:**
```bash
brew install --cask pgadmin4
```

**Connection Settings:**
1. Right-click **Servers** → **Create** → **Server**
2. **General Tab**:
   - Name: `Logbook Local`
3. **Connection Tab**:
   - Host: `localhost`
   - Port: `5432`
   - Maintenance database: `logbook`
   - Username: your_username
   - Password: (if applicable)
   - Save password: ✓

#### DataGrip (JetBrains)

Professional database IDE with powerful features. Paid software, but free for students, teachers, and open source developers.

##### 1. Download and Install

**Option A: Using Homebrew (Recommended)**
```bash
brew install --cask datagrip
```

**Option B: Download from JetBrains**
- Visit [https://www.jetbrains.com/datagrip/download/](https://www.jetbrains.com/datagrip/download/)
- Download for macOS
- Open the DMG file and drag DataGrip to Applications folder

**Free License Options:**
- **Students/Teachers**: [Free Educational License](https://www.jetbrains.com/community/education/)
- **Open Source**: [Free Open Source License](https://www.jetbrains.com/community/opensource/)
- **Free Trial**: 30-day trial for evaluation

##### 2. First Launch Setup

1. Launch DataGrip from Applications
2. Accept the Privacy Policy
3. Choose your UI theme (Light/Dark/High Contrast)
4. If first JetBrains product: Create/Sign in to JetBrains account
5. Enter license key or start trial

##### 3. Create New Data Source

**Method 1: From Welcome Screen**
1. On welcome screen, click **New** (or press `⌘N` on Mac)
2. Select **Data Source** → **PostgreSQL**

**Method 2: From Database Explorer**
1. Click the **+** icon in Database Explorer
2. Select **Data Source** → **PostgreSQL**

##### 4. Configure PostgreSQL Connection

**Data Sources and Drivers Dialog:**

**General Tab:**
- **Name**: `Logbook Local` (or any name you prefer)
- **Comment**: Optional description like "Local development database"

**Connection Settings:**
- **Host**: `localhost`
- **Port**: `5432`
- **Authentication**: User & Password
- **User**: `sid` (your macOS username)
- **Password**: Leave blank (or enter if you set a password)
- **Save**: Password (check this option)
- **Database**: `logbook`
- **URL**: Should auto-fill as `jdbc:postgresql://localhost:5432/logbook`

**Example Configuration:**
```
Name:     Logbook Local
Host:     localhost
Port:     5432
User:     sid
Password: (empty)
Database: logbook
URL:      jdbc:postgresql://localhost:5432/logbook
```

##### 5. Download PostgreSQL Driver

1. If this is your first time, DataGrip will show "Download missing driver files"
2. Click **Download** or the download link at the bottom
3. Wait for the PostgreSQL JDBC driver to download
4. The "Download" link should change to show driver version

##### 6. Test Connection

1. Click **Test Connection** button at the bottom of the dialog
2. Should show: "Succeeded" with green checkmark
3. You'll see connection details like:
   ```
   PostgreSQL 15.x
   Driver: PostgreSQL JDBC Driver
   Ping: <time>ms
   ```
4. If successful, click **OK** to save

##### 7. Connect to Database

1. In Database Explorer panel (left side), you'll see your data source
2. Click the connection or press `⌘Enter` to connect
3. Once connected, expand the tree:
   - `logbook@localhost`
   - `logbook` (database)
   - `public` (schema)
   - `tables` - See all your tables (users, trips, trip_days, activities, bookings)

##### 8. Basic Usage

**Open Query Console:**
- Right-click database → **New** → **Query Console**
- Or press `⌘Shift+L`
- Or click **+** tab at top and select **Query Console**

**Run Your First Query:**
```sql
-- See all tables
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- Count records
SELECT
  'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'trips', COUNT(*) FROM trips
UNION ALL
SELECT 'trip_days', COUNT(*) FROM trip_days
UNION ALL
SELECT 'activities', COUNT(*) FROM activities
UNION ALL
SELECT 'bookings', COUNT(*) FROM bookings;
```

**Execute Query:**
- Press `⌘Enter` (Mac) or `Ctrl+Enter` (Windows) to run query under cursor
- Or press `⌘Shift+Enter` to run entire script

**View Table Data:**
- Double-click any table to open data editor
- Or right-click table → **View Data**

##### 9. Useful DataGrip Features

**1. Database Diagrams**
- Right-click on schema/table → **Diagrams** → **Show Visualization**
- Or select multiple tables, right-click → **Diagrams** → **Show Diagram**
- Shows relationships, foreign keys, and table structures

**2. Table Editor**
- Double-click any table to view/edit data
- Edit cells directly in the grid
- Press `⌘Enter` to commit changes
- Press `⌘Z` to undo

**3. Smart Code Completion**
- Type in query console - DataGrip suggests table names, columns
- Press `Ctrl+Space` for completion suggestions
- Automatically suggests JOIN conditions

**4. SQL Formatting**
- Write messy SQL
- Press `⌘Option+L` (Mac) or `Ctrl+Alt+L` (Windows)
- SQL is automatically formatted with proper indentation

**5. Generate SQL**
- Right-click table → **SQL Generator**
- Generate SELECT, INSERT, UPDATE, DELETE statements
- Customize column selection

**6. Export Data**
- Run query
- Click **Export Data** icon (down arrow in results)
- Choose format: CSV, JSON, SQL Inserts, Excel, etc.

**7. Execute Explain Plan**
- Write SELECT query
- Press `⌘Shift+E` or click **Explain Plan** button
- View query execution plan with costs

**8. Multiple Cursors**
- Hold `Option` (Mac) or `Alt` (Windows) and click to add cursors
- Edit multiple lines simultaneously

##### 10. Keyboard Shortcuts (macOS)

| Action | Shortcut |
|--------|----------|
| New Query Console | `⌘Shift+L` |
| Execute Statement | `⌘Enter` |
| Execute Script | `⌘Shift+Enter` |
| Format SQL | `⌘Option+L` |
| Code Completion | `Ctrl+Space` |
| Show Execution Plan | `⌘Shift+E` |
| Navigate to Table | `⌘O` |
| Find in Files | `⌘Shift+F` |
| Show Database Changes | `⌘Shift+D` |
| Commit Changes | `⌘K` |
| Rollback Changes | `⌘Option+Z` |

##### 11. Configure Settings (Optional)

**Access Settings:**
- `⌘,` (Mac) or `Ctrl+Alt+S` (Windows)

**Useful Settings:**
- **Appearance** → Theme (Darcula, Light, High Contrast)
- **Editor** → **General** → **Appearance** → Show line numbers
- **Editor** → **Code Style** → **SQL** → Customize formatting
- **Database** → **Query Execution** → Auto-commit (turn off for safety)

##### 12. Troubleshooting DataGrip

**Can't Find Driver:**
- Go to **File** → **Data Sources**
- Click **Drivers** tab at top
- Find **PostgreSQL** → Click **Download/Update** button

**Connection Timeout:**
- Increase timeout: In connection settings → **Advanced** tab
- Set `loginTimeout` to `30` or `60` seconds

**Can't See Tables:**
- Check you're connected (green indicator next to data source)
- Refresh: Right-click data source → **Refresh**
- Or press `⌘Option+Y`

**Permission Denied:**
- Verify PostgreSQL is running:
  ```bash
  brew services list | grep postgresql
  ```
- Test with psql first:
  ```bash
  psql -d logbook
  ```

**SSL Connection Error:**
- In connection settings → **Advanced** tab
- Add property: `ssl` = `false`
- Or set `sslmode` = `disable`

##### 13. DataGrip vs Other Clients

**Pros:**
- ✅ Best code completion and intelligence
- ✅ Powerful refactoring tools
- ✅ Database diff and migration tools
- ✅ Version control integration (Git)
- ✅ Multiple database support in one window
- ✅ Advanced debugging and profiling
- ✅ JetBrains ecosystem integration

**Cons:**
- ❌ Paid software (though free for students/OSS)
- ❌ Heavier resource usage
- ❌ Steeper learning curve

**Best For:**
- Professional developers
- Complex database work
- Multi-database projects
- Team collaboration
- Those already using JetBrains IDEs

### Connection Troubleshooting

#### DBeaver Can't Connect

1. **Verify PostgreSQL is running:**
   ```bash
   brew services list | grep postgresql
   ```

2. **Check if port 5432 is accessible:**
   ```bash
   lsof -i :5432
   ```

3. **Test connection with psql first:**
   ```bash
   psql -d logbook
   ```

4. **Check pg_hba.conf** (if authentication issues):
   ```bash
   cat /opt/homebrew/var/postgresql@15/pg_hba.conf
   ```

   Should have a line like:
   ```
   local   all   all   trust
   ```

#### Driver Issues

If DBeaver or other clients can't download drivers:
- Check your internet connection
- Manually download PostgreSQL JDBC driver from [https://jdbc.postgresql.org/download/](https://jdbc.postgresql.org/download/)
- In DBeaver: **Database** → **Driver Manager** → **PostgreSQL** → **Libraries** → **Add File**

#### Password Authentication Failed

If using macOS user without password:
- Leave password field empty in the client
- Or in DBeaver, uncheck "Save password" and leave it blank

If using dedicated user:
- Verify password is correct
- Test login via command line:
  ```bash
  psql -U logbook_user -d logbook
  ```

### Useful DBeaver Features

#### 1. ER Diagrams

View entity relationships:
- Right-click database → **View Diagram**
- Or select multiple tables → Right-click → **View Diagram**

#### 2. Data Export

Export query results:
- Run query
- Right-click on results → **Export Data**
- Choose format (CSV, JSON, SQL, etc.)

#### 3. SQL Formatting

Auto-format SQL:
- Write query in SQL Editor
- Press `⌘⇧F` (Mac) or `Ctrl+Shift+F` (Windows)

#### 4. Dark Mode

Enable dark theme:
- **Window** → **Preferences** → **General** → **Appearance** → **Dark Theme**

#### 5. Execute Explain Plan

Analyze query performance:
- Write SELECT query
- Press `⌘⇧E` (Mac) or `Ctrl+Shift+E` (Windows)
- View execution plan with costs

### Connection String Reference

For quick reference when setting up any client:

**Format:**
```
postgresql://[username[:password]@][host][:port]/[database]
```

**Your Logbook Database:**
```
Host:     localhost
Port:     5432
Database: logbook
Username: sid (or your macOS username)
Password: (empty for local development)

Connection String: postgresql://localhost:5432/logbook
JDBC URL: jdbc:postgresql://localhost:5432/logbook
```

## Uninstallation (if needed)

```bash
# Stop PostgreSQL service
brew services stop postgresql@15

# Uninstall PostgreSQL
brew uninstall postgresql@15

# Remove data directory (WARNING: This deletes all databases!)
rm -rf /opt/homebrew/var/postgresql@15
```
