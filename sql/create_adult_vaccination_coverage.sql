CREATE OR REPLACE TABLE ADULT_VACCINATION_COVERAGE (
    VACCINE VARCHAR(255) COMMENT 'Type of vaccine administered',
    DOSE VARCHAR(50) COMMENT 'Specific dose type or schedule of the vaccine',
    GEOGRAPHY_TYPE VARCHAR(100) COMMENT 'Level of geographic aggregation (e.g., States/Local Areas)',
    GEOGRAPHY VARCHAR(100) COMMENT 'Name of the geographic area',
    FIPS VARCHAR(10) COMMENT 'Federal Information Processing Standards (FIPS) code for geographic identification',
    SURVEY_YEAR NUMBER COMMENT 'Year the survey was conducted',
    DIMENSION_TYPE VARCHAR(100) COMMENT 'Demographic or categorical dimension (e.g., age group)',
    DIMENSION VARCHAR(255) COMMENT 'Specific category within the dimension type',
    ESTIMATE_PERCENTAGE FLOAT COMMENT 'Estimated vaccination coverage percentage',
    CONFIDENCE_INTERVAL VARCHAR(50) COMMENT '95% Confidence Interval for the estimate',
    SAMPLE_SIZE NUMBER COMMENT 'Number of individuals in the sample'
) COMMENT = 'CDC Vaccination Coverage among Adults (18+ Years) tracking various vaccines across different geographic areas, demographics, and time periods';