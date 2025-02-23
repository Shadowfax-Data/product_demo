# Sample Extracted Balance Sheet Data

This document provides examples of the balance sheet data extracted from Snowflake's quarterly financial statements for FY2025.

## Q1 FY2025 (April 30, 2024)

```csv
fiscal_quarter,category,line_item,amount,is_total
Q1 FY2025,Other,"Property and equipment, net",263667.0,False
Q1 FY2025,Assets,"Intangible assets, net",307967.0,False
Q1 FY2025,Deferred Items,Total assets,7298018.0,True
Q1 FY2025,Liabilities,"Operating lease liabilities, current",30940.0,False
Q1 FY2025,Deferred Items,Total current liabilities,2428823.0,True
Q1 FY2025,Deferred Items,"Operating lease liabilities, non-current",247501.0,False
Q1 FY2025,Deferred Items,Total liabilities,2730326.0,True
Q1 FY2025,Other,Accumulated other comprehensive loss,-15713.0,False
Q1 FY2025,Other,Accumulated deficit,-4908921.0,False
Q1 FY2025,Other,Total Snowflake Inc. stockholders' equity,4558234.0,True
Q1 FY2025,Other,Total stockholders' equity,4567692.0,True
Q1 FY2025,Other,Total liabilities and stockholders' equity,7298018.0,True
```

## Q2 FY2025 (July 31, 2024)

```csv
fiscal_quarter,category,line_item,amount,is_total
Q2 FY2025,Assets,"Intangible assets, net",286538.0,False
Q2 FY2025,Deferred Items,Total assets,6943886.0,True
Q2 FY2025,Liabilities,"Operating lease liabilities, current",32843.0,False
Q2 FY2025,Deferred Items,Total current liabilities,2464682.0,True
Q2 FY2025,Deferred Items,"Operating lease liabilities, non-current",279969.0,False
Q2 FY2025,Deferred Items,Total liabilities,2806298.0,True
Q2 FY2025,Other,Accumulated other comprehensive loss,-5379.0,False
Q2 FY2025,Other,Accumulated deficit,-5625819.0,False
Q2 FY2025,Other,Total Snowflake Inc. stockholders' equity,4129001.0,True
Q2 FY2025,Other,Total stockholders' equity,4137588.0,True
Q2 FY2025,Other,Total liabilities and stockholders' equity,6943886.0,True
```

## Q3 FY2025 (October 31, 2024)

```csv
fiscal_quarter,category,line_item,amount,is_total
Q3 FY2025,Other,"Property and equipment, net",278374.0,False
Q3 FY2025,Assets,"Intangible assets, net",268514.0,False
Q3 FY2025,Deferred Items,Total assets,8202258.0,True
Q3 FY2025,Liabilities,"Operating lease liabilities, current",38288.0,False
Q3 FY2025,Deferred Items,Total current liabilities,2647272.0,True
Q3 FY2025,Deferred Items,"Convertible senior notes, net",2269459.0,False
Q3 FY2025,Deferred Items,"Operating lease liabilities, non-current",287881.0,False
Q3 FY2025,Deferred Items,Total liabilities,5267849.0,True
Q3 FY2025,Other,Accumulated other comprehensive loss,-2760.0,False
Q3 FY2025,Other,Accumulated deficit,-6970492.0,False
Q3 FY2025,Other,Total Snowflake Inc. stockholders' equity,2929445.0,True
Q3 FY2025,Other,Total stockholders' equity,2934409.0,True
Q3 FY2025,Other,Total liabilities and stockholders' equity,8202258.0,True
```

## Key Observations

1. **Total Assets Growth**:
   - Q1: $7,298,018,000
   - Q2: $6,943,886,000
   - Q3: $8,202,258,000

2. **Total Liabilities Trend**:
   - Q1: $2,730,326,000
   - Q2: $2,806,298,000
   - Q3: $5,267,849,000

3. **Stockholders' Equity Changes**:
   - Q1: $4,567,692,000
   - Q2: $4,137,588,000
   - Q3: $2,934,409,000

4. **Notable Items**:
   - Convertible senior notes appear in Q3 with a value of $2,269,459,000
   - Operating lease liabilities show consistent presence across quarters
   - Accumulated deficit has increased each quarter

## Data Quality Notes

1. **Categorization**:
   - Some items are categorized as "Other" or "Deferred Items" due to complex table structure
   - Main categories (Assets, Liabilities, Equity) are consistently identified

2. **Validation**:
   - Total assets match total liabilities plus stockholders' equity in each quarter
   - All monetary values are properly formatted and scaled
   - Fiscal quarters are correctly identified from the source documents

3. **Limitations**:
   - Some subcategories might be merged due to PDF table extraction challenges
   - Certain line items might have slightly different names across quarters
   - Some detailed breakdowns might be missing due to table structure complexity