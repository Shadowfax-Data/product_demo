# ADOLESCENT_VACCINATION_COVERAGE

This table contains CDC data on vaccination coverage among adolescents aged 13-17 years.

## Table Structure

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| YEAR | NUMBER(4) | Year of data collection |
| LOCATION | VARCHAR | Geographic location (state or territory) |
| AGE_GROUP | VARCHAR | Age group of adolescents (13-17 years) |
| VACCINE_TYPE | VARCHAR | Type of vaccine administered |
| COVERAGE_PCT | FLOAT | Vaccination coverage percentage |
| SAMPLE_SIZE | NUMBER | Number of adolescents in the sample |
| CONFIDENCE_INTERVAL_LOW | FLOAT | Lower bound of 95% confidence interval |
| CONFIDENCE_INTERVAL_HIGH | FLOAT | Upper bound of 95% confidence interval |

## Example Queries

1. Get average vaccination coverage by vaccine type for the most recent year:
```sql
SELECT 
    VACCINE_TYPE,
    AVG(COVERAGE_PCT) as avg_coverage,
    COUNT(*) as location_count
FROM ADOLESCENT_VACCINATION_COVERAGE
WHERE YEAR = (SELECT MAX(YEAR) FROM ADOLESCENT_VACCINATION_COVERAGE)
GROUP BY VACCINE_TYPE
ORDER BY avg_coverage DESC;
```

2. Compare vaccination coverage trends over years:
```sql
SELECT 
    YEAR,
    VACCINE_TYPE,
    AVG(COVERAGE_PCT) as avg_coverage
FROM ADOLESCENT_VACCINATION_COVERAGE
GROUP BY YEAR, VACCINE_TYPE
ORDER BY VACCINE_TYPE, YEAR;
```

3. Find states with highest and lowest coverage for each vaccine:
```sql
WITH RankedCoverage AS (
    SELECT 
        YEAR,
        LOCATION,
        VACCINE_TYPE,
        COVERAGE_PCT,
        ROW_NUMBER() OVER (PARTITION BY YEAR, VACCINE_TYPE ORDER BY COVERAGE_PCT DESC) as highest_rank,
        ROW_NUMBER() OVER (PARTITION BY YEAR, VACCINE_TYPE ORDER BY COVERAGE_PCT ASC) as lowest_rank
    FROM ADOLESCENT_VACCINATION_COVERAGE
    WHERE LOCATION NOT IN ('United States', 'National')
)
SELECT 
    YEAR,
    VACCINE_TYPE,
    MAX(CASE WHEN highest_rank = 1 THEN LOCATION END) as highest_coverage_state,
    MAX(CASE WHEN highest_rank = 1 THEN COVERAGE_PCT END) as highest_coverage_pct,
    MAX(CASE WHEN lowest_rank = 1 THEN LOCATION END) as lowest_coverage_state,
    MAX(CASE WHEN lowest_rank = 1 THEN COVERAGE_PCT END) as lowest_coverage_pct
FROM RankedCoverage
WHERE highest_rank = 1 OR lowest_rank = 1
GROUP BY YEAR, VACCINE_TYPE
ORDER BY YEAR DESC, VACCINE_TYPE;
```