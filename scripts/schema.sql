-- Debt Collections Database Schema
-- PostgreSQL 15+ compatible
-- All money fields use DECIMAL(15,2) for precision

-- Drop tables if they exist (for clean installation)
DROP TABLE IF EXISTS call_log CASCADE;
DROP TABLE IF EXISTS promise CASCADE;
DROP TABLE IF EXISTS promise_policy CASCADE;
DROP TABLE IF EXISTS followup CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;

-- Accounts table: Customer account information
CREATE TABLE IF NOT EXISTS accounts (
    "accountId" SERIAL PRIMARY KEY,
    "accountNumber" VARCHAR(50) NOT NULL UNIQUE,
    "customerName" VARCHAR(200) NOT NULL,
    "loanAmount" DECIMAL(15,2) NOT NULL,
    "overdueAmount" DECIMAL(15,2) DEFAULT 0,
    "preferredLanguage" VARCHAR(20) DEFAULT 'en',
    "lastEmiDate" DATE,
    "charges" DECIMAL(15,2) DEFAULT 0,
    "lastPaymentAmount" DECIMAL(15,2) DEFAULT 0,
    "lastPaymentDate" DATE
);

-- Followup table: Call followup records
CREATE TABLE IF NOT EXISTS followup (
    "followupId" SERIAL PRIMARY KEY,
    "accountId" INT REFERENCES accounts("accountId"),
    "remarks" TEXT
);

-- Promise table: Promise to pay records
CREATE TABLE IF NOT EXISTS promise (
    "promiseId" SERIAL PRIMARY KEY,
    "followupId" INT REFERENCES followup("followupId"),
    "accountId" INT REFERENCES accounts("accountId"),
    "promiseAmount" DECIMAL(15,2) NOT NULL,
    "promiseDate" DATE NOT NULL
);

-- Promise policy table: Business rules for PTP validation
CREATE TABLE IF NOT EXISTS promise_policy (
    "promisePolicyId" SERIAL PRIMARY KEY,
    "maxPromiseDays" INT NOT NULL DEFAULT 30,
    "minPromisePercent" DECIMAL(5,2) NOT NULL DEFAULT 25.00
);

-- Call log table: Records every call outcome
CREATE TABLE IF NOT EXISTS call_log (
    "callId" SERIAL PRIMARY KEY,
    "accountId" INT REFERENCES accounts("accountId"),
    "followupId" INT REFERENCES followup("followupId"),
    "callStartTime" TIMESTAMP,
    "callEndTime" TIMESTAMP,
    "callStatus" VARCHAR(30),
    "languageUsed" VARCHAR(20),
    "ptpCaptured" BOOLEAN DEFAULT FALSE,
    "escalated" BOOLEAN DEFAULT FALSE
);

-- Sample data for the collections voice bot
INSERT INTO promise_policy ("maxPromiseDays", "minPromisePercent")
VALUES (30, 25.00)
ON CONFLICT DO NOTHING;

INSERT INTO accounts
    ("accountNumber","customerName","loanAmount","overdueAmount",
     "preferredLanguage","lastEmiDate","charges","lastPaymentAmount","lastPaymentDate")
VALUES
    ('LN001','Rajesh Kumar',500000,12400,'hi','2025-02-01',500,5000,'2025-01-15'),
    ('LN002','Priya Sharma',250000,8750,'en','2025-02-05',250,0,NULL),
    ('LN003','Anand Rajan',750000,31200,'en','2025-01-28',1500,10000,'2025-01-10')
ON CONFLICT ("accountNumber") DO NOTHING;
