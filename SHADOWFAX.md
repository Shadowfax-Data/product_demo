# SHADOWFAX Database Documentation

## Overview
The SHADOWFAX database contains system views and tables for tracking query history and performance metrics. This database appears to be primarily used for monitoring and analyzing query execution within the Snowflake environment.

## Schemas

### PUBLIC Schema
The PUBLIC schema contains the following objects:

#### QUERY_HISTORY (View)
A system view that provides detailed information about query execution history and performance metrics.

##### Columns

| Column Name | Data Type | Nullable | Description |
|------------|-----------|----------|-------------|
| QUERY_ID | TEXT | YES | Unique identifier for each query |
| QUERY_TEXT | TEXT | YES | The actual SQL text of the query |
| DATABASE_ID | NUMBER | YES | Identifier of the database used |
| DATABASE_NAME | TEXT | YES | Name of the database used |
| SCHEMA_ID | NUMBER | YES | Identifier of the schema used |
| SCHEMA_NAME | TEXT | YES | Name of the schema used |
| QUERY_TYPE | TEXT | YES | Type of the query executed |
| SESSION_ID | NUMBER | YES | Identifier of the session |
| USER_NAME | TEXT | YES | Name of the user who executed the query |
| ROLE_NAME | TEXT | YES | Role used to execute the query |
| WAREHOUSE_ID | NUMBER | YES | Identifier of the warehouse used |
| WAREHOUSE_NAME | TEXT | YES | Name of the warehouse used |
| WAREHOUSE_SIZE | TEXT | YES | Size of the warehouse used |
| WAREHOUSE_TYPE | TEXT | YES | Type of the warehouse |
| START_TIME | TIMESTAMP_LTZ | YES | Query start timestamp |
| END_TIME | TIMESTAMP_LTZ | YES | Query end timestamp |
| TOTAL_ELAPSED_TIME | NUMBER | YES | Total time taken by the query |
| BYTES_SCANNED | NUMBER | NO | Amount of data scanned |
| ROWS_PRODUCED | NUMBER | YES | Number of rows returned by the query |
| COMPILATION_TIME | NUMBER | YES | Time spent in query compilation |
| EXECUTION_TIME | NUMBER | YES | Time spent in query execution |
| CREDITS_USED_CLOUD_SERVICES | FLOAT | NO | Credits consumed by cloud services |

##### Sample Queries

1. Query to analyze warehouse performance:
```sql
SELECT 
    WAREHOUSE_NAME,
    COUNT(*) as query_count,
    AVG(TOTAL_ELAPSED_TIME)/1000 as avg_execution_time_seconds,
    SUM(CREDITS_USED_CLOUD_SERVICES) as total_credits_used
FROM QUERY_HISTORY
WHERE START_TIME >= DATEADD(day, -7, CURRENT_TIMESTAMP())
GROUP BY WAREHOUSE_NAME
ORDER BY query_count DESC;
```

2. Query to find slow-running queries:
```sql
SELECT 
    QUERY_ID,
    QUERY_TEXT,
    USER_NAME,
    WAREHOUSE_NAME,
    TOTAL_ELAPSED_TIME/1000 as execution_time_seconds,
    BYTES_SCANNED/1024/1024/1024 as gb_scanned
FROM QUERY_HISTORY
WHERE START_TIME >= DATEADD(day, -1, CURRENT_TIMESTAMP())
    AND TOTAL_ELAPSED_TIME > 60000  -- queries taking more than 1 minute
ORDER BY TOTAL_ELAPSED_TIME DESC
LIMIT 10;
```

3. Query to analyze user activity:
```sql
SELECT 
    USER_NAME,
    COUNT(*) as query_count,
    COUNT(DISTINCT DATABASE_NAME) as databases_accessed,
    SUM(CREDITS_USED_CLOUD_SERVICES) as total_credits_used
FROM QUERY_HISTORY
WHERE START_TIME >= DATEADD(month, -1, CURRENT_TIMESTAMP())
GROUP BY USER_NAME
ORDER BY query_count DESC;
```

### DEV Schema
The DEV schema appears to be empty or may contain objects that are not accessible with the current privileges.

## Notes
- The database primarily serves monitoring and analytics purposes through the QUERY_HISTORY view
- The QUERY_HISTORY view is particularly useful for:
  - Performance monitoring and optimization
  - Resource usage tracking
  - User activity analysis
  - Query pattern analysis
- Access to the view's data may be limited based on the user's role and privileges