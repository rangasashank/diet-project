import duckdb

# Connect to DuckDB database (creates diet.db if it doesn't exist)
con = duckdb.connect('diet.db')

# Define diet-to-subreddit mapping
# Expand this dict with all diets/subreddits you want to include
diet_subreddits = {
    'keto': 'keto',
    'vegan': 'vegan',
    'paleo': 'paleo',
    'intermittentfasting': 'intermittentfasting',
    'whole30': 'whole30'
}

# Build CASE WHEN clauses for diet mapping
diet_cases = ' '.join(
    f"WHEN subreddit = '{sub}' THEN '{diet}'" 
    for diet, sub in diet_subreddits.items()
)

# Ingest posts (submissions)
con.execute(f"""
CREATE OR REPLACE TABLE posts AS
SELECT
    id::VARCHAR,
    subreddit::VARCHAR,
    title::VARCHAR,
    -- Clean stray unicode escapes
    regexp_replace(selftext, '\\u[0-9A-Fa-f]{{4}}', ' ', 'g') AS selftext,
    -- Convert epoch seconds to timestamp
    to_timestamp(created_utc) AS created_ts,
    score::INTEGER,
    num_comments::INTEGER,
    -- Map subreddit to diet label
    CASE
        {diet_cases}
        ELSE NULL
    END AS diet
FROM read_json_auto('data/*_submissions.json.zst')
""")

# Ingest comments
con.execute("""
CREATE OR REPLACE TABLE comments AS
SELECT
    id::VARCHAR,
    -- Strip 't3_' prefix to match posts.id
    substr(link_id, 4)::VARCHAR AS post_id,
    author::VARCHAR,
    -- Clean stray unicode escapes
    regexp_replace(body, '\\u[0-9A-Fa-f]{{4}}', ' ', 'g') AS body,
    score::INTEGER,
    to_timestamp(created_utc) AS created_ts
FROM read_json_auto('data/*_comments.json.zst')
""")

# Add primary key and index for performance and deduplication
con.execute('ALTER TABLE posts ADD PRIMARY KEY(id)')
con.execute('CREATE INDEX IF NOT EXISTS comments_post_idx ON comments(post_id)')

# Optional: record ingestion metadata
con.execute("""
CREATE OR REPLACE TABLE ingestion_log AS
SELECT
    'posts' AS table_name,
    count(*) AS row_count,
    CURRENT_TIMESTAMP() AS ingested_at
UNION ALL
SELECT
    'comments' AS table_name,
    count(*) AS row_count,
    CURRENT_TIMESTAMP() AS ingested_at
""")

print("Ingestion complete: posts and comments loaded into diet.db")
