# CDC Vaccination Coverage Data Processing

This project processes and loads CDC vaccination coverage datasets into Snowflake for analysis.

## Project Structure

```
/workspace
├── data/                 # Raw CSV files from CDC
├── scripts/             # Python processing scripts
│   └── cdc_data_loader.py  # Main data processing script
├── docs/               # Table documentation
└── sql/                # SQL table creation scripts
```

## Datasets

The project processes the following CDC vaccination coverage datasets:

1. Adolescents (13-17 Years)
2. Adults (18+ Years)
3. Healthcare Personnel
4. Nursing Home Residents
5. Pregnant Women
6. Young Children (0-35 Months)
7. Kindergartners
8. Children (19-35 Months) by Race/Hispanic Origin

## Documentation

Each table has its own markdown documentation file in the `docs/` directory with:
- Table description
- Column definitions
- Sample queries

## Data Processing

The data processing workflow:
1. Downloads CDC CSV files
2. Processes metadata
3. Creates Snowflake tables with appropriate schema and comments
4. Loads data into Snowflake
5. Generates documentation