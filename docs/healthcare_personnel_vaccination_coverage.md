# Healthcare Personnel Vaccination Coverage

This table contains data about vaccination coverage among healthcare personnel across different regions and seasons.

## Table Description

The `HEALTHCARE_PERSONNEL_VACCINATION_COVERAGE` table tracks vaccination rates among different types of healthcare personnel across various geographic regions and seasons. This data is particularly valuable for understanding immunization trends in healthcare settings.

## Columns

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| VACCINE | VARCHAR(100) | Type of vaccine administered (e.g., Seasonal Influenza) |
| GEOGRAPHY_TYPE | VARCHAR(50) | Type of geographic region (e.g., States) |
| GEOGRAPHY | VARCHAR(100) | Name of the geographic region |
| SEASON | VARCHAR(20) | Vaccination season (e.g., 2018-19) |
| PERSONNEL_TYPE | VARCHAR(100) | Category of healthcare personnel |
| ESTIMATE_PERCENTAGE | FLOAT | Estimated vaccination coverage percentage |
| CONFIDENCE_INTERVAL_95_PERCENT | VARCHAR(50) | 95% confidence interval for the estimate |
| SAMPLE_SIZE | INTEGER | Number of individuals in the sample |

## Example Queries

### 1. Get Average Vaccination Rates by Season

```sql
SELECT 
    SEASON,
    AVG(ESTIMATE_PERCENTAGE) as AVG_VACCINATION_RATE,
    COUNT(DISTINCT GEOGRAPHY) as NUMBER_OF_REGIONS
FROM HEALTHCARE_PERSONNEL_VACCINATION_COVERAGE
GROUP BY SEASON
ORDER BY SEASON DESC;
```

### 2. Find Top 5 States with Highest Vaccination Rates in Recent Seasons

```sql
SELECT 
    GEOGRAPHY,
    SEASON,
    ESTIMATE_PERCENTAGE,
    SAMPLE_SIZE
FROM HEALTHCARE_PERSONNEL_VACCINATION_COVERAGE
WHERE GEOGRAPHY_TYPE = 'States'
    AND SEASON >= '2020-21'
ORDER BY ESTIMATE_PERCENTAGE DESC
LIMIT 5;
```

### 3. Compare Vaccination Rates Across Different Personnel Types

```sql
SELECT 
    PERSONNEL_TYPE,
    AVG(ESTIMATE_PERCENTAGE) as AVG_VACCINATION_RATE,
    SUM(SAMPLE_SIZE) as TOTAL_SAMPLE_SIZE
FROM HEALTHCARE_PERSONNEL_VACCINATION_COVERAGE
GROUP BY PERSONNEL_TYPE
ORDER BY AVG_VACCINATION_RATE DESC;
```

### 4. Trend Analysis Over Seasons for a Specific State

```sql
SELECT 
    SEASON,
    GEOGRAPHY,
    ESTIMATE_PERCENTAGE,
    SAMPLE_SIZE
FROM HEALTHCARE_PERSONNEL_VACCINATION_COVERAGE
WHERE GEOGRAPHY = 'New Jersey'
ORDER BY SEASON;
```