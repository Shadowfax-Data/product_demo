# SEC Financial Statement Dataset (Q4 2024)

## Overview
This dataset contains detailed financial statement information from SEC filings for Q4 2024. The data has been processed and loaded into Snowflake for analysis. The dataset includes numerical data points, presentation information, submission metadata, and XBRL tag definitions.

## Data Structure
The data is organized into four main tables in Snowflake, each serving a specific purpose in representing the SEC filing information.

### Table Statistics
| Table Name | Row Count | Size (bytes) | Description |
|------------|-----------|--------------|-------------|
| SEC_NUMERICAL_DATA | 3,705,077 | 77,544,448 | Financial data points from SEC filings |
| SEC_PRESENTATION | 737,504 | 9,735,168 | Presentation and structure information |
| SEC_SUBMISSIONS | 6,491 | 791,040 | Filing submission metadata |
| SEC_TAGS | 84,365 | 3,680,768 | XBRL tag definitions and documentation |

## Table Schemas

### SEC_NUMERICAL_DATA
Contains the actual financial data points from SEC filings.

Key Columns:
- `ADSH` (VARCHAR(20)): SEC Accession Number - Filing Identifier
- `TAG` (VARCHAR(256)): Financial Element Tag/Metric Name
- `VERSION` (VARCHAR(20)): Version of the Tag
- `DDATE` (NUMBER): Date of Data Point (YYYYMMDD)
- `VALUE` (FLOAT): Numerical Value of the Data Point
- `UOM` (VARCHAR(20)): Unit of Measure (e.g., USD, shares)
- `QTRS` (NUMBER): Number of Quarters Represented

### SEC_PRESENTATION
Defines how financial information should be presented in reports.

Key Columns:
- `ADSH` (VARCHAR(20)): SEC Accession Number - Filing Identifier
- `REPORT` (NUMBER): Report Index Number
- `LINE` (NUMBER): Line Number within Report
- `STMT` (VARCHAR(2)): Financial Statement Type Code
- `TAG` (VARCHAR(256)): Financial Element Tag
- `PLABEL` (VARCHAR): Presentation Label
- `NEGATING` (NUMBER(1,0)): Indicates if Value Should be Negated

### SEC_SUBMISSIONS
Contains metadata about SEC filings and submitting companies.

Key Columns:
- `ADSH` (VARCHAR(20)): SEC Accession Number - Filing Identifier
- `CIK` (NUMBER): Central Index Key (CIK)
- `NAME` (VARCHAR(150)): Entity Name
- `SIC` (NUMBER): Standard Industrial Classification
- `FORM` (VARCHAR(10)): SEC Form Type
- `FILED` (NUMBER): Filing Date (YYYYMMDD)
- `PERIOD` (NUMBER): Period End Date (YYYYMMDD)
- `FY` (NUMBER): Fiscal Year
- `FP` (VARCHAR(2)): Fiscal Period

### SEC_TAGS
Defines XBRL tags used in the financial statements.

Key Columns:
- `TAG` (VARCHAR(256)): Financial Element Tag
- `VERSION` (VARCHAR(20)): Version of the Tag
- `CUSTOM` (NUMBER): Custom Tag Indicator
- `DATATYPE` (VARCHAR(20)): Data Type
- `CRDR` (VARCHAR(1)): Credit/Debit Type
- `TLABEL` (VARCHAR): Tag Label
- `DOC` (VARCHAR): Documentation

## Data Relationships
- The `ADSH` field serves as the primary link between SEC_NUMERICAL_DATA, SEC_PRESENTATION, and SEC_SUBMISSIONS tables
- The `TAG` and `VERSION` fields connect SEC_NUMERICAL_DATA and SEC_PRESENTATION to SEC_TAGS

## Usage Notes
1. The dataset represents Q4 2024 SEC filings
2. Numerical values are stored with their respective units of measure
3. Dates are stored in YYYYMMDD format
4. Text fields use VARCHAR with appropriate length limits
5. The data model supports both standard and custom XBRL tags