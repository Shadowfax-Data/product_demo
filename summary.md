# COVID-19 Database Documentation

This document provides a comprehensive overview of the COVID19_EPIDEMIOLOGICAL_DATA database, including detailed information about tables, their columns, and example queries for each data category.

## Table of Contents
1. [Global Case Tracking](#global-case-tracking)
2. [US-Specific Data](#us-specific-data)
3. [Country-Specific Data](#country-specific-data)
4. [Mobility and Policy Data](#mobility-and-policy-data)
5. [Vaccination Data](#vaccination-data)
6. [Cross-Reference Examples](#cross-reference-examples)

## Global Case Tracking

This section covers global COVID-19 case tracking data from multiple authoritative sources.

### JHU_COVID_19
**Description**: Johns Hopkins University's comprehensive global COVID-19 case tracking data, providing detailed information about cases, deaths, and recoveries at country, state, and county levels.

**Columns**:
- `DATE`: Date of the record
- `COUNTRY_REGION`: Name of the country/region
- `PROVINCE_STATE`: Name of the province/state (if applicable)
- `COUNTY`: Name of the county (if applicable)
- `CASE_TYPE`: Type of case (Confirmed, Deaths, Recovered)
- `CASES`: Cumulative number of cases
- `DIFFERENCE`: Daily change in cases
- `LAT`: Latitude of the location
- `LONG`: Longitude of the location
- `ISO3166_1`: Country code (ISO 3166-1 format)
- `ISO3166_2`: State/Province code (ISO 3166-2 format)
- `FIPS`: US FIPS code for counties
- `LAST_UPDATED_DATE`: Timestamp of last update
- `LAST_REPORTED_FLAG`: Boolean indicating if this is the most recent report

**Sample Query**:
```sql
SELECT 
    DATE,
    COUNTRY_REGION,
    CASE_TYPE,
    CASES,
    DIFFERENCE
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.JHU_COVID_19
WHERE COUNTRY_REGION = 'United States'
AND CASE_TYPE = 'Confirmed'
AND DATE >= DATEADD(days, -30, CURRENT_DATE())
ORDER BY DATE DESC;
```

### WHO_SITUATION_REPORTS
**Description**: World Health Organization's situation reports providing detailed country-level information about COVID-19 cases, deaths, and transmission classification.

**Columns**:
- `DATE`: Report date
- `COUNTRY_REGION`: Name of the country/region
- `COUNTRY`: Alternative country name
- `TOTAL_CASES`: Cumulative number of cases
- `CASES_NEW`: New cases reported
- `DEATHS`: Cumulative number of deaths
- `DEATHS_NEW`: New deaths reported
- `TRANSMISSION_CLASSIFICATION`: WHO's classification of transmission type
- `DAYS_SINCE_LAST_REPORTED_CASE`: Days elapsed since last reported case
- `SITUATION_REPORT_NAME`: Name of the WHO situation report
- `SITUATION_REPORT_URL`: URL to the original WHO report
- `ISO3166_1`: Country code
- `LAST_UPDATE_DATE`: Timestamp of last update
- `LAST_REPORTED_FLAG`: Boolean indicating if this is the most recent report

**Sample Query**:
```sql
SELECT 
    DATE,
    COUNTRY_REGION,
    TOTAL_CASES,
    CASES_NEW,
    DEATHS,
    DEATHS_NEW,
    TRANSMISSION_CLASSIFICATION
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.WHO_SITUATION_REPORTS
WHERE DATE >= DATEADD(days, -14, CURRENT_DATE())
AND CASES_NEW > 0
ORDER BY CASES_NEW DESC;
```

### ECDC_GLOBAL
**Description**: European Centre for Disease Prevention and Control's global COVID-19 data, providing daily updates on cases and deaths with population context.

**Columns**:
- `DATE`: Report date
- `COUNTRY_REGION`: Name of the country/region
- `CONTINENTEXP`: Continent name
- `POPULATION`: Country population
- `CASES`: Cumulative number of cases
- `DEATHS`: Cumulative number of deaths
- `CASES_SINCE_PREV_DAY`: New cases since previous day
- `DEATHS_SINCE_PREV_DAY`: New deaths since previous day
- `ISO3166_1`: Country code
- `LAST_UPDATE_DATE`: Timestamp of last update
- `LAST_REPORTED_FLAG`: Boolean indicating if this is the most recent report

**Sample Query**:
```sql
SELECT 
    DATE,
    COUNTRY_REGION,
    CASES,
    CASES_SINCE_PREV_DAY,
    DEATHS,
    DEATHS_SINCE_PREV_DAY,
    ROUND(CASES/POPULATION * 100000, 2) as CASES_PER_100K
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.ECDC_GLOBAL
WHERE DATE >= DATEADD(days, -7, CURRENT_DATE())
AND POPULATION > 0
ORDER BY CASES_PER_100K DESC;
```

### WHO_DAILY_REPORT
**Description**: World Health Organization's daily COVID-19 reports providing country-level statistics with population-adjusted metrics.

**Columns**:
- `DATE`: Timestamp of the report
- `COUNTRY_REGION`: Name of the country/region
- `ISO3166_1`: Country code
- `CASES`: New cases reported
- `DEATHS`: New deaths reported
- `CASES_TOTAL`: Cumulative total cases
- `DEATHS_TOTAL`: Cumulative total deaths
- `CASES_TOTAL_PER_100000`: Total cases per 100,000 population
- `DEATHS_TOTAL_PER_100000`: Total deaths per 100,000 population
- `TRANSMISSION_CLASSIFICATION`: WHO's classification of transmission type

**Sample Query**:
```sql
SELECT 
    DATE::DATE as REPORT_DATE,
    COUNTRY_REGION,
    CASES,
    DEATHS,
    CASES_TOTAL_PER_100000,
    DEATHS_TOTAL_PER_100000,
    TRANSMISSION_CLASSIFICATION
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.WHO_DAILY_REPORT
WHERE DATE >= DATEADD(days, -7, CURRENT_DATE())
ORDER BY CASES_TOTAL_PER_100000 DESC;
```

### WHO_TIMESERIES
**Description**: World Health Organization's time series data tracking the progression of COVID-19 cases and deaths over time, including population-adjusted metrics.

**Columns**:
- `DATE`: Timestamp of the record
- `COUNTRY_REGION`: Name of the country/region
- `ISO3166_1`: Country code
- `CASES`: New cases reported
- `DEATHS`: New deaths reported
- `CASES_TOTAL`: Cumulative total cases
- `DEATHS_TOTAL`: Cumulative total deaths
- `CASES_TOTAL_PER_100000`: Total cases per 100,000 population
- `DEATHS_TOTAL_PER_100000`: Total deaths per 100,000 population
- `TRANSMISSION_CLASSIFICATION`: WHO's classification of transmission type

**Sample Query**:
```sql
SELECT 
    DATE::DATE as REPORT_DATE,
    COUNTRY_REGION,
    CASES,
    DEATHS,
    CASES_TOTAL,
    DEATHS_TOTAL,
    CASES_TOTAL_PER_100000,
    DEATHS_TOTAL_PER_100000
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.WHO_TIMESERIES
WHERE COUNTRY_REGION = 'United States'
AND DATE >= DATEADD(months, -1, CURRENT_DATE())
ORDER BY DATE;
```

### Cross-Table Comparison Query
This example shows how to compare case reporting between different global data sources:
```sql
WITH latest_data AS (
    SELECT 
        DATE::DATE as report_date,
        'WHO' as source,
        COUNTRY_REGION,
        CASES_TOTAL as total_cases,
        DEATHS_TOTAL as total_deaths
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.WHO_TIMESERIES
    WHERE DATE = (SELECT MAX(DATE) FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.WHO_TIMESERIES)
    
    UNION ALL
    
    SELECT 
        DATE,
        'JHU' as source,
        COUNTRY_REGION,
        CASES,
        0 as total_deaths
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.JHU_COVID_19
    WHERE DATE = (SELECT MAX(DATE) FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.JHU_COVID_19)
    AND CASE_TYPE = 'Confirmed'
    
    UNION ALL
    
    SELECT 
        DATE,
        'ECDC' as source,
        COUNTRY_REGION,
        CASES,
        DEATHS
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.ECDC_GLOBAL
    WHERE DATE = (SELECT MAX(DATE) FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.ECDC_GLOBAL)
)
SELECT 
    COUNTRY_REGION,
    MAX(CASE WHEN source = 'WHO' THEN total_cases END) as WHO_cases,
    MAX(CASE WHEN source = 'JHU' THEN total_cases END) as JHU_cases,
    MAX(CASE WHEN source = 'ECDC' THEN total_cases END) as ECDC_cases
FROM latest_data
GROUP BY COUNTRY_REGION
HAVING WHO_cases IS NOT NULL 
    AND JHU_cases IS NOT NULL 
    AND ECDC_cases IS NOT NULL
ORDER BY WHO_cases DESC
LIMIT 10;
```

## US-Specific Data

This section covers detailed COVID-19 data specific to the United States from various authoritative sources.

### NYT_US_COVID19
**Description**: New York Times county-level US COVID-19 cases and deaths data, providing detailed tracking of the pandemic's spread across US counties and states.

**Columns**:
- `DATE`: Date of the record
- `COUNTY`: County name
- `STATE`: State name
- `FIPS`: Federal Information Processing Standard county code
- `CASES`: Cumulative number of cases
- `DEATHS`: Cumulative number of deaths
- `ISO3166_1`: Country code (US)
- `ISO3166_2`: State code
- `CASES_SINCE_PREV_DAY`: New cases since previous day
- `DEATHS_SINCE_PREV_DAY`: New deaths since previous day
- `LAST_UPDATE_DATE`: Timestamp of last update
- `LAST_REPORTED_FLAG`: Boolean indicating if this is the most recent report

**Sample Query**:
```sql
SELECT 
    DATE,
    STATE,
    COUNTY,
    CASES,
    DEATHS,
    CASES_SINCE_PREV_DAY,
    DEATHS_SINCE_PREV_DAY
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.NYT_US_COVID19
WHERE DATE >= DATEADD(days, -30, CURRENT_DATE())
AND STATE = 'New York'
ORDER BY DATE DESC, CASES DESC;
```

### CDC_TESTING
**Description**: Centers for Disease Control and Prevention's COVID-19 testing data by state, tracking positive, negative, and inconclusive test results.

**Columns**:
- `ISO3166_1`: Country code (US)
- `ISO3166_2`: State code
- `DATE`: Date of the testing data
- `POSITIVE`: Number of positive tests
- `NEGATIVE`: Number of negative tests
- `INCONCLUSIVE`: Number of inconclusive tests

**Sample Query**:
```sql
SELECT 
    DATE,
    ISO3166_2 as STATE,
    POSITIVE,
    NEGATIVE,
    INCONCLUSIVE,
    (POSITIVE + NEGATIVE + COALESCE(INCONCLUSIVE, 0)) as TOTAL_TESTS,
    ROUND(POSITIVE::FLOAT / NULLIF(POSITIVE + NEGATIVE + COALESCE(INCONCLUSIVE, 0), 0) * 100, 2) as POSITIVITY_RATE
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.CDC_TESTING
WHERE DATE >= DATEADD(days, -14, CURRENT_DATE())
ORDER BY DATE DESC, POSITIVITY_RATE DESC;
```

### CDC_INPATIENT_BEDS_COVID_19
**Description**: CDC's hospital capacity and COVID-19 patient data, tracking inpatient bed utilization and availability across US states.

**Columns**:
- `STATE`: State abbreviation
- `DATE`: Date of the report
- `INPATIENT_BEDS_OCCUPIED`: Number of inpatient beds occupied
- `INPATIENT_BEDS_LOWER_BOUND`: Lower bound of confidence interval
- `INPATIENT_BEDS_UPPER_BOUND`: Upper bound of confidence interval
- `INPATIENT_BEDS_IN_USE_PCT`: Percentage of inpatient beds in use
- `TOTAL_INPATIENT_BEDS`: Total number of inpatient beds
- `ISO3166_1`: Country code (US)
- `ISO3166_2`: State code
- `LAST_REPORTED_FLAG`: Boolean indicating if this is the most recent report

**Sample Query**:
```sql
SELECT 
    DATE,
    STATE,
    TOTAL_INPATIENT_BEDS,
    INPATIENT_BEDS_OCCUPIED,
    INPATIENT_BEDS_IN_USE_PCT,
    ROUND((INPATIENT_BEDS_OCCUPIED / NULLIF(TOTAL_INPATIENT_BEDS, 0)) * 100, 2) as CALCULATED_OCCUPANCY_RATE
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.CDC_INPATIENT_BEDS_COVID_19
WHERE DATE >= DATEADD(days, -7, CURRENT_DATE())
ORDER BY DATE DESC, INPATIENT_BEDS_IN_USE_PCT DESC;
```

### KFF_US_STATE_MITIGATIONS
**Description**: Kaiser Family Foundation's comprehensive tracking of state-level COVID-19 policy responses and mitigation measures.

**Columns**:
- `COUNTRY_REGION`: Country (United States)
- `PROVINCE_STATE`: State name
- `STATUS_OF_REOPENING`: Current reopening status
- `STAY_AT_HOME_ORDER`: Status of stay-at-home orders
- `MANDATORY_QUARANTINE_FOR_TRAVELERS`: Travel quarantine requirements
- `NON_ESSENTIAL_BUSINESS_CLOSURES`: Status of business closures
- `LARGE_GATHERINGS_BAN`: Restrictions on gathering sizes
- `RESTAURANT_LIMITS`: Restaurant operating restrictions
- `BAR_CLOSURES`: Bar operating restrictions
- `FACE_COVERING_REQUIREMENT`: Mask mandate status
- `PRIMARY_ELECTION_POSTPONEMENT`: Election changes
- `EMERGENCY_DECLARATION`: Emergency declaration status
- `LAST_UPDATED_DATE`: Timestamp of last update

**Sample Query**:
```sql
SELECT 
    PROVINCE_STATE,
    STATUS_OF_REOPENING,
    STAY_AT_HOME_ORDER,
    FACE_COVERING_REQUIREMENT,
    RESTAURANT_LIMITS,
    BAR_CLOSURES,
    LARGE_GATHERINGS_BAN
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.KFF_US_STATE_MITIGATIONS
WHERE LAST_UPDATED_DATE = (
    SELECT MAX(LAST_UPDATED_DATE) 
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.KFF_US_STATE_MITIGATIONS
)
ORDER BY PROVINCE_STATE;
```

### Cross-Table Analysis Example
This query combines NYT case data with KFF mitigation measures to analyze the relationship between policy decisions and case counts:
```sql
WITH state_cases AS (
    SELECT 
        DATE,
        STATE,
        SUM(CASES_SINCE_PREV_DAY) as NEW_CASES,
        SUM(DEATHS_SINCE_PREV_DAY) as NEW_DEATHS
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.NYT_US_COVID19
    WHERE DATE >= DATEADD(days, -30, CURRENT_DATE())
    GROUP BY DATE, STATE
)
SELECT 
    c.DATE,
    c.STATE,
    c.NEW_CASES,
    c.NEW_DEATHS,
    m.STATUS_OF_REOPENING,
    m.FACE_COVERING_REQUIREMENT,
    m.LARGE_GATHERINGS_BAN
FROM state_cases c
JOIN COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.KFF_US_STATE_MITIGATIONS m
    ON c.STATE = m.PROVINCE_STATE
WHERE c.NEW_CASES > 0
ORDER BY c.NEW_CASES DESC
LIMIT 20;
```

## Country-Specific Data

This section documents the tables containing detailed COVID-19 data for specific countries.

### Italy Data (PCM_DPS_COVID19)

**Description**: Detailed Italian case statistics and summary data from the Presidenza del Consiglio dei Ministri Dipartimento della Protezione Civile.

**Columns**:
- `CASES`: Number (Case count in geography and case type)
- `DIFFERENCE`: Number (Change in case count since previous report)
- `COUNTRY_REGION`: Text (ISO-3166-1 entity name)
- `ISO3166_1`: Text (ISO-3166-1 code for geography)
- `PROVINCE_STATE`: Text (ISO-3166-2 entity name)
- `CASE_TYPE`: Text (Case type)
- `LONG`: Float (Indicative longitude of geography centroid)
- `LAT`: Float (Indicative latitude of geography centroid)
- `DATE`: Date (Date of data point)
- `LAST_UPDATED_DATE`: Timestamp (UTC timestamp of last update)
- `ISO3166_2`: Text (ISO-3166-2 code for geography)
- `LAST_REPORTED_FLAG`: Boolean (New data in last import)

**Sample Query**:
```sql
SELECT 
    DATE,
    PROVINCE_STATE,
    CASE_TYPE,
    CASES,
    DIFFERENCE
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.PCM_DPS_COVID19
WHERE COUNTRY_REGION = 'Italy'
    AND DATE >= DATEADD(day, -30, CURRENT_DATE())
    AND CASE_TYPE = 'Confirmed'
ORDER BY DATE DESC, PROVINCE_STATE;
```

### German Data (RKI_GER_COVID19_DASHBOARD)

**Description**: Detailed district (Kreis) level data for Germany from the Robert Koch Institut.

**Columns**:
- `DISTRICT_ID`: Text (District identifier)
- `STATE_ID`: Text (Federal subject/state identifier)
- `COUNTY`: Text (ISO-3166-3 entity name)
- `DISTRICT_TYPE`: Text (ISO-3166-3 entity type)
- `STATE`: Text (ISO-3166-2 entity name)
- `CASES`: Number (Number of cases)
- `DEATHS`: Number (Number of deaths)
- `CASES_PER_100K`: Float (Cases per 100,000 population)
- `CASES7_PER_100K`: Float (7-day incidence per 100,000)
- `CASES_PER_POPULATION`: Float (Cases per population)
- `DEATH_RATE`: Float (Case-fatality ratio)
- `POPULATION`: Number (Population of district)
- `LAST_UPDATE`: Timestamp (Last update timestamp)
- `LAST_UPDATE_DATE`: Timestamp
- `ISO3166_1`: Text (Country code)
- `ISO3166_2`: Text (State code)
- `LAST_REPORTED_FLAG`: Boolean

**Sample Query**:
```sql
SELECT 
    STATE,
    COUNTY,
    CASES,
    DEATHS,
    CASES_PER_100K,
    DEATH_RATE,
    LAST_UPDATE_DATE
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.RKI_GER_COVID19_DASHBOARD
WHERE LAST_REPORTED_FLAG = TRUE
ORDER BY CASES_PER_100K DESC;
```

### Canadian Data (VH_CAN_DETAILED)

**Description**: COVID-19 cases and deaths data at the province level in Canada.

**Sample Query**:
```sql
SELECT 
    PROVINCE_STATE,
    DATE,
    CASE_TYPE,
    CASES,
    DIFFERENCE
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.VH_CAN_DETAILED
WHERE DATE >= DATEADD(day, -14, CURRENT_DATE())
ORDER BY DATE DESC, PROVINCE_STATE;
```

### Belgian Data (SCS_BE_DETAILED_*)

Belgium provides detailed data through four related tables:

1. **SCS_BE_DETAILED_HOSPITALISATIONS**
   - Description: Hospitalizations and details on patient disposition
   - Contains daily hospital capacity and COVID-19 patient data

2. **SCS_BE_DETAILED_MORTALITY**
   - Description: Detailed data on mortality
   - Tracks COVID-19 related deaths and mortality statistics

3. **SCS_BE_DETAILED_PROVINCE_CASE_COUNTS**
   - Description: Detailed data on case counts in Belgium and Luxembourg
   - Provincial-level case tracking

4. **SCS_BE_DETAILED_TESTS**
   - Description: Day-to-day time series on tests performed
   - Testing data and positivity rates

**Sample Query** (Combining Belgian hospitalization and case data):
```sql
SELECT 
    h.DATE,
    h.PROVINCE,
    c.CASES as NEW_CASES,
    h.NEW_IN as NEW_HOSPITALIZATIONS,
    h.TOTAL_IN as TOTAL_HOSPITALIZED,
    h.TOTAL_ICU as ICU_PATIENTS
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.SCS_BE_DETAILED_HOSPITALISATIONS h
JOIN COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.SCS_BE_DETAILED_PROVINCE_CASE_COUNTS c
    ON h.DATE = c.DATE 
    AND h.PROVINCE = c.PROVINCE
WHERE h.DATE >= DATEADD(day, -30, CURRENT_DATE())
ORDER BY h.DATE DESC, h.PROVINCE;
```

### Cross-Country Comparison Query

This sample query compares case rates across different country-specific data sources:

```sql
WITH CountryData AS (
    -- Italian Data
    SELECT 
        DATE,
        'Italy' as COUNTRY,
        SUM(CASES) as TOTAL_CASES
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.PCM_DPS_COVID19
    WHERE CASE_TYPE = 'Confirmed'
    GROUP BY DATE

    UNION ALL

    -- German Data
    SELECT 
        LAST_UPDATE_DATE as DATE,
        'Germany' as COUNTRY,
        SUM(CASES) as TOTAL_CASES
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.RKI_GER_COVID19_DASHBOARD
    GROUP BY LAST_UPDATE_DATE
)
SELECT 
    DATE,
    COUNTRY,
    TOTAL_CASES,
    TOTAL_CASES - LAG(TOTAL_CASES) OVER (PARTITION BY COUNTRY ORDER BY DATE) as DAILY_NEW_CASES
FROM CountryData
WHERE DATE >= DATEADD(day, -30, CURRENT_DATE())
ORDER BY COUNTRY, DATE DESC;
```

## Mobility and Policy Data

This section covers data related to population mobility patterns and policy responses during the COVID-19 pandemic.

### GOOG_GLOBAL_MOBILITY_REPORT
**Description**: Google's Community Mobility Reports showing how visits and length of stay at different places change compared to baseline days before the pandemic.

**Columns**:
- `COUNTRY_REGION`: Name of the country
- `PROVINCE_STATE`: Name of the state/province (if applicable)
- `ISO_3166_1`: Country code
- `ISO_3166_2`: State/province code (if applicable)
- `DATE`: Date of the mobility data
- `GROCERY_AND_PHARMACY_CHANGE_PERC`: Percentage change in visits to grocery and pharmacy locations
- `PARKS_CHANGE_PERC`: Percentage change in visits to parks
- `RESIDENTIAL_CHANGE_PERC`: Percentage change in time spent at residential locations
- `RETAIL_AND_RECREATION_CHANGE_PERC`: Percentage change in visits to retail and recreation locations
- `TRANSIT_STATIONS_CHANGE_PERC`: Percentage change in visits to transit stations
- `WORKPLACES_CHANGE_PERC`: Percentage change in visits to workplaces
- `LAST_UPDATE_DATE`: Timestamp of last update
- `LAST_REPORTED_FLAG`: Boolean indicating if this is the most recent report

**Sample Query**:
```sql
SELECT 
    DATE,
    COUNTRY_REGION,
    RETAIL_AND_RECREATION_CHANGE_PERC,
    GROCERY_AND_PHARMACY_CHANGE_PERC,
    PARKS_CHANGE_PERC,
    TRANSIT_STATIONS_CHANGE_PERC,
    WORKPLACES_CHANGE_PERC,
    RESIDENTIAL_CHANGE_PERC
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.GOOG_GLOBAL_MOBILITY_REPORT
WHERE DATE >= DATEADD(days, -30, CURRENT_DATE())
AND COUNTRY_REGION = 'United States'
ORDER BY DATE DESC;
```

### APPLE_MOBILITY
**Description**: Apple's Mobility Trends Reports showing relative volume of direction requests per country/region, sub-region, or city compared to baseline volume on January 13, 2020.

**Columns**:
- `COUNTRY_REGION`: Name of the country
- `PROVINCE_STATE`: Name of the state/province (if applicable)
- `DATE`: Date of the mobility data
- `TRANSPORTATION_TYPE`: Type of transportation (driving, walking, or transit)
- `DIFFERENCE`: Percentage difference from baseline
- `ISO3166_1`: Country code
- `ISO3166_2`: State/province code (if applicable)
- `LAST_UPDATED_DATE`: Timestamp of last update
- `LAST_REPORTED_FLAG`: Boolean indicating if this is the most recent report

**Sample Query**:
```sql
SELECT 
    DATE,
    COUNTRY_REGION,
    TRANSPORTATION_TYPE,
    DIFFERENCE
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.APPLE_MOBILITY
WHERE DATE >= DATEADD(days, -14, CURRENT_DATE())
AND COUNTRY_REGION = 'United States'
ORDER BY DATE DESC, TRANSPORTATION_TYPE;
```

### HDX_ACAPS
**Description**: ACAPS COVID-19 Government Measures Dataset, tracking governments' responses to the pandemic across different categories.

**Columns**:
- `COUNTRY_STATE`: Country name
- `REGION`: Geographic region
- `CATEGORY`: Type of measure (e.g., Public health measures, Social distancing)
- `MEASURE`: Specific measure implemented
- `TARGETED_POP_GROUP`: Target population for the measure
- `COMMENTS`: Detailed description of the measure
- `DATE_IMPLEMENTED`: Date when measure was implemented
- `SOURCE`: Information source
- `SOURCE_TYPE`: Type of source (e.g., Government, Media)
- `LINK`: URL to source document
- `ENTRY_DATE`: Date of data entry
- `ISO3166_1`: Country code
- `LAST_UPDATED_DATE`: Timestamp of last update
- `LOG_TYPE`: Type of log entry

**Sample Query**:
```sql
SELECT 
    COUNTRY_STATE,
    CATEGORY,
    MEASURE,
    DATE_IMPLEMENTED,
    COMMENTS
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.HDX_ACAPS
WHERE DATE_IMPLEMENTED >= DATEADD(months, -1, CURRENT_DATE())
ORDER BY DATE_IMPLEMENTED DESC, COUNTRY_STATE;
```

### HUM_RESTRICTIONS_COUNTRY
**Description**: Humanitarian Data Exchange (HDX) dataset tracking COVID-19 related travel restrictions and exceptions by country.

**Columns**:
- `COUNTRY`: Country name
- `ISO3166_1`: Country code
- `LONG`: Longitude coordinate
- `LAT`: Latitude coordinate
- `PUBLISHED`: Publication date
- `SOURCES`: Source information and links
- `RESTRICTION_TEXT`: Detailed text of restrictions
- `INFO_DATE`: Date of information
- `QUARANTINE_TEXT`: Quarantine requirements text
- `LAST_UPDATE_DATE`: Timestamp of last update

**Sample Query**:
```sql
SELECT 
    COUNTRY,
    PUBLISHED,
    INFO_DATE,
    SUBSTRING(RESTRICTION_TEXT, 1, 200) as RESTRICTION_SUMMARY,
    SUBSTRING(QUARANTINE_TEXT, 1, 200) as QUARANTINE_SUMMARY
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.HUM_RESTRICTIONS_COUNTRY
WHERE PUBLISHED >= DATEADD(months, -1, CURRENT_DATE())
ORDER BY PUBLISHED DESC, COUNTRY;
```

### Cross-Table Analysis Example
This query combines mobility data with policy measures to analyze the relationship between government actions and population movement:
```sql
WITH mobility_avg AS (
    SELECT 
        g.COUNTRY_REGION,
        g.DATE,
        AVG(g.RETAIL_AND_RECREATION_CHANGE_PERC) as retail_change,
        AVG(g.WORKPLACES_CHANGE_PERC) as workplace_change,
        AVG(g.RESIDENTIAL_CHANGE_PERC) as residential_change
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.GOOG_GLOBAL_MOBILITY_REPORT g
    WHERE DATE >= DATEADD(months, -1, CURRENT_DATE())
    GROUP BY g.COUNTRY_REGION, g.DATE
)
SELECT 
    m.COUNTRY_REGION,
    m.DATE,
    m.retail_change,
    m.workplace_change,
    m.residential_change,
    h.MEASURE as policy_measure,
    h.CATEGORY as measure_category
FROM mobility_avg m
LEFT JOIN COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.HDX_ACAPS h
    ON m.COUNTRY_REGION = h.COUNTRY_STATE
    AND m.DATE >= h.DATE_IMPLEMENTED
    AND m.DATE <= DATEADD(days, 14, h.DATE_IMPLEMENTED)
WHERE h.CATEGORY IN ('Movement restrictions', 'Social distancing')
ORDER BY m.DATE DESC, m.COUNTRY_REGION
LIMIT 100;

This section covers the following tables:
- GOOG_GLOBAL_MOBILITY_REPORT
- APPLE_MOBILITY
- HDX_ACAPS
- HUM_RESTRICTIONS_COUNTRY

Each table in this section provides different aspects of mobility and policy data:



## Vaccination Data

### OWID_VACCINATIONS
**Description**: Our World in Data's comprehensive COVID-19 vaccination dataset, providing detailed information about vaccination progress across countries, including total vaccinations, people vaccinated, and vaccination rates.

**Columns**:
- `DATE`: Date of the vaccination record
- `COUNTRY_REGION`: Name of the country/region
- `ISO3166_1`: Country code in ISO 3166-1 format
- `TOTAL_VACCINATIONS`: Total number of doses administered
- `PEOPLE_VACCINATED`: Total number of people who received at least one dose
- `PEOPLE_FULLY_VACCINATED`: Total number of people who received all doses prescribed by protocol
- `DAILY_VACCINATIONS_RAW`: Daily change in total vaccinations (raw)
- `DAILY_VACCINATIONS`: Smoothed daily change in total vaccinations
- `TOTAL_VACCINATIONS_PER_HUNDRED`: Total vaccinations per 100 people
- `PEOPLE_VACCINATED_PER_HUNDRED`: People vaccinated per 100 people
- `PEOPLE_FULLY_VACCINATED_PER_HUNDRED`: People fully vaccinated per 100 people
- `DAILY_VACCINATIONS_PER_MILLION`: Daily vaccinations per million people
- `VACCINES`: Types of vaccines being administered
- `LAST_OBSERVATION_DATE`: Date of the last observation
- `SOURCE_NAME`: Name of the data source
- `SOURCE_WEBSITE`: Website URL of the data source
- `LAST_UPDATE_DATE`: Timestamp of the last update
- `LAST_REPORTED_FLAG`: Boolean indicating if this is the most recent report

**Sample Queries**:

1. Latest vaccination rates by country:
```sql
SELECT 
    COUNTRY_REGION,
    TOTAL_VACCINATIONS,
    PEOPLE_VACCINATED,
    PEOPLE_FULLY_VACCINATED,
    TOTAL_VACCINATIONS_PER_HUNDRED,
    PEOPLE_FULLY_VACCINATED_PER_HUNDRED
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.OWID_VACCINATIONS
WHERE LAST_REPORTED_FLAG = TRUE
AND TOTAL_VACCINATIONS IS NOT NULL
ORDER BY TOTAL_VACCINATIONS_PER_HUNDRED DESC
LIMIT 20;
```

2. Daily vaccination trends for a specific country:
```sql
SELECT 
    DATE,
    DAILY_VACCINATIONS,
    DAILY_VACCINATIONS_PER_MILLION,
    VACCINES
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.OWID_VACCINATIONS
WHERE COUNTRY_REGION = 'United States'
AND DATE >= DATEADD(months, -1, CURRENT_DATE())
ORDER BY DATE DESC;
```

3. Vaccination progress comparison:
```sql
SELECT 
    COUNTRY_REGION,
    TOTAL_VACCINATIONS,
    PEOPLE_VACCINATED,
    PEOPLE_FULLY_VACCINATED,
    ROUND(PEOPLE_FULLY_VACCINATED::FLOAT / NULLIF(PEOPLE_VACCINATED, 0) * 100, 2) as COMPLETION_RATE
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.OWID_VACCINATIONS
WHERE LAST_REPORTED_FLAG = TRUE
AND PEOPLE_VACCINATED > 1000000
ORDER BY COMPLETION_RATE DESC;
```

This section covers the following table:
- OWID_VACCINATIONS

**Columns**:
- `LOCATION`: Country or region name
- `ISO_CODE`: ISO 3166-1 alpha-3 country code
- `DATE`: Date of the record
- `TOTAL_VACCINATIONS`: Total number of doses administered
- `PEOPLE_VACCINATED`: Total number of people who received at least one dose
- `PEOPLE_FULLY_VACCINATED`: Total number of people who received all doses prescribed by protocol
- `TOTAL_BOOSTERS`: Total number of booster doses administered
- `DAILY_VACCINATIONS_RAW`: Daily change in total vaccinations
- `DAILY_VACCINATIONS`: Smoothed daily change in total vaccinations
- `TOTAL_VACCINATIONS_PER_HUNDRED`: Total vaccinations per 100 people
- `PEOPLE_VACCINATED_PER_HUNDRED`: People vaccinated per 100 people
- `PEOPLE_FULLY_VACCINATED_PER_HUNDRED`: People fully vaccinated per 100 people
- `TOTAL_BOOSTERS_PER_HUNDRED`: Total booster doses per 100 people
- `DAILY_VACCINATIONS_PER_MILLION`: Daily vaccinations per 1,000,000 people
- `LAST_OBSERVATION_DATE`: Date of the last reported observation

**Sample Query**:
```sql
SELECT 
    LOCATION,
    DATE,
    TOTAL_VACCINATIONS,
    PEOPLE_VACCINATED,
    PEOPLE_FULLY_VACCINATED,
    TOTAL_BOOSTERS,
    PEOPLE_FULLY_VACCINATED_PER_HUNDRED,
    DAILY_VACCINATIONS_PER_MILLION
FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.OWID_VACCINATIONS
WHERE DATE >= DATEADD(days, -30, CURRENT_DATE())
AND LOCATION IN ('United States', 'United Kingdom', 'Germany', 'France', 'Italy')
ORDER BY DATE DESC, PEOPLE_FULLY_VACCINATED_PER_HUNDRED DESC;
```

## Cross-Reference Examples

This section demonstrates how to combine data from different categories of tables to perform more complex analyses.

### Cases and Mobility Analysis
This query combines JHU case data with Google mobility data to analyze the relationship between COVID-19 cases and population movement patterns:
```sql
WITH mobility_changes AS (
    SELECT 
        DATE,
        COUNTRY_REGION,
        retail_and_recreation_percent_change_from_baseline,
        grocery_and_pharmacy_percent_change_from_baseline,
        parks_percent_change_from_baseline,
        transit_stations_percent_change_from_baseline,
        workplaces_percent_change_from_baseline,
        residential_percent_change_from_baseline
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.GOOG_GLOBAL_MOBILITY_REPORT
    WHERE DATE >= DATEADD(months, -1, CURRENT_DATE())
),
case_data AS (
    SELECT 
        DATE,
        COUNTRY_REGION,
        SUM(CASES) as total_cases,
        SUM(DIFFERENCE) as new_cases
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.JHU_COVID_19
    WHERE CASE_TYPE = 'Confirmed'
    AND DATE >= DATEADD(months, -1, CURRENT_DATE())
    GROUP BY DATE, COUNTRY_REGION
)
SELECT 
    c.DATE,
    c.COUNTRY_REGION,
    c.new_cases,
    m.retail_and_recreation_percent_change_from_baseline as retail_mobility,
    m.workplaces_percent_change_from_baseline as workplace_mobility,
    m.residential_percent_change_from_baseline as residential_mobility
FROM case_data c
JOIN mobility_changes m 
    ON c.COUNTRY_REGION = m.COUNTRY_REGION 
    AND c.DATE = m.DATE
WHERE c.new_cases > 0
ORDER BY c.DATE DESC, c.new_cases DESC
LIMIT 100;
```

### Vaccination Progress and Policy Measures
This query combines vaccination data with policy measures to analyze the relationship between vaccination rates and policy changes:
```sql
WITH vaccination_progress AS (
    SELECT 
        DATE,
        COUNTRY,
        TOTAL_VACCINATIONS,
        PEOPLE_VACCINATED,
        PEOPLE_FULLY_VACCINATED,
        TOTAL_VACCINATIONS_PER_HUNDRED,
        PEOPLE_VACCINATED_PER_HUNDRED
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.OWID_VACCINATIONS
    WHERE DATE >= DATEADD(months, -3, CURRENT_DATE())
),
policy_measures AS (
    SELECT 
        DATE,
        COUNTRY,
        MEASURE,
        TARGETED_POPULATION,
        COMMENTS
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.HDX_ACAPS
    WHERE DATE >= DATEADD(months, -3, CURRENT_DATE())
)
SELECT 
    v.DATE,
    v.COUNTRY,
    v.TOTAL_VACCINATIONS_PER_HUNDRED as vaccination_rate,
    v.PEOPLE_FULLY_VACCINATED,
    p.MEASURE as policy_measure,
    p.TARGETED_POPULATION,
    p.COMMENTS
FROM vaccination_progress v
LEFT JOIN policy_measures p 
    ON v.COUNTRY = p.COUNTRY 
    AND v.DATE = p.DATE
WHERE v.TOTAL_VACCINATIONS_PER_HUNDRED IS NOT NULL
ORDER BY v.DATE DESC, v.TOTAL_VACCINATIONS_PER_HUNDRED DESC;
```

### Hospital Capacity and Case Correlation (US)
This query combines CDC hospital capacity data with NYT case data to analyze healthcare system stress:
```sql
WITH hospital_metrics AS (
    SELECT 
        DATE,
        STATE,
        TOTAL_INPATIENT_BEDS,
        INPATIENT_BEDS_OCCUPIED,
        INPATIENT_BEDS_IN_USE_PCT
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.CDC_INPATIENT_BEDS_COVID_19
    WHERE DATE >= DATEADD(days, -30, CURRENT_DATE())
),
case_metrics AS (
    SELECT 
        DATE,
        STATE,
        SUM(CASES_SINCE_PREV_DAY) as new_cases,
        SUM(DEATHS_SINCE_PREV_DAY) as new_deaths
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.NYT_US_COVID19
    WHERE DATE >= DATEADD(days, -30, CURRENT_DATE())
    GROUP BY DATE, STATE
)
SELECT 
    h.DATE,
    h.STATE,
    c.new_cases,
    c.new_deaths,
    h.TOTAL_INPATIENT_BEDS,
    h.INPATIENT_BEDS_OCCUPIED,
    h.INPATIENT_BEDS_IN_USE_PCT,
    ROUND((c.new_cases::FLOAT / NULLIF(h.TOTAL_INPATIENT_BEDS, 0)) * 100, 2) as new_cases_per_100_beds
FROM hospital_metrics h
JOIN case_metrics c 
    ON h.STATE = c.STATE 
    AND h.DATE = c.DATE
WHERE h.INPATIENT_BEDS_IN_USE_PCT IS NOT NULL
ORDER BY h.DATE DESC, new_cases_per_100_beds DESC;
```

### Global Data Source Comparison
This query compares COVID-19 statistics across different global data sources (WHO, JHU, and ECDC) and includes mobility data:
```sql
WITH global_cases AS (
    -- WHO Data
    SELECT 
        DATE::DATE as report_date,
        'WHO' as source,
        COUNTRY_REGION,
        CASES_TOTAL as total_cases,
        DEATHS_TOTAL as total_deaths
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.WHO_TIMESERIES
    WHERE DATE = (SELECT MAX(DATE) FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.WHO_TIMESERIES)
    
    UNION ALL
    
    -- JHU Data
    SELECT 
        DATE,
        'JHU' as source,
        COUNTRY_REGION,
        SUM(CASES) as total_cases,
        0 as total_deaths
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.JHU_COVID_19
    WHERE DATE = (SELECT MAX(DATE) FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.JHU_COVID_19)
    AND CASE_TYPE = 'Confirmed'
    GROUP BY DATE, COUNTRY_REGION
    
    UNION ALL
    
    -- ECDC Data
    SELECT 
        DATE,
        'ECDC' as source,
        COUNTRY_REGION,
        CASES as total_cases,
        DEATHS as total_deaths
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.ECDC_GLOBAL
    WHERE DATE = (SELECT MAX(DATE) FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.ECDC_GLOBAL)
),
mobility_latest AS (
    SELECT 
        COUNTRY_REGION,
        AVG(workplaces_percent_change_from_baseline) as avg_workplace_mobility,
        AVG(residential_percent_change_from_baseline) as avg_residential_mobility
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.GOOG_GLOBAL_MOBILITY_REPORT
    WHERE DATE >= DATEADD(days, -7, CURRENT_DATE())
    GROUP BY COUNTRY_REGION
)
SELECT 
    g.COUNTRY_REGION,
    MAX(CASE WHEN g.source = 'WHO' THEN g.total_cases END) as WHO_cases,
    MAX(CASE WHEN g.source = 'JHU' THEN g.total_cases END) as JHU_cases,
    MAX(CASE WHEN g.source = 'ECDC' THEN g.total_cases END) as ECDC_cases,
    m.avg_workplace_mobility,
    m.avg_residential_mobility
FROM global_cases g
LEFT JOIN mobility_latest m ON g.COUNTRY_REGION = m.COUNTRY_REGION
GROUP BY g.COUNTRY_REGION, m.avg_workplace_mobility, m.avg_residential_mobility
HAVING WHO_cases IS NOT NULL 
    AND JHU_cases IS NOT NULL 
    AND ECDC_cases IS NOT NULL
ORDER BY WHO_cases DESC
LIMIT 20;
```

This section provides comprehensive examples of joining different categories of tables to perform complex analyses.

### Case Data and Mobility Analysis
This query combines JHU case data with Google mobility data to analyze the relationship between COVID-19 cases and population movement patterns:

```sql
WITH case_data AS (
    SELECT 
        DATE,
        COUNTRY_REGION,
        SUM(CASES) as total_cases,
        SUM(DIFFERENCE) as new_cases
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.JHU_COVID_19
    WHERE CASE_TYPE = 'Confirmed'
    AND DATE >= DATEADD(days, -30, CURRENT_DATE())
    GROUP BY DATE, COUNTRY_REGION
)
SELECT 
    c.DATE,
    c.COUNTRY_REGION,
    c.new_cases,
    g.retail_and_recreation_percent_change_from_baseline,
    g.grocery_and_pharmacy_percent_change_from_baseline,
    g.parks_percent_change_from_baseline,
    g.transit_stations_percent_change_from_baseline,
    g.workplaces_percent_change_from_baseline,
    g.residential_percent_change_from_baseline
FROM case_data c
JOIN COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.GOOG_GLOBAL_MOBILITY_REPORT g
    ON c.COUNTRY_REGION = g.country_region 
    AND c.DATE = g.date
WHERE c.new_cases > 0
ORDER BY c.new_cases DESC
LIMIT 20;
```

### Vaccination Progress and Policy Measures
This query analyzes vaccination rates alongside policy changes to understand the impact of policies on vaccination progress:

```sql
WITH vaccination_data AS (
    SELECT 
        location as country,
        date,
        total_vaccinations,
        people_vaccinated,
        people_fully_vaccinated,
        total_boosters,
        daily_vaccinations,
        daily_vaccinations_per_million
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.OWID_VACCINATIONS
    WHERE date >= DATEADD(days, -90, CURRENT_DATE())
),
policy_data AS (
    SELECT 
        country,
        date,
        stringency_index,
        population
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.HDX_ACAPS
    WHERE date >= DATEADD(days, -90, CURRENT_DATE())
)
SELECT 
    v.date,
    v.country,
    v.daily_vaccinations,
    v.daily_vaccinations_per_million,
    p.stringency_index,
    ROUND(v.people_fully_vaccinated / NULLIF(p.population, 0) * 100, 2) as vaccination_rate_pct
FROM vaccination_data v
JOIN policy_data p 
    ON v.country = p.country 
    AND v.date = p.date
WHERE v.daily_vaccinations > 0
ORDER BY v.date DESC, vaccination_rate_pct DESC;
```

### Hospital Capacity and Case Correlation
This query examines the relationship between US COVID-19 cases and hospital capacity:

```sql
WITH state_cases AS (
    SELECT 
        DATE,
        STATE,
        SUM(CASES_SINCE_PREV_DAY) as new_cases,
        SUM(CASES) as total_cases
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.NYT_US_COVID19
    WHERE DATE >= DATEADD(days, -30, CURRENT_DATE())
    GROUP BY DATE, STATE
)
SELECT 
    c.DATE,
    c.STATE,
    c.new_cases,
    h.TOTAL_INPATIENT_BEDS,
    h.INPATIENT_BEDS_OCCUPIED,
    h.INPATIENT_BEDS_IN_USE_PCT,
    ROUND(c.new_cases / NULLIF(h.TOTAL_INPATIENT_BEDS, 0) * 100, 2) as new_cases_per_bed_pct
FROM state_cases c
JOIN COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.CDC_INPATIENT_BEDS_COVID_19 h
    ON c.STATE = h.STATE 
    AND c.DATE = h.DATE
WHERE c.new_cases > 0
ORDER BY new_cases_per_bed_pct DESC
LIMIT 20;
```