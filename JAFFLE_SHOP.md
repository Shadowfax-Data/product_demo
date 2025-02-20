# JAFFLE_SHOP Database Documentation

## Overview
The JAFFLE_SHOP database contains data for a restaurant management system, tracking customers, orders, products, and locations. The database is organized into multiple schemas, with DEMO being the main schema containing the core business tables.

## Schemas
- DEMO: Main schema containing core business tables
- DEV: Development schema with similar structure to DEMO
- PUBLIC: Default schema
- INFORMATION_SCHEMA: System schema with metadata views

## Tables in DEMO Schema

### CUSTOMERS
Stores customer information and their order history metrics.

#### Columns
- `CUSTOMER_ID` (TEXT): Unique identifier for each customer
- `CUSTOMER_NAME` (TEXT): Name of the customer
- `COUNT_LIFETIME_ORDERS` (NUMBER): Total number of orders placed by the customer
- `FIRST_ORDERED_AT` (TIMESTAMP_NTZ): Timestamp of customer's first order
- `LAST_ORDERED_AT` (TIMESTAMP_NTZ): Timestamp of customer's most recent order
- `LIFETIME_SPEND_PRETAX` (NUMBER): Total amount spent before tax
- `LIFETIME_TAX_PAID` (NUMBER): Total tax paid on all orders
- `LIFETIME_SPEND` (NUMBER): Total amount spent including tax
- `CUSTOMER_TYPE` (TEXT): Classification of the customer

#### Sample Query
```sql
-- Get top customers by lifetime spend
SELECT 
    customer_name,
    count_lifetime_orders,
    lifetime_spend,
    first_ordered_at,
    last_ordered_at
FROM DEMO.CUSTOMERS
ORDER BY lifetime_spend DESC
LIMIT 10;
```

### ORDERS
Tracks all orders placed at various locations.

#### Columns
- `ORDER_ID` (TEXT): Unique identifier for each order
- `LOCATION_ID` (TEXT): Reference to the location where order was placed
- `CUSTOMER_ID` (TEXT): Reference to the customer who placed the order
- `SUBTOTAL_CENTS` (NUMBER): Order subtotal in cents
- `TAX_PAID_CENTS` (NUMBER): Tax amount in cents
- `ORDER_TOTAL_CENTS` (NUMBER): Total order amount in cents
- `SUBTOTAL` (NUMBER): Order subtotal in dollars
- `TAX_PAID` (NUMBER): Tax amount in dollars
- `ORDER_TOTAL` (NUMBER): Total order amount in dollars
- `ORDERED_AT` (TIMESTAMP_NTZ): Timestamp when order was placed
- `ORDER_COST` (NUMBER): Cost of the order to the business
- `ORDER_ITEMS_SUBTOTAL` (NUMBER): Subtotal of all items in the order
- `COUNT_FOOD_ITEMS` (NUMBER): Number of food items in the order
- `COUNT_DRINK_ITEMS` (NUMBER): Number of drink items in the order
- `COUNT_ORDER_ITEMS` (NUMBER): Total number of items in the order
- `IS_FOOD_ORDER` (BOOLEAN): Whether the order contains food
- `IS_DRINK_ORDER` (BOOLEAN): Whether the order contains drinks
- `CUSTOMER_ORDER_NUMBER` (NUMBER): Sequential number of this order for the customer

#### Sample Query
```sql
-- Get daily order statistics by location
SELECT 
    l.location_name,
    DATE(o.ordered_at) as order_date,
    COUNT(DISTINCT o.order_id) as total_orders,
    SUM(o.order_total) as total_revenue,
    AVG(o.order_total) as avg_order_value
FROM DEMO.ORDERS o
JOIN DEMO.LOCATIONS l ON o.location_id = l.location_id
GROUP BY l.location_name, DATE(o.ordered_at)
ORDER BY order_date DESC;
```

### ORDER_ITEMS
Details of individual items within each order.

#### Columns
- `ORDER_ITEM_ID` (TEXT): Unique identifier for each order item
- `ORDER_ID` (TEXT): Reference to the parent order
- `PRODUCT_ID` (TEXT): Reference to the product ordered
- `ORDERED_AT` (TIMESTAMP_NTZ): Timestamp when item was ordered
- `PRODUCT_NAME` (TEXT): Name of the product
- `PRODUCT_PRICE` (NUMBER): Price of the product
- `IS_FOOD_ITEM` (BOOLEAN): Whether this is a food item
- `IS_DRINK_ITEM` (BOOLEAN): Whether this is a drink item
- `SUPPLY_COST` (NUMBER): Cost of supplies for this item

#### Sample Query
```sql
-- Get most popular items by quantity sold
SELECT 
    oi.product_name,
    COUNT(*) as times_ordered,
    SUM(oi.product_price) as total_revenue,
    AVG(oi.product_price) as avg_price
FROM DEMO.ORDER_ITEMS oi
GROUP BY oi.product_name
ORDER BY times_ordered DESC
LIMIT 10;
```

### PRODUCTS
Catalog of available products.

#### Columns
- `PRODUCT_ID` (TEXT): Unique identifier for each product
- `PRODUCT_NAME` (TEXT): Name of the product
- `PRODUCT_TYPE` (TEXT): Type/category of the product
- `PRODUCT_DESCRIPTION` (TEXT): Description of the product
- `PRODUCT_PRICE` (NUMBER): Price of the product
- `IS_FOOD_ITEM` (BOOLEAN): Whether this is a food item
- `IS_DRINK_ITEM` (BOOLEAN): Whether this is a drink item

#### Sample Query
```sql
-- Get product sales and profitability analysis
SELECT 
    p.product_name,
    p.product_type,
    COUNT(DISTINCT oi.order_id) as number_of_orders,
    SUM(oi.product_price) as total_revenue,
    SUM(oi.supply_cost) as total_cost,
    SUM(oi.product_price - oi.supply_cost) as total_profit
FROM DEMO.PRODUCTS p
LEFT JOIN DEMO.ORDER_ITEMS oi ON p.product_id = oi.product_id
GROUP BY p.product_name, p.product_type
ORDER BY total_profit DESC;
```

### LOCATIONS
Store locations where orders can be placed.

#### Columns
- `LOCATION_ID` (TEXT): Unique identifier for each location
- `LOCATION_NAME` (TEXT): Name of the location
- `TAX_RATE` (FLOAT): Tax rate applied at this location
- `OPENED_DATE` (TIMESTAMP_NTZ): Date when location opened

#### Sample Query
```sql
-- Get location performance metrics
SELECT 
    l.location_name,
    l.tax_rate,
    COUNT(DISTINCT o.order_id) as total_orders,
    COUNT(DISTINCT o.customer_id) as unique_customers,
    SUM(o.order_total) as total_revenue,
    SUM(o.tax_paid) as total_tax_collected
FROM DEMO.LOCATIONS l
LEFT JOIN DEMO.ORDERS o ON l.location_id = o.location_id
GROUP BY l.location_name, l.tax_rate
ORDER BY total_revenue DESC;
```

### SUPPLIES
Inventory of supplies used to make products.

#### Columns
- `SUPPLY_UUID` (TEXT): Unique identifier for supply record
- `SUPPLY_ID` (TEXT): Identifier for the supply item
- `PRODUCT_ID` (TEXT): Reference to the product this supply is used for
- `SUPPLY_NAME` (TEXT): Name of the supply item
- `SUPPLY_COST` (NUMBER): Cost of the supply item
- `IS_PERISHABLE_SUPPLY` (BOOLEAN): Whether the supply item is perishable

#### Sample Query
```sql
-- Get supply costs and usage by product
SELECT 
    p.product_name,
    s.supply_name,
    s.supply_cost,
    s.is_perishable_supply,
    COUNT(oi.order_item_id) as times_used
FROM DEMO.SUPPLIES s
JOIN DEMO.PRODUCTS p ON s.product_id = p.product_id
LEFT JOIN DEMO.ORDER_ITEMS oi ON p.product_id = oi.product_id
GROUP BY p.product_name, s.supply_name, s.supply_cost, s.is_perishable_supply
ORDER BY times_used DESC;
```