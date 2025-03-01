# SEC Financial Statement Dataset Documentation

## Overview
This dataset contains financial statement data from the U.S. Securities and Exchange Commission (SEC). The data is sourced from the SEC's Financial Statement Data Sets, specifically from the 2024 Q4 release. The dataset provides detailed financial information submitted by companies in their XBRL (eXtensible Business Reporting Language) filings.

## Dataset Structure
The dataset is organized into four main components, each serving a specific purpose in representing financial statement information:

### 1. Submissions (SUB.txt)
Contains metadata about company submissions to the SEC.

**Table: SEC_SUBMISSIONS**
- Primary Key: `adsh` (20-character EDGAR accession number)
- Key Fields:
  - `cik`: Central Index Key (company identifier)
  - `name`: Company name
  - `sic`: Standard Industrial Classification
  - `countryba`: Business address country
  - `stprba`: Business address state/province
  - `cityba`: Business address city
  - `zipba`: Business address ZIP code
  - `bas1`: Business address street line 1
  - `form`: SEC form type
  - `period`: Balance sheet date (YYYYMMDD)
  - `fy`: Fiscal year
  - `fp`: Fiscal period focus
  - `filed`: Filing date (YYYYMMDD)

### 2. Numbers (NUM.txt)
Contains the actual financial statement values and their contexts.

**Table: SEC_NUMBERS**
- Primary Key: Composite (`adsh`, `tag`, `version`, `ddate`, `qtrs`)
- Foreign Key: `adsh` references SEC_SUBMISSIONS
- Key Fields:
  - `tag`: XBRL tag
  - `version`: XBRL taxonomy version
  - `ddate`: Date of data point (YYYYMMDD)
  - `qtrs`: Number of quarters represented
  - `uom`: Unit of measure (e.g., USD)
  - `value`: Actual numerical value
  - `footnote`: Associated footnote text

### 3. Tags (TAG.txt)
Contains metadata about the XBRL tags used in the financial statements.

**Table: SEC_TAGS**
- Primary Key: Composite (`tag`, `version`)
- Key Fields:
  - `tag`: XBRL tag name
  - `version`: XBRL taxonomy version
  - `custom`: Boolean indicating if tag is custom
  - `abstract`: Boolean indicating if tag is abstract
  - `datatype`: Data type (e.g., monetary, text)
  - `iord`: Item or dimension indicator
  - `crdr`: Credit/debit indicator
  - `tlabel`: Tag label
  - `doc`: Documentation text

### 4. Presentations (PRE.txt)
Contains information about how the financial statement items are presented.

**Table: SEC_PRESENTATIONS**
- Primary Key: Composite (`adsh`, `report`, `line`)
- Foreign Key: `adsh` references SEC_SUBMISSIONS
- Key Fields:
  - `report`: Report number
  - `line`: Line number
  - `stmt`: Financial statement type
  - `inpth`: Indent level
  - `rfile`: Reference file type
  - `tag`: XBRL tag
  - `version`: XBRL taxonomy version
  - `plabel`: Presentation label

## Relationships Between Tables
1. **SEC_SUBMISSIONS** is the central table:
   - Each submission (identified by `adsh`) can have multiple entries in SEC_NUMBERS
   - Each submission can have multiple presentation records in SEC_PRESENTATIONS

2. **SEC_NUMBERS** links to:
   - SEC_SUBMISSIONS through `adsh`
   - SEC_TAGS through the combination of `tag` and `version`

3. **SEC_PRESENTATIONS** links to:
   - SEC_SUBMISSIONS through `adsh`
   - SEC_TAGS through the combination of `tag` and `version`

4. **SEC_TAGS** serves as a reference table:
   - Provides metadata for tags used in both SEC_NUMBERS and SEC_PRESENTATIONS

## Data Processing Pipeline
1. Data is downloaded from SEC's website using `download_sec_data.py`
2. Text files are converted to CSV format using `convert_to_csv.py`
3. Data analysis is performed using `analyze_data.py`
4. Snowflake tables are created using `create_snowflake_tables.py`
5. Data is loaded into Snowflake using `load_to_snowflake.py`

## Usage Notes
- All dates are in YYYYMMDD format
- Monetary values are typically in millions of dollars (USD)
- The dataset includes both standard XBRL tags and custom company-specific tags
- Some fields may contain NULL values where data is not applicable or not provided
- The data represents quarterly financial statements and related disclosures