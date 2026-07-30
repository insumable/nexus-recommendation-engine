import duckdb

print("Connecting to DuckDB (creating local database file)...")
con = duckdb.connect("nexus.duckdb")

print("Processing metadata file (this may take a minute)...")
con.execute("""
    CREATE TABLE IF NOT EXISTS dim_electronics AS 
    SELECT 
        parent_asin AS item_id,
        title,
        TRY_CAST(price AS DOUBLE) AS price,
        categories
    FROM read_json_auto(
        'data/meta_Electronics.jsonl.gz',
        sample_size = 50000,
        columns = {
            'parent_asin': 'VARCHAR',
            'title': 'VARCHAR',
            'price': 'VARCHAR',
            'categories': 'JSON'
        }
    );
""")

print("Processing reviews file (this will map your 6 GB file into OLAP)...")
con.execute("""
    CREATE TABLE IF NOT EXISTS fact_reviews AS 
    SELECT 
        user_id,
        parent_asin AS item_id,
        rating,
        timestamp
    FROM read_json_auto('data/Electronics.jsonl.gz', sample_size = 50000);
""")

print("Ingestion complete! Checking table sizes...")
print("Products count:", con.execute("SELECT COUNT(*) FROM dim_electronics;").fetchone()[0])
print("Reviews count:", con.execute("SELECT COUNT(*) FROM fact_reviews;").fetchone()[0])

con.close()