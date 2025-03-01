# SEC Financial Statement Data Sets Analysis

## Overview
This repository contains scripts for processing and analyzing the SEC's Financial Statement Data Sets, specifically focusing on the Q4 2024 dataset. The dataset provides detailed financial statement information from SEC filings in a structured format.

## Dataset Structure
The SEC Financial Statement Dataset is distributed as a ZIP file containing four main tab-delimited text files:

### 1. Submissions (SUB.txt → SUBMISSIONS table)
Contains basic information about each SEC submission:
- Submission details (adsh, cik, name, sic, countryba, stprba, cityba, zipba)
- Filing period information (form, period, fy, fp, filed)
- Company details (accepted, prevrpt, detail, instance, nciks, aciks)

### 2. Numbers (NUM.txt → NUMBERS table)
Contains the financial statement numeric values:
- Submission reference (adsh)
- Financial statement line items (tag, version)
- Values and context (ddate, qtrs, uom, value)
- Calculation details (coreg, footnote, footlen)

### 3. Presentations (PRE.txt → PRESENTATIONS table)
Contains information about how the financial statements are presented:
- Submission reference (adsh)
- Statement organization (report, line, stmt, inpth)
- Presentation details (rfile, tag, version, plabel, negating)

### 4. Tags (TAG.txt → TAGS table)
Contains definitions for the XBRL tags used in the financial statements:
- Tag details (tag, version, custom)
- Descriptions (abstract, datatype, iord, crdr, tlabel, doc)

## Database Schema

### SUBMISSIONS Table
Primary table storing SEC filing submission information.
```sql
CREATE TABLE SUBMISSIONS (
    ADSH VARCHAR(20),
    CIK INT,
    NAME VARCHAR(150),
    SIC INT,
    COUNTRYBA VARCHAR(2),
    STPRBA VARCHAR(2),
    CITYBA VARCHAR(30),
    ZIPBA VARCHAR(10),
    FORM VARCHAR(10),
    PERIOD DATE,
    FY INT,
    FP VARCHAR(2),
    FILED DATE,
    ACCEPTED TIMESTAMP,
    PREVRPT BOOLEAN,
    DETAIL BOOLEAN,
    INSTANCE VARCHAR(32),
    NCIKS INT,
    ACIKS VARCHAR(120),
    PRIMARY KEY (ADSH)
);
```

### NUMBERS Table
Stores the actual financial values from the statements.
```sql
CREATE TABLE NUMBERS (
    ADSH VARCHAR(20),
    TAG VARCHAR(256),
    VERSION VARCHAR(20),
    COREG VARCHAR(256),
    DDATE DATE,
    QTRS INT,
    UOM VARCHAR(20),
    VALUE FLOAT,
    FOOTNOTE VARCHAR(512),
    FOOTLEN INT,
    FOREIGN KEY (ADSH) REFERENCES SUBMISSIONS(ADSH)
);
```

### PRESENTATIONS Table
Contains information about how data is presented in financial statements.
```sql
CREATE TABLE PRESENTATIONS (
    ADSH VARCHAR(20),
    REPORT INT,
    LINE INT,
    STMT VARCHAR(2),
    INPTH BOOLEAN,
    RFILE VARCHAR(1),
    TAG VARCHAR(256),
    VERSION VARCHAR(20),
    PLABEL VARCHAR(512),
    NEGATING BOOLEAN,
    FOREIGN KEY (ADSH) REFERENCES SUBMISSIONS(ADSH)
);
```

### TAGS Table
Stores XBRL tag definitions and documentation.
```sql
CREATE TABLE TAGS (
    TAG VARCHAR(256),
    VERSION VARCHAR(20),
    CUSTOM BOOLEAN,
    ABSTRACT BOOLEAN,
    DATATYPE VARCHAR(20),
    IORD VARCHAR(1),
    CRDR VARCHAR(1),
    TLABEL VARCHAR(512),
    DOC TEXT,
    PRIMARY KEY (TAG, VERSION)
);
```

## Data Processing Workflow

1. **Data Download** (`download_sec.py`)
   - Downloads the SEC dataset using specific headers for authentication
   - Extracts the ZIP file to /tmp directory
   - Handles connection errors and validates downloaded content

2. **Data Processing** (`process_data.py`)
   - Converts tab-delimited files to CSV format
   - Performs data type inference and validation
   - Handles large files efficiently through chunked processing
   - Generates processed CSV files in /tmp/2024q4_processed/

3. **Database Setup** (`create_tables.py`)
   - Establishes connection to Snowflake
   - Creates tables with appropriate schemas
   - Adds comprehensive column comments
   - Implements proper constraints and relationships

4. **Data Loading** (`load_data.py`)
   - Creates internal Snowflake stage
   - Bulk loads data from CSV files
   - Handles data type conversions
   - Performs basic data validation

## Data Volume Summary
- SUBMISSIONS: ~6,500 records
- NUMBERS: ~3.7 million records
- PRESENTATIONS: ~737,000 records
- TAGS: ~84,000 records

## Usage Notes
- The dataset provides comprehensive financial statement information from SEC filings
- Data is structured to maintain relationships between submissions, actual values, and their presentation
- XBRL tags provide standardized definitions for financial concepts
- The database schema is optimized for querying relationships between financial statements and their components