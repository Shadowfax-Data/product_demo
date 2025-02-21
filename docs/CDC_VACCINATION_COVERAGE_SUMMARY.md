# CDC Vaccination Coverage Datasets Overview

This document provides a comprehensive overview of the CDC vaccination coverage datasets loaded into Snowflake. The datasets cover various population groups and provide insights into vaccination trends across different demographics, locations, and time periods.

## Available Tables

1. **ADOLESCENT_VACCINATION_COVERAGE**
   - Coverage for ages 13-17 years
   - Vaccines: Tdap, MenACWY, HPV
   - Years: 2008-2023

2. **ADULT_VACCINATION_COVERAGE**
   - Coverage for ages 18+ years
   - Vaccines: Pneumococcal, Tetanus, Zoster
   - Years: 2008-2023

3. **HEALTHCARE_PERSONNEL_VACCINATION_COVERAGE**
   - Coverage among healthcare workers
   - Primary focus on Influenza vaccination
   - Seasons: 2013-14 to 2020-21

4. **NURSING_HOME_RESIDENTS_VACCINATION_COVERAGE**
   - Coverage in nursing home settings
   - Vaccines: Influenza, Pneumococcal
   - Years: 2005-2021

5. **PREGNANT_WOMEN_VACCINATION_COVERAGE**
   - Coverage during pregnancy
   - Vaccines: Influenza, Tdap
   - Years: 2012-2022

6. **YOUNG_CHILDREN_VACCINATION_COVERAGE**
   - Coverage for ages 0-35 months
   - Multiple vaccines including Hep A, Hib, Influenza
   - Detailed geographic and demographic breakdowns

7. **KINDERGARTNERS_VACCINATION_COVERAGE**
   - School entry vaccination requirements
   - Multiple vaccines and exemption types
   - Years: 2008-2020

8. **CHILDREN_19_35_MONTHS_RACE_VACCINATION_COVERAGE**
   - Coverage by race, ethnicity, poverty level
   - Ages 19-35 months
   - Metropolitan vs non-metropolitan analysis

## Common Dimensions Across Tables

- **Geographic Location**: Most tables include state-level data
- **Time Period**: Generally covering 2008-2023 with variations
- **Demographics**: Age, race, ethnicity (where applicable)
- **Vaccine Types**: Various vaccines depending on population group

## Example Cross-Table Queries

### 1. Compare Vaccination Coverage Across Age Groups (2020)

```sql
WITH adolescent_rates AS (
  SELECT 
    'Adolescent (13-17)' as age_group,
    location,
    coverage_estimate
  FROM ADOLESCENT_VACCINATION_COVERAGE
  WHERE year = 2020
    AND vaccine_type = 'Tdap'
),
adult_rates AS (
  SELECT 
    'Adult (18+)' as age_group,
    location,
    coverage_estimate
  FROM ADULT_VACCINATION_COVERAGE
  WHERE year = 2020
    AND vaccine_type = 'Tdap'
)
SELECT 
  location,
  age_group,
  coverage_estimate
FROM adolescent_rates
UNION ALL
SELECT 
  location,
  age_group,
  coverage_estimate
FROM adult_rates
ORDER BY location, age_group;
```

### 2. Vaccination Coverage Trends in Vulnerable Populations (2019-2020)

```sql
WITH pregnant_women AS (
  SELECT 
    'Pregnant Women' as population_group,
    year,
    AVG(coverage_estimate) as avg_coverage
  FROM PREGNANT_WOMEN_VACCINATION_COVERAGE
  WHERE year IN (2019, 2020)
    AND vaccine_type = 'Influenza'
  GROUP BY year
),
nursing_home AS (
  SELECT 
    'Nursing Home Residents' as population_group,
    year,
    AVG(coverage_estimate) as avg_coverage
  FROM NURSING_HOME_RESIDENTS_VACCINATION_COVERAGE
  WHERE year IN (2019, 2020)
    AND vaccine_type = 'Influenza'
  GROUP BY year
),
healthcare AS (
  SELECT 
    'Healthcare Personnel' as population_group,
    year,
    AVG(coverage_estimate) as avg_coverage
  FROM HEALTHCARE_PERSONNEL_VACCINATION_COVERAGE
  WHERE year IN (2019, 2020)
  GROUP BY year
)
SELECT *
FROM pregnant_women
UNION ALL
SELECT *
FROM nursing_home
UNION ALL
SELECT *
FROM healthcare
ORDER BY population_group, year;
```

### 3. Childhood Vaccination Coverage by Demographics (2020)

```sql
WITH race_data AS (
  SELECT 
    race_ethnicity,
    AVG(coverage_estimate) as avg_coverage
  FROM CHILDREN_19_35_MONTHS_RACE_VACCINATION_COVERAGE
  WHERE year = 2020
  GROUP BY race_ethnicity
),
kindergarten_data AS (
  SELECT 
    'Overall Kindergarten' as group_type,
    AVG(coverage_estimate) as avg_coverage
  FROM KINDERGARTNERS_VACCINATION_COVERAGE
  WHERE year = 2020
)
SELECT *
FROM race_data
UNION ALL
SELECT *
FROM kindergarten_data
ORDER BY avg_coverage DESC;
```

### 4. Geographic Variation Analysis (2020)

```sql
WITH coverage_by_state AS (
  SELECT 
    location,
    'Young Children' as population_group,
    AVG(coverage_estimate) as avg_coverage
  FROM YOUNG_CHILDREN_VACCINATION_COVERAGE
  WHERE year = 2020
  GROUP BY location
  
  UNION ALL
  
  SELECT 
    location,
    'Adolescents' as population_group,
    AVG(coverage_estimate) as avg_coverage
  FROM ADOLESCENT_VACCINATION_COVERAGE
  WHERE year = 2020
  GROUP BY location
  
  UNION ALL
  
  SELECT 
    location,
    'Adults' as population_group,
    AVG(coverage_estimate) as avg_coverage
  FROM ADULT_VACCINATION_COVERAGE
  WHERE year = 2020
  GROUP BY location
)
SELECT 
  location,
  population_group,
  avg_coverage
FROM coverage_by_state
WHERE location NOT IN ('National', 'United States')
ORDER BY location, population_group;
```

## Key Insights

1. **Age Group Coverage**:
   - Adolescent vaccination rates tend to be higher than adult rates for similar vaccines
   - School-entry requirements contribute to higher coverage in kindergartners

2. **Vulnerable Populations**:
   - Healthcare personnel generally maintain the highest coverage rates
   - Pregnant women show increasing vaccination trends
   - Nursing home residents have high but variable coverage rates

3. **Geographic Patterns**:
   - Significant variation exists between states
   - Urban areas generally show higher coverage rates
   - Some regions consistently perform above or below national averages

4. **Demographic Disparities**:
   - Coverage rates vary by race/ethnicity and socioeconomic status
   - Metropolitan vs non-metropolitan differences are observed
   - Poverty level impacts vaccination coverage

## Data Quality Notes

- Some tables contain special values (NR, NR*, --) indicating non-reported or suppressed data
- Confidence intervals are provided where available
- Coverage estimates are generally presented as percentages
- Different time periods may use different methodologies for data collection

## Recommended Usage

1. **Trend Analysis**: Use year-over-year comparisons within population groups
2. **Geographic Comparisons**: Compare states or regions while considering population size
3. **Demographic Studies**: Consider multiple demographic factors when analyzing disparities
4. **Cross-Population Analysis**: Account for different baseline characteristics when comparing groups