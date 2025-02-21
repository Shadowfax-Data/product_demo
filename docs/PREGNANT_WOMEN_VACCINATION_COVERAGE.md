# Pregnant Women Vaccination Coverage

This table contains data about vaccination coverage among pregnant women across different locations and years.

## Table Structure

- **VACCINE**: Type of vaccine administered (e.g., Influenza, Tdap)
- **GEOGRAPHY_TYPE**: Type of geographic region (e.g., States, National)
- **GEOGRAPHY**: Specific geographic location
- **SURVEY_YEAR**: Survey year or influenza season
- **DIMENSION_TYPE**: Type of demographic dimension (e.g., Race and Ethnicity, Age Group)
- **DIMENSION**: Specific demographic category within the dimension
- **ESTIMATE_PCT**: Estimated vaccination coverage percentage
- **CONFIDENCE_INTERVAL**: 95% Confidence Interval range
- **SAMPLE_SIZE**: Number of respondents in the sample

## Example Queries

1. Get average vaccination coverage by vaccine type and race/ethnicity:
```sql
SELECT 
    VACCINE,
    DIMENSION,
    AVG(ESTIMATE_PCT) as avg_coverage,
    SUM(SAMPLE_SIZE) as total_sample_size
FROM PREGNANT_WOMEN_VACCINATION_COVERAGE
WHERE DIMENSION_TYPE = 'Race and Ethnicity'
GROUP BY VACCINE, DIMENSION
ORDER BY VACCINE, avg_coverage DESC;
```

2. Track vaccination trends over time for Influenza vaccine:
```sql
SELECT 
    SURVEY_YEAR,
    GEOGRAPHY_TYPE,
    AVG(ESTIMATE_PCT) as avg_coverage,
    SUM(SAMPLE_SIZE) as total_sample_size
FROM PREGNANT_WOMEN_VACCINATION_COVERAGE
WHERE VACCINE = 'Influenza'
  AND DIMENSION_TYPE = 'Overall'
GROUP BY SURVEY_YEAR, GEOGRAPHY_TYPE
ORDER BY SURVEY_YEAR DESC;
```

3. Compare state-level coverage for the most recent year:
```sql
SELECT 
    GEOGRAPHY,
    VACCINE,
    ESTIMATE_PCT,
    CONFIDENCE_INTERVAL,
    SAMPLE_SIZE
FROM PREGNANT_WOMEN_VACCINATION_COVERAGE
WHERE SURVEY_YEAR = (SELECT MAX(SURVEY_YEAR) FROM PREGNANT_WOMEN_VACCINATION_COVERAGE)
  AND GEOGRAPHY_TYPE = 'States'
  AND DIMENSION_TYPE = 'Overall'
ORDER BY GEOGRAPHY, VACCINE;
```

4. Analyze vaccination disparities across demographic dimensions:
```sql
SELECT 
    DIMENSION_TYPE,
    DIMENSION,
    VACCINE,
    AVG(ESTIMATE_PCT) as avg_coverage,
    SUM(SAMPLE_SIZE) as total_sample_size
FROM PREGNANT_WOMEN_VACCINATION_COVERAGE
WHERE SURVEY_YEAR = (SELECT MAX(SURVEY_YEAR) FROM PREGNANT_WOMEN_VACCINATION_COVERAGE)
GROUP BY DIMENSION_TYPE, DIMENSION, VACCINE
HAVING total_sample_size > 100
ORDER BY DIMENSION_TYPE, VACCINE, avg_coverage DESC;
```

## Data Quality Notes

- Coverage estimates are provided as percentages
- Each estimate includes 95% confidence intervals
- Sample sizes are provided to indicate the reliability of estimates
- Some records may include footnotes with important contextual information