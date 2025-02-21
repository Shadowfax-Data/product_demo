# Adult Vaccination Coverage

This table contains CDC data about vaccination coverage among adults 18 years and older across different geographic areas, years, and population dimensions.

## Table Details

**Name:** `ADULT_VACCINATION_COVERAGE`  
**Database:** `CDC_DATASET`  
**Schema:** `PUBLIC`  
**Type:** Transient  

## Columns

| Column Name | Type | Description |
|------------|------|-------------|
| VACCINE | VARCHAR(100) | Type of vaccine administered |
| DOSE | VARCHAR(50) | Specific dose type or schedule of the vaccine |
| GEOGRAPHY_TYPE | VARCHAR(50) | Level of geographic aggregation (e.g., States/Local Areas) |
| GEOGRAPHY | VARCHAR(100) | Name of the geographic area |
| FIPS | VARCHAR(10) | Federal Information Processing Standards (FIPS) code |
| SURVEY_YEAR | NUMBER | Year the survey was conducted |
| DIMENSION_TYPE | VARCHAR(50) | Type of population dimension being measured |
| DIMENSION | VARCHAR(100) | Specific category within the dimension type |
| ESTIMATE_PERCENT | FLOAT | Estimated vaccination coverage percentage |
| CI_95_PERCENT | VARCHAR(50) | 95% Confidence Interval for the estimate |
| SAMPLE_SIZE | NUMBER | Number of individuals in the sample |

## Example Queries

### 1. Get the latest vaccination rates by state for Tdap vaccine

```sql
SELECT 
    GEOGRAPHY,
    SURVEY_YEAR,
    ESTIMATE_PERCENT,
    CI_95_PERCENT,
    SAMPLE_SIZE
FROM ADULT_VACCINATION_COVERAGE
WHERE 
    VACCINE = 'Tetanus'
    AND DOSE = 'Tdap'
    AND DIMENSION_TYPE = '>=18 Years'
    AND DIMENSION = 'Overall'
    AND SURVEY_YEAR = (
        SELECT MAX(SURVEY_YEAR) 
        FROM ADULT_VACCINATION_COVERAGE
        WHERE VACCINE = 'Tetanus' AND DOSE = 'Tdap'
    )
ORDER BY ESTIMATE_PERCENT DESC;
```

### 2. Track Shingles vaccination trends over time

```sql
SELECT 
    SURVEY_YEAR,
    AVG(ESTIMATE_PERCENT) as AVG_COVERAGE,
    COUNT(DISTINCT GEOGRAPHY) as NUM_STATES
FROM ADULT_VACCINATION_COVERAGE
WHERE 
    VACCINE = 'Zoster (Shingles)'
    AND DIMENSION_TYPE = '>=60 Years'
    AND DIMENSION = 'Overall'
GROUP BY SURVEY_YEAR
ORDER BY SURVEY_YEAR;
```

### 3. Compare vaccination rates across different age groups

```sql
SELECT 
    DIMENSION_TYPE,
    VACCINE,
    AVG(ESTIMATE_PERCENT) as AVG_COVERAGE,
    COUNT(*) as NUM_OBSERVATIONS
FROM ADULT_VACCINATION_COVERAGE
WHERE 
    SURVEY_YEAR = 2019
    AND DIMENSION = 'Overall'
GROUP BY DIMENSION_TYPE, VACCINE
HAVING COUNT(*) > 10
ORDER BY VACCINE, AVG_COVERAGE DESC;
```