# Healthcare Personnel Vaccination Coverage

This table contains data about vaccination coverage among healthcare personnel across different locations and years.

## Table Structure

- **Table Name**: HEALTHCARE_PERSONNEL_VACCINATION_COVERAGE
- **Database**: CDC_DATASET
- **Schema**: PUBLIC

### Columns

| Column Name | Type | Description |
|------------|------|-------------|
| YEAR | NUMBER | Year of data collection |
| LOCATION | VARCHAR | Geographic location (state or territory) |
| MEASURE | VARCHAR | Type of vaccination measure being reported |
| ESTIMATE | NUMBER | Vaccination coverage estimate percentage |
| SAMPLE_SIZE | NUMBER | Number of healthcare personnel in the sample |
| CONFIDENCE_LIMIT_LOW | NUMBER | Lower bound of the 95% confidence interval |
| CONFIDENCE_LIMIT_HIGH | NUMBER | Upper bound of the 95% confidence interval |

## Example Queries

1. Get the national vaccination coverage trends over time:
```sql
SELECT 
    YEAR,
    MEASURE,
    AVG(ESTIMATE) as avg_coverage,
    AVG(SAMPLE_SIZE) as avg_sample_size
FROM HEALTHCARE_PERSONNEL_VACCINATION_COVERAGE
WHERE LOCATION = 'United States'
GROUP BY YEAR, MEASURE
ORDER BY YEAR DESC, MEASURE;
```

2. Find states with highest vaccination coverage in the most recent year:
```sql
WITH latest_year AS (
    SELECT MAX(YEAR) as max_year 
    FROM HEALTHCARE_PERSONNEL_VACCINATION_COVERAGE
)
SELECT 
    LOCATION,
    MEASURE,
    ESTIMATE,
    CONFIDENCE_LIMIT_LOW,
    CONFIDENCE_LIMIT_HIGH
FROM HEALTHCARE_PERSONNEL_VACCINATION_COVERAGE
WHERE YEAR = (SELECT max_year FROM latest_year)
    AND LOCATION != 'United States'
ORDER BY ESTIMATE DESC
LIMIT 10;
```

3. Compare vaccination coverage between regions:
```sql
SELECT 
    YEAR,
    MEASURE,
    LOCATION,
    ESTIMATE,
    SAMPLE_SIZE
FROM HEALTHCARE_PERSONNEL_VACCINATION_COVERAGE
WHERE YEAR = 2023
    AND LOCATION IN ('Northeast', 'Midwest', 'South', 'West')
ORDER BY MEASURE, ESTIMATE DESC;
```