# Adult Vaccination Coverage

This table contains CDC data on vaccination coverage among adults aged 18 years and older across different geographic areas, demographics, and time periods.

## Table Structure

- **VACCINE**: Type of vaccine administered (e.g., Tetanus, Zoster)
- **DOSE**: Specific dose type or schedule (e.g., Tdap, Td or Tdap)
- **GEOGRAPHY_TYPE**: Level of geographic aggregation (e.g., States/Local Areas)
- **GEOGRAPHY**: Name of the geographic area
- **FIPS**: Federal Information Processing Standards (FIPS) code
- **SURVEY_YEAR**: Year the survey was conducted
- **DIMENSION_TYPE**: Demographic or categorical dimension (e.g., age group)
- **DIMENSION**: Specific category within the dimension type
- **ESTIMATE_PERCENTAGE**: Estimated vaccination coverage percentage
- **CONFIDENCE_INTERVAL**: 95% Confidence Interval for the estimate
- **SAMPLE_SIZE**: Number of individuals in the sample

## Example Queries

1. Get overall vaccination rates by vaccine type for the most recent year:
```sql
SELECT 
    VACCINE,
    AVG(ESTIMATE_PERCENTAGE) as avg_coverage,
    COUNT(*) as sample_count
FROM ADULT_VACCINATION_COVERAGE
WHERE 
    SURVEY_YEAR = (SELECT MAX(SURVEY_YEAR) FROM ADULT_VACCINATION_COVERAGE)
    AND DIMENSION = 'Overall'
GROUP BY VACCINE
ORDER BY avg_coverage DESC;
```

2. Track Tdap vaccination trends over time:
```sql
SELECT 
    SURVEY_YEAR,
    AVG(ESTIMATE_PERCENTAGE) as coverage_rate,
    COUNT(DISTINCT GEOGRAPHY) as locations_count
FROM ADULT_VACCINATION_COVERAGE
WHERE 
    VACCINE = 'Tetanus'
    AND DOSE = 'Tdap'
    AND DIMENSION = 'Overall'
GROUP BY SURVEY_YEAR
ORDER BY SURVEY_YEAR;
```

3. Compare vaccination rates across different demographic dimensions:
```sql
SELECT 
    DIMENSION_TYPE,
    DIMENSION,
    AVG(ESTIMATE_PERCENTAGE) as avg_coverage,
    COUNT(*) as sample_count
FROM ADULT_VACCINATION_COVERAGE
WHERE 
    SURVEY_YEAR = 2019
    AND VACCINE = 'Tetanus'
GROUP BY DIMENSION_TYPE, DIMENSION
ORDER BY DIMENSION_TYPE, avg_coverage DESC;
```