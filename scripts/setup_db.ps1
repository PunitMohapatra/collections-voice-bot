# PostgreSQL DB Setup Script for Collections Voice Bot
# ====================================================

$ErrorActionPreference = "Stop"

$DB_NAME = "collections_dev"
$DB_USER = "postgres"
$DB_PASS = "all@1234"
$DB_HOST = "localhost"
$DB_PORT = "5432"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Setting up PostgreSQL Database: $DB_NAME" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Check if pg_isready or psql is available
$psqlPath = Get-Command psql -ErrorAction SilentlyContinue

if (-not $psqlPath) {
    # Check common installation directories on Windows
    $commonPaths = @(
        "C:\Program Files\PostgreSQL\*\bin\psql.exe",
        "C:\Program Files (x86)\PostgreSQL\*\bin\psql.exe"
    )
    foreach ($pattern in $commonPaths) {
        $found = Resolve-Path $pattern -ErrorAction SilentlyContinue
        if ($found) {
            $psqlPath = $found[0].Path
            $binDir = Split-Path $psqlPath
            # Add to PATH temporarily
            $env:Path += ";$binDir"
            Write-Host "Found psql at: $psqlPath" -ForegroundColor Green
            break
        }
    }
}

if (-not $psqlPath) {
    Write-Host "WARNING: psql executable not found in PATH." -ForegroundColor Yellow
    Write-Host "Please ensure PostgreSQL is installed and psql is in your environment PATH." -ForegroundColor Yellow
    Write-Host "Alternatively, run the queries in 'scripts/schema.sql' manually using pgAdmin or DBeaver." -ForegroundColor Yellow
    Exit 1
}

# Set PGPASSWORD environment variable so psql doesn't prompt for password
$env:PGPASSWORD = $DB_PASS

Write-Host "1. Dropping existing database (if any) and creating new database '$DB_NAME'..." -ForegroundColor Cyan

try {
    # Drop existing connections if any, then drop and create database
    # We run these against the default 'postgres' database
    & psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME WITH (FORCE);"
    & psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;"
    Write-Host "Database '$DB_NAME' created successfully." -ForegroundColor Green
} catch {
    Write-Host "Error creating database: $_" -ForegroundColor Red
    Write-Host "Ensure PostgreSQL is running and credentials in application.properties match." -ForegroundColor Yellow
    Exit 1
}

Write-Host "`n2. Running schema.sql script to create tables and load sample data..." -ForegroundColor Cyan

$schemaPath = Join-Path $PSScriptRoot "schema.sql"
if (-not (Test-Path $schemaPath)) {
    # Try current directory too
    $schemaPath = "scripts/schema.sql"
}

try {
    & psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $schemaPath
    Write-Host "`nDatabase schema and sample data loaded successfully!" -ForegroundColor Green
} catch {
    Write-Host "Error loading database schema: $_" -ForegroundColor Red
    Exit 1
}

# Clear password from environment variables
$env:PGPASSWORD = $null

Write-Host "`nDatabase setup complete!" -ForegroundColor Green
