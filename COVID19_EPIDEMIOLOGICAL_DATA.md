# COVID19_EPIDEMIOLOGICAL_DATA Database Documentation

This database contains comprehensive COVID-19 epidemiological data from various sources including WHO, JHU, CDC, and other health organizations.

## Tables Overview

### JHU_COVID_19
Global case counts from Johns Hopkins University

Sample Query:
```sql
SELECT 
    country_region,
    province_state,
    date,
    confirmed,
    deaths,
    recovered
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.JHU_COVID_19
WHERE date >= DATEADD(day, -30, CURRENT_DATE())
ORDER BY date DESC, confirmed DESC
LIMIT 10;
```

### CDC_TESTING
US COVID-19 testing data from CDC

Sample Query:
```sql
SELECT 
    state,
    date,
    total_test_results,
    positive,
    negative
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.CDC_TESTING
WHERE date >= DATEADD(day, -7, CURRENT_DATE())
ORDER BY date DESC, total_test_results DESC;
```

### OWID_VACCINATIONS
Our World in Data vaccination statistics

Sample Query:
```sql
SELECT 
    location,
    date,
    total_vaccinations,
    people_vaccinated,
    people_fully_vaccinated
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.OWID_VACCINATIONS
WHERE total_vaccinations IS NOT NULL
ORDER BY date DESC, total_vaccinations DESC
LIMIT 10;
```

### GOOG_GLOBAL_MOBILITY_REPORT
Google Community Mobility Reports showing movement trends

Sample Query:
```sql
SELECT 
    country_region,
    sub_region_1,
    date,
    retail_and_recreation_percent_change_from_baseline,
    grocery_and_pharmacy_percent_change_from_baseline,
    parks_percent_change_from_baseline,
    transit_stations_percent_change_from_baseline,
    workplaces_percent_change_from_baseline,
    residential_percent_change_from_baseline
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.GOOG_GLOBAL_MOBILITY_REPORT
WHERE date >= DATEADD(day, -7, CURRENT_DATE())
ORDER BY date DESC, country_region;
```

### WHO_SITUATION_REPORTS
World Health Organization situation reports

Sample Query:
```sql
SELECT 
    country,
    date,
    cases,
    deaths
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.WHO_SITUATION_REPORTS
WHERE date >= DATEADD(day, -14, CURRENT_DATE())
ORDER BY date DESC, cases DESC;
```

## Table Details

### JHU_COVID_19
Johns Hopkins University COVID-19 case tracking data

**Columns:**
- COUNTRY_REGION (TEXT) - ISO-3166-1 entity name
- PROVINCE_STATE (TEXT) - ISO-3166-2 entity name
- COUNTY (TEXT) - County name for US counties
- FIPS (TEXT) - County FIPS code
- DATE (DATE) - Date of data point
- CASE_TYPE (TEXT) - Case type: one of confirmed, active, recovered or deaths
- CASES (NUMBER) - Case count in geography and case type
- LONG (FLOAT) - Indicative longitude of geography (centroid)
- LAT (FLOAT) - Indicative latitude of geography (centroid)
- ISO3166_1 (TEXT) - ISO-3166-1 code for geography of report
- ISO3166_2 (TEXT) - ISO-3166-2 code for geography of report
- DIFFERENCE (NUMBER) - Change in case count since previous date
- LAST_UPDATED_DATE (TIMESTAMP) - Timestamp of last update (UTC)
- LAST_REPORTED_FLAG (BOOLEAN) - New data in last import

### CDC_TESTING
CDC COVID-19 testing data

**Columns:**
- ISO3166_1 (TEXT) - Country code
- ISO3166_2 (TEXT) - State/Province code
- DATE (TIMESTAMP) - Date of report
- POSITIVE (NUMBER) - Number of positive tests
- NEGATIVE (NUMBER) - Number of negative tests
- INCONCLUSIVE (NUMBER) - Number of inconclusive tests

### OWID_VACCINATIONS
Our World in Data vaccination tracking

**Columns:**
- DATE (DATE) - Date of report
- COUNTRY_REGION (TEXT) - Country name
- ISO3166_1 (TEXT) - Country code
- TOTAL_VACCINATIONS (NUMBER) - Total number of doses administered
- PEOPLE_VACCINATED (NUMBER) - Total number of people who received at least one dose
- PEOPLE_FULLY_VACCINATED (NUMBER) - Total number of people fully vaccinated
- DAILY_VACCINATIONS_RAW (NUMBER) - Raw daily vaccination count
- DAILY_VACCINATIONS (NUMBER) - Smoothed daily vaccination count
- TOTAL_VACCINATIONS_PER_HUNDRED (FLOAT) - Total vaccinations per 100 people
- PEOPLE_VACCINATED_PER_HUNDRED (FLOAT) - People vaccinated per 100 people
- PEOPLE_FULLY_VACCINATED_PER_HUNDRED (FLOAT) - People fully vaccinated per 100 people
- DAILY_VACCINATIONS_PER_MILLION (FLOAT) - Daily vaccinations per million people
- VACCINES (TEXT) - Vaccines being administered
- SOURCE_NAME (TEXT) - Data source name
- SOURCE_WEBSITE (TEXT) - Data source website
- LAST_UPDATE_DATE (TIMESTAMP) - Last update timestamp
- LAST_REPORTED_FLAG (BOOLEAN) - New data in last import

### WHO_SITUATION_REPORTS
World Health Organization situation reports

**Columns:**
- COUNTRY (TEXT) - Country name
- TOTAL_CASES (NUMBER) - Total case count for geography
- CASES_NEW (NUMBER) - New cases since last situation report
- DEATHS (NUMBER) - Total mortality count for geography
- DEATHS_NEW (NUMBER) - New mortality since last situation report
- TRANSMISSION_CLASSIFICATION (TEXT) - Transmission classification
- DAYS_SINCE_LAST_REPORTED_CASE (NUMBER) - Days since last reported case
- ISO3166_1 (TEXT) - ISO 3166-1 code for geography
- COUNTRY_REGION (TEXT) - ISO-3166-1 entity name
- DATE (DATE) - Date of data point
- SITUATION_REPORT_NAME (TEXT) - WHO Situation Report title
- SITUATION_REPORT_URL (TEXT) - WHO Situation Report URL
- LAST_UPDATE_DATE (TIMESTAMP) - Timestamp of last update (UTC)
- LAST_REPORTED_FLAG (BOOLEAN) - New data in last import