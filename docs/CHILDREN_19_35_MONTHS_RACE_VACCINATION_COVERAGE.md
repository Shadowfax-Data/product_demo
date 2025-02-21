# Children 19-35 Months Vaccination Coverage by Race and Demographics

This table contains vaccination coverage data for children aged 19-35 months, broken down by race, Hispanic origin, poverty level, and metropolitan residence location.

## Table Structure

- **YEAR**: Year of data collection
- **RACE_ETHNICITY**: Race and ethnicity category (e.g., White non-Hispanic, Black non-Hispanic, Hispanic)
- **POVERTY_LEVEL**: Poverty level category (Above/Below poverty level)
- **RESIDENCE_LOCATION**: Location of residence in metropolitan area (MSA central city, MSA non-central city, Non-MSA)
- **VACCINE_TYPE**: Type of vaccine administered
- **COVERAGE_PERCENTAGE**: Vaccination coverage percentage
- **CONFIDENCE_INTERVAL_LOW**: Lower bound of 95% confidence interval
- **CONFIDENCE_INTERVAL_HIGH**: Upper bound of 95% confidence interval
- **SAMPLE_SIZE**: Number of children in the sample

## Example Queries

1. Get average vaccination coverage by race/ethnicity across all years:
```sql
SELECT 
    RACE_ETHNICITY,
    AVG(COVERAGE_PERCENTAGE) as AVG_COVERAGE,
    COUNT(*) as MEASUREMENTS
FROM CHILDREN_19_35_MONTHS_RACE_VACCINATION_COVERAGE
GROUP BY RACE_ETHNICITY
ORDER BY AVG_COVERAGE DESC;
```

2. Compare vaccination coverage between poverty levels:
```sql
SELECT 
    POVERTY_LEVEL,
    VACCINE_TYPE,
    AVG(COVERAGE_PERCENTAGE) as AVG_COVERAGE
FROM CHILDREN_19_35_MONTHS_RACE_VACCINATION_COVERAGE
GROUP BY POVERTY_LEVEL, VACCINE_TYPE
ORDER BY VACCINE_TYPE, AVG_COVERAGE DESC;
```

3. Analyze trends over time for specific vaccines:
```sql
SELECT 
    YEAR,
    VACCINE_TYPE,
    AVG(COVERAGE_PERCENTAGE) as AVG_COVERAGE
FROM CHILDREN_19_35_MONTHS_RACE_VACCINATION_COVERAGE
GROUP BY YEAR, VACCINE_TYPE
ORDER BY VACCINE_TYPE, YEAR;
```

4. Compare coverage by metropolitan residence location:
```sql
SELECT 
    RESIDENCE_LOCATION,
    YEAR,
    AVG(COVERAGE_PERCENTAGE) as AVG_COVERAGE
FROM CHILDREN_19_35_MONTHS_RACE_VACCINATION_COVERAGE
GROUP BY RESIDENCE_LOCATION, YEAR
ORDER BY YEAR, AVG_COVERAGE DESC;
```