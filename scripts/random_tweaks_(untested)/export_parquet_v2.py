import duckdb

# Connect to the existing DuckDB store
con = duckdb.connect('diet.db')

# 1. Create a deterministic split logic and top-3 comments aggregation as a VIEW
con.execute("""
CREATE OR REPLACE VIEW train_text AS
WITH top_comments AS (
    SELECT
        post_id,
        string_agg(body, ' ') AS top_comments
    FROM (
        SELECT
            post_id,
            body,
            score,
            ROW_NUMBER() OVER (PARTITION BY post_id ORDER BY score DESC) AS rn
        FROM comments
    ) sub
    WHERE rn <= 3
    GROUP BY post_id
)
SELECT
    p.id,
    p.diet,
    -- Concatenate title, body, and top comments into one text field
    p.title || ' ' || p.selftext || ' ' || COALESCE(tc.top_comments, '') AS text,
    p.score,
    p.created_ts,
    -- Deterministic split: hash(id) mod 10
    CASE
        WHEN abs(hash(p.id)) % 10 = 0 THEN 'test'
        WHEN abs(hash(p.id)) % 10 = 1 THEN 'dev'
        ELSE 'train'
    END AS split
FROM posts p
LEFT JOIN top_comments tc ON tc.post_id = p.id
WHERE p.selftext IS NOT NULL
""")

# 2. Export the view to partitioned Parquet files by split
# Creates directory structure: data/train/, data/dev/, data/test/
con.execute("""
COPY train_text
TO 'data/train.parquet'
(FORMAT PARQUET, PARTITION_BY (split));
""")

print("Export complete: 'data/train.parquet' partitioned by split.")
