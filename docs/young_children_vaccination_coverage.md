# Young Children Vaccination Coverage (0-35 Months)

## Table Description
The `YOUNG_CHILDREN_VACCINATION_COVERAGE` table contains vaccination coverage data for children aged 0-35 months across different vaccines, locations, and demographic dimensions. The data includes vaccination rates, sample sizes, and confidence intervals for various demographic groups and geographic locations.

## Table Structure

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| LOCATION | VARCHAR(100) | Geographic location (state or region) |
| VACCINE | VARCHAR(100) | Type of vaccine administered |
| YEAR | NUMBER | Year of data collection |
| DIMENSION | VARCHAR(100) | Demographic dimension (e.g., Race/Ethnicity, Income, etc.) |
| DIMENSION_LEVEL | VARCHAR(100) | Specific category within the dimension |
| SAMPLE_SIZE | NUMBER | Number of children in the sample |
| ESTIMATE | NUMBER | Estimated vaccination coverage percentage |
| CI_LOW | NUMBER | Lower bound of 95% confidence interval |
| CI_HIGH | NUMBER | Upper bound of 95% confidence interval |

## Example Queries

1. Get average vaccination coverage by vaccine type for the most recent year:
```sql
SELECT 
    VACCINE,
    AVG(ESTIMATE) as AVG_COVERAGE,
    MIN(ESTIMATE) as MIN_COVERAGE,
    MAX(ESTIMATE) as MAX_COVERAGE
FROM YOUNG_CHILDREN_VACCINATION_COVERAGE
WHERE DIMENSION = 'Total'
AND YEAR = (SELECT MAX(YEAR) FROM YOUNG_CHILDREN_VACCINATION_COVERAGE)
GROUP BY VACCINE
ORDER BY AVG_COVERAGE DESC;
```

2. Compare vaccination coverage across different income levels:
```sql
SELECT 
    DIMENSION_LEVEL,
    YEAR,
    AVG(ESTIMATE) as AVG_COVERAGE
FROM YOUNG_CHILDREN_VACCINATION_COVERAGE
WHERE DIMENSION = 'Income'
GROUP BY DIMENSION_LEVEL, YEAR
ORDER BY YEAR DESC, AVG_COVERAGE DESC;
```

3. Find states with the highest and lowest vaccination coverage:
```sql
WITH RankedLocations AS (
    SELECT 
        LOCATION,
        VACCINE,
        ESTIMATE,
        RANK() OVER (PARTITION BY VACCINE ORDER BY ESTIMATE DESC) as HighRank,
        RANK() OVER (PARTITION BY VACCINE ORDER BY ESTIMATE ASC) as LowRank
    FROM YOUNG_CHILDREN_VACCINATION_COVERAGE
    WHERE DIMENSION = 'Total'
    AND YEAR = (SELECT MAX(YEAR) FROM YOUNG_CHILDREN_VACCINATION_COVERAGE)
    AND LOCATION NOT LIKE 'HHS%'
)
SELECT 
    VACCINE,
    MAX(CASE WHEN HighRank = 1 THEN LOCATION END) as Highest_Coverage_State,
    MAX(CASE WHEN HighRank = 1 THEN ESTIMATE END) as Highest_Coverage_Pct,
    MAX(CASE WHEN LowRank = 1 THEN LOCATION END) as Lowest_Coverage_State,
    MAX(CASE WHEN LowRank = 1 THEN ESTIMATE END) as Lowest_Coverage_Pct
FROM RankedLocations
WHERE HighRank = 1 OR LowRank = 1
GROUP BY VACCINE
ORDER BY VACCINE;
```

4. Track vaccination trends over time:
```sql
SELECT 
    YEAR,
    VACCINE,
    AVG(ESTIMATE) as AVG_COVERAGE
FROM YOUNG_CHILDREN_VACCINATION_COVERAGE
WHERE DIMENSION = 'Total'
AND LOCATION = 'United States'
GROUP BY YEAR, VACCINE
ORDER BY VACCINE, YEAR;
```