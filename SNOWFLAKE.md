# SNOWFLAKE Database Documentation

The SNOWFLAKE database is a system database that contains metadata about your Snowflake account and objects. It primarily consists of system views in the INFORMATION_SCHEMA that provide information about database objects, privileges, and system state.

## Schemas

The database contains the following schemas:
- ALERT
- CORE
- CORTEX
- IMAGES
- INFORMATION_SCHEMA
- LOCAL
- ML
- NOTIFICATION

The most important schema is INFORMATION_SCHEMA, which contains system views for metadata querying.

## INFORMATION_SCHEMA Views

### Key System Views

1. **TABLES**
   - Description: Lists all tables defined in this database that are accessible to the current user's role
   - Sample Query:
   ```sql
   SELECT TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE, COMMENT
   FROM SNOWFLAKE.INFORMATION_SCHEMA.TABLES
   WHERE TABLE_SCHEMA NOT IN ('INFORMATION_SCHEMA')
   ORDER BY TABLE_SCHEMA, TABLE_NAME;
   ```

2. **COLUMNS**
   - Description: Lists all columns of tables defined in this database that are accessible to the current user's role
   - Sample Query:
   ```sql
   SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COMMENT
   FROM SNOWFLAKE.INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = '<your_schema>'
   ORDER BY TABLE_NAME, ORDINAL_POSITION;
   ```

3. **VIEWS**
   - Description: Lists all views defined in this database that are accessible to the current user's role
   - Sample Query:
   ```sql
   SELECT TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME, VIEW_DEFINITION
   FROM SNOWFLAKE.INFORMATION_SCHEMA.VIEWS
   WHERE TABLE_SCHEMA NOT IN ('INFORMATION_SCHEMA');
   ```

### Security and Access Control Views

1. **OBJECT_PRIVILEGES**
   - Description: Shows privileges on all objects defined in this database
   - Sample Query:
   ```sql
   SELECT GRANTEE, GRANTOR, OBJECT_CATALOG, OBJECT_SCHEMA, OBJECT_NAME, PRIVILEGE_TYPE
   FROM SNOWFLAKE.INFORMATION_SCHEMA.OBJECT_PRIVILEGES
   WHERE OBJECT_SCHEMA NOT IN ('INFORMATION_SCHEMA');
   ```

2. **ENABLED_ROLES**
   - Description: Shows roles that are enabled for the current user
   - Sample Query:
   ```sql
   SELECT *
   FROM SNOWFLAKE.INFORMATION_SCHEMA.ENABLED_ROLES;
   ```

### Database Object Views

1. **FUNCTIONS**
   - Description: Lists user-defined functions in this database
   - Sample Query:
   ```sql
   SELECT FUNCTION_CATALOG, FUNCTION_SCHEMA, FUNCTION_NAME, DATA_TYPE
   FROM SNOWFLAKE.INFORMATION_SCHEMA.FUNCTIONS
   WHERE FUNCTION_SCHEMA NOT IN ('INFORMATION_SCHEMA');
   ```

2. **PROCEDURES**
   - Description: Lists stored procedures in this database
   - Sample Query:
   ```sql
   SELECT PROCEDURE_CATALOG, PROCEDURE_SCHEMA, PROCEDURE_NAME
   FROM SNOWFLAKE.INFORMATION_SCHEMA.PROCEDURES
   WHERE PROCEDURE_SCHEMA NOT IN ('INFORMATION_SCHEMA');
   ```

3. **STAGES**
   - Description: Lists stages in this database
   - Sample Query:
   ```sql
   SELECT STAGE_CATALOG, STAGE_SCHEMA, STAGE_NAME, STAGE_URL, STAGE_TYPE
   FROM SNOWFLAKE.INFORMATION_SCHEMA.STAGES
   WHERE STAGE_SCHEMA NOT IN ('INFORMATION_SCHEMA');
   ```

### Storage and Performance Views

1. **TABLE_STORAGE_METRICS**
   - Description: Provides storage metrics for all tables
   - Sample Query:
   ```sql
   SELECT TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME, 
          ACTIVE_BYTES, TIME_TRAVEL_BYTES, FAILSAFE_BYTES
   FROM SNOWFLAKE.INFORMATION_SCHEMA.TABLE_STORAGE_METRICS
   WHERE TABLE_SCHEMA NOT IN ('INFORMATION_SCHEMA')
   ORDER BY ACTIVE_BYTES DESC;
   ```

2. **LOAD_HISTORY**
   - Description: Shows history of data loading operations
   - Sample Query:
   ```sql
   SELECT TABLE_NAME, FILE_NAME, ROW_COUNT, ERROR_COUNT, STATUS
   FROM SNOWFLAKE.INFORMATION_SCHEMA.LOAD_HISTORY
   ORDER BY LAST_LOAD_TIME DESC;
   ```

## Usage Notes

1. The INFORMATION_SCHEMA views are essential for:
   - Database administration and monitoring
   - Security auditing
   - Object metadata querying
   - Storage and performance analysis

2. Best Practices:
   - Always filter out INFORMATION_SCHEMA when querying for user objects
   - Use these views for automated monitoring and reporting
   - Consider performance impact when querying large metadata sets