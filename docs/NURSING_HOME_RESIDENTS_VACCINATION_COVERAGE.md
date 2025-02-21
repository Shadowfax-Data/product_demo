# Nursing Home Residents Vaccination Coverage

This table contains data about vaccination coverage among nursing home residents across different demographics and geographic regions in the United States.

## Table Structure

- **VACCINE**: Type of vaccine administered (e.g., Seasonal Influenza, Pneumococcal)
- **GEOGRAPHY_TYPE**: Type of geographic region (e.g., HHS Regions/National)
- **GEOGRAPHY**: Specific geographic location
- **SURVEY_YEAR**: Survey year or influenza season (e.g., 2015-16 for flu seasons)
- **DIMENSION_TYPE**: Type of demographic dimension (e.g., Age, Marital Status)
- **DIMENSION**: Specific demographic category within the dimension
- **ESTIMATE_PERCENTAGE**: Vaccination coverage estimate percentage
- **POPULATION_SIZE**: Size of the population in the demographic category

## Example Queries

1. Get national vaccination coverage trends by vaccine type:
```sql
SELECT 
    VACCINE,
    SURVEY_YEAR,
    AVG(ESTIMATE_PERCENTAGE) as avg_coverage
FROM NURSING_HOME_RESIDENTS_VACCINATION_COVERAGE
WHERE GEOGRAPHY_TYPE = 'HHS Regions/National'
  AND GEOGRAPHY = 'National'
GROUP BY VACCINE, SURVEY_YEAR
ORDER BY VACCINE, SURVEY_YEAR;
```

2. Compare vaccination coverage across age groups:
```sql
SELECT 
    DIMENSION as age_group,
    VACCINE,
    AVG(ESTIMATE_PERCENTAGE) as avg_coverage,
    SUM(POPULATION_SIZE) as total_population
FROM NURSING_HOME_RESIDENTS_VACCINATION_COVERAGE
WHERE DIMENSION_TYPE = 'Age'
  AND ESTIMATE_PERCENTAGE IS NOT NULL
GROUP BY DIMENSION, VACCINE
ORDER BY VACCINE, DIMENSION;
```

3. Analyze regional differences in vaccination coverage:
```sql
SELECT 
    GEOGRAPHY as region,
    VACCINE,
    SURVEY_YEAR,
    AVG(ESTIMATE_PERCENTAGE) as avg_coverage
FROM NURSING_HOME_RESIDENTS_VACCINATION_COVERAGE
WHERE GEOGRAPHY_TYPE = 'HHS Regions/National'
  AND GEOGRAPHY != 'National'
  AND ESTIMATE_PERCENTAGE IS NOT NULL
GROUP BY GEOGRAPHY, VACCINE, SURVEY_YEAR
ORDER BY VACCINE, SURVEY_YEAR, avg_coverage DESC;
```

## Data Notes

- Coverage data is available for different vaccines including Seasonal Influenza and Pneumococcal
- Data is broken down by various demographic dimensions (Age, Marital Status, etc.)
- Geographic coverage includes both national and HHS regional levels
- Some estimates may be NA (null) due to insufficient sample size
- Survey years are presented in different formats depending on the vaccine type (e.g., '2015-16' for flu seasons)