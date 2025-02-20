# SNOWFLAKE_SAMPLE_DATA Database Documentation

The SNOWFLAKE_SAMPLE_DATA database contains sample datasets provided by Snowflake for testing and demonstration purposes. It includes TPC-H and TPC-DS benchmark datasets at various scale factors.

## Schemas

1. TPCH_SF1 - TPC-H data at scale factor 1
2. TPCH_SF10 - TPC-H data at scale factor 10
3. TPCH_SF100 - TPC-H data at scale factor 100
4. TPCH_SF1000 - TPC-H data at scale factor 1000
5. TPCDS_SF10TCL - TPC-DS data at scale factor 10
6. TPCDS_SF100TCL - TPC-DS data at scale factor 100

This documentation will focus on the TPCH_SF1 schema as a representative example, as the structure is identical across all TPC-H scale factors.

## Tables in TPCH_SF1 Schema

### CUSTOMER Table
A table containing customer information.

**Columns:**
- C_CUSTKEY (NUMBER, NOT NULL) - Primary key for customer
- C_NAME (TEXT, NOT NULL) - Customer name
- C_ADDRESS (TEXT, NOT NULL) - Customer address
- C_NATIONKEY (NUMBER, NOT NULL) - Foreign key to NATION table
- C_PHONE (TEXT, NOT NULL) - Customer phone number
- C_ACCTBAL (NUMBER, NOT NULL) - Customer account balance
- C_MKTSEGMENT (TEXT) - Market segment
- C_COMMENT (TEXT) - Additional comments

**Sample Query:**
```sql
SELECT 
    c.C_NAME,
    c.C_MKTSEGMENT,
    n.N_NAME as NATION,
    COUNT(o.O_ORDERKEY) as ORDER_COUNT,
    SUM(o.O_TOTALPRICE) as TOTAL_SPEND
FROM CUSTOMER c
JOIN NATION n ON c.C_NATIONKEY = n.N_NATIONKEY
LEFT JOIN ORDERS o ON c.C_CUSTKEY = o.O_CUSTKEY
GROUP BY 1, 2, 3
ORDER BY TOTAL_SPEND DESC
LIMIT 10;
```

### ORDERS Table
Contains order header information.

**Columns:**
- O_ORDERKEY (NUMBER, NOT NULL) - Primary key for orders
- O_CUSTKEY (NUMBER, NOT NULL) - Foreign key to CUSTOMER table
- O_ORDERSTATUS (TEXT, NOT NULL) - Current status of the order
- O_TOTALPRICE (NUMBER, NOT NULL) - Total price of the order
- O_ORDERDATE (DATE, NOT NULL) - Date the order was placed
- O_ORDERPRIORITY (TEXT, NOT NULL) - Priority of the order
- O_CLERK (TEXT, NOT NULL) - Clerk who processed the order
- O_SHIPPRIORITY (NUMBER, NOT NULL) - Priority of shipping
- O_COMMENT (TEXT, NOT NULL) - Additional comments

**Sample Query:**
```sql
SELECT 
    DATE_TRUNC('month', O_ORDERDATE) as ORDER_MONTH,
    O_ORDERSTATUS,
    COUNT(*) as ORDER_COUNT,
    SUM(O_TOTALPRICE) as TOTAL_REVENUE
FROM ORDERS
GROUP BY 1, 2
ORDER BY 1, 2;
```

### LINEITEM Table
Contains the line items for each order.

**Columns:**
- L_ORDERKEY (NUMBER, NOT NULL) - Foreign key to ORDERS table
- L_PARTKEY (NUMBER, NOT NULL) - Foreign key to PART table
- L_SUPPKEY (NUMBER, NOT NULL) - Foreign key to SUPPLIER table
- L_LINENUMBER (NUMBER, NOT NULL) - Line number within the order
- L_QUANTITY (NUMBER, NOT NULL) - Quantity ordered
- L_EXTENDEDPRICE (NUMBER, NOT NULL) - Line item price
- L_DISCOUNT (NUMBER, NOT NULL) - Discount percentage
- L_TAX (NUMBER, NOT NULL) - Tax percentage
- L_RETURNFLAG (TEXT, NOT NULL) - Return status flag
- L_LINESTATUS (TEXT, NOT NULL) - Status of the line item
- L_SHIPDATE (DATE, NOT NULL) - Date shipped
- L_COMMITDATE (DATE, NOT NULL) - Commit date
- L_RECEIPTDATE (DATE, NOT NULL) - Receipt date
- L_SHIPINSTRUCT (TEXT, NOT NULL) - Shipping instructions
- L_SHIPMODE (TEXT, NOT NULL) - Mode of shipping
- L_COMMENT (TEXT, NOT NULL) - Additional comments

**Sample Query:**
```sql
SELECT 
    p.P_TYPE,
    l.L_SHIPMODE,
    COUNT(*) as SHIPMENT_COUNT,
    AVG(l.L_QUANTITY) as AVG_QUANTITY,
    SUM(l.L_EXTENDEDPRICE * (1 - l.L_DISCOUNT)) as TOTAL_REVENUE
FROM LINEITEM l
JOIN PART p ON l.L_PARTKEY = p.P_PARTKEY
WHERE l.L_SHIPDATE >= DATEADD(month, -3, CURRENT_DATE())
GROUP BY 1, 2
ORDER BY TOTAL_REVENUE DESC
LIMIT 10;
```

### PART Table
Contains information about parts/products.

**Columns:**
- P_PARTKEY (NUMBER, NOT NULL) - Primary key for parts
- P_NAME (TEXT, NOT NULL) - Part name
- P_MFGR (TEXT, NOT NULL) - Manufacturer
- P_BRAND (TEXT, NOT NULL) - Brand
- P_TYPE (TEXT, NOT NULL) - Type of part
- P_SIZE (NUMBER, NOT NULL) - Size
- P_CONTAINER (TEXT, NOT NULL) - Container type
- P_RETAILPRICE (NUMBER, NOT NULL) - Retail price
- P_COMMENT (TEXT) - Additional comments

**Sample Query:**
```sql
SELECT 
    P_BRAND,
    P_TYPE,
    P_SIZE,
    COUNT(DISTINCT PS_SUPPKEY) as SUPPLIER_COUNT,
    AVG(P_RETAILPRICE) as AVG_RETAIL_PRICE
FROM PART
JOIN PARTSUPP ON P_PARTKEY = PS_PARTKEY
GROUP BY 1, 2, 3
HAVING COUNT(DISTINCT PS_SUPPKEY) > 1
ORDER BY SUPPLIER_COUNT DESC;
```

### SUPPLIER Table
Contains information about suppliers.

**Columns:**
- S_SUPPKEY (NUMBER, NOT NULL) - Primary key for supplier
- S_NAME (TEXT, NOT NULL) - Supplier name
- S_ADDRESS (TEXT, NOT NULL) - Supplier address
- S_NATIONKEY (NUMBER, NOT NULL) - Foreign key to NATION table
- S_PHONE (TEXT, NOT NULL) - Supplier phone number
- S_ACCTBAL (NUMBER, NOT NULL) - Supplier account balance
- S_COMMENT (TEXT) - Additional comments

**Sample Query:**
```sql
SELECT 
    n.N_NAME as NATION,
    COUNT(DISTINCT s.S_SUPPKEY) as SUPPLIER_COUNT,
    AVG(s.S_ACCTBAL) as AVG_ACCOUNT_BALANCE,
    COUNT(DISTINCT p.P_PARTKEY) as PARTS_SUPPLIED
FROM SUPPLIER s
JOIN NATION n ON s.S_NATIONKEY = n.N_NATIONKEY
JOIN PARTSUPP ps ON s.S_SUPPKEY = ps.PS_SUPPKEY
JOIN PART p ON ps.PS_PARTKEY = p.P_PARTKEY
GROUP BY 1
ORDER BY SUPPLIER_COUNT DESC;
```

### PARTSUPP Table
Contains supplier pricing and availability information for parts.

**Columns:**
- PS_PARTKEY (NUMBER, NOT NULL) - Foreign key to PART table
- PS_SUPPKEY (NUMBER, NOT NULL) - Foreign key to SUPPLIER table
- PS_AVAILQTY (NUMBER, NOT NULL) - Available quantity
- PS_SUPPLYCOST (NUMBER, NOT NULL) - Supply cost
- PS_COMMENT (TEXT) - Additional comments

**Sample Query:**
```sql
SELECT 
    p.P_TYPE,
    COUNT(DISTINCT ps.PS_SUPPKEY) as SUPPLIER_COUNT,
    AVG(ps.PS_SUPPLYCOST) as AVG_SUPPLY_COST,
    SUM(ps.PS_AVAILQTY) as TOTAL_AVAILABLE_QTY
FROM PARTSUPP ps
JOIN PART p ON ps.PS_PARTKEY = p.P_PARTKEY
GROUP BY 1
ORDER BY SUPPLIER_COUNT DESC;
```

### NATION Table
Contains information about nations/countries.

**Columns:**
- N_NATIONKEY (NUMBER, NOT NULL) - Primary key for nation
- N_NAME (TEXT, NOT NULL) - Nation name
- N_REGIONKEY (NUMBER, NOT NULL) - Foreign key to REGION table
- N_COMMENT (TEXT) - Additional comments

**Sample Query:**
```sql
SELECT 
    n.N_NAME as NATION,
    r.R_NAME as REGION,
    COUNT(DISTINCT c.C_CUSTKEY) as CUSTOMER_COUNT,
    COUNT(DISTINCT s.S_SUPPKEY) as SUPPLIER_COUNT
FROM NATION n
JOIN REGION r ON n.N_REGIONKEY = r.R_REGIONKEY
LEFT JOIN CUSTOMER c ON n.N_NATIONKEY = c.C_NATIONKEY
LEFT JOIN SUPPLIER s ON n.N_NATIONKEY = s.S_NATIONKEY
GROUP BY 1, 2
ORDER BY CUSTOMER_COUNT DESC;
```

### REGION Table
Contains information about geographical regions.

**Columns:**
- R_REGIONKEY (NUMBER, NOT NULL) - Primary key for region
- R_NAME (TEXT, NOT NULL) - Region name
- R_COMMENT (TEXT) - Additional comments

**Sample Query:**
```sql
SELECT 
    r.R_NAME as REGION,
    COUNT(DISTINCT n.N_NATIONKEY) as NATION_COUNT,
    COUNT(DISTINCT c.C_CUSTKEY) as CUSTOMER_COUNT,
    SUM(o.O_TOTALPRICE) as TOTAL_SALES
FROM REGION r
JOIN NATION n ON r.R_REGIONKEY = n.N_REGIONKEY
LEFT JOIN CUSTOMER c ON n.N_NATIONKEY = c.C_NATIONKEY
LEFT JOIN ORDERS o ON c.C_CUSTKEY = o.O_CUSTKEY
GROUP BY 1
ORDER BY TOTAL_SALES DESC;
```

## Table Relationships

The TPC-H schema represents a business model with the following key relationships:

1. Customers (CUSTOMER) place Orders (ORDERS)
2. Orders (ORDERS) contain line items (LINEITEM)
3. Line items (LINEITEM) reference parts (PART)
4. Parts (PART) are supplied by suppliers (SUPPLIER) through PARTSUPP
5. Both customers and suppliers are associated with nations (NATION)
6. Nations (NATION) belong to regions (REGION)

This structure allows for analysis of:
- Customer ordering patterns
- Supplier performance
- Product sales and inventory
- Geographic distribution of business
- Supply chain efficiency