import duckdb
from pathlib import Path

# Connect to DuckDB database file (creates if not exists)
con = duckdb.connect("diet.db")
print("Connected to diet.db")
con.execute("PRAGMA threads=8;")  # tweak to utilize all cores

# Create empty tables if they don't exist
con.execute("""
CREATE TABLE IF NOT EXISTS posts (
    id TEXT,
    subreddit TEXT,
    title TEXT,
    selftext TEXT,
    score BIGINT,
    created_utc TIMESTAMP
);
""")

con.execute("""
CREATE TABLE IF NOT EXISTS comments (
    id TEXT,
    post_id TEXT,
    body TEXT,
    score BIGINT,
    created_utc TIMESTAMP
);
""")

# Ingest submissions (posts)
for path in Path("./raw").glob("*_submissions.zst"):
    print(f"Loading posts from {path.name}...")
    con.execute(f"""
    INSERT INTO posts
    SELECT
      id,
      subreddit,
      coalesce(title, '') AS title,
      coalesce(selftext, '') AS selftext,
      score,
      to_timestamp(CAST(created_utc AS DOUBLE)) AS created_utc
    FROM read_json_auto('{path.as_posix()}', compression='zstd');
    """)

# Ingest top-level comments
for path in Path("./raw").glob("*_comments.zst"):
    print(f"Loading comments from {path.name} (top-level only)...")
    con.execute(f"""
    INSERT INTO comments
    SELECT
      id,
      substr(link_id, 4) AS post_id,
      coalesce(body, '') AS body,
      score,
      to_timestamp(CAST(created_utc AS DOUBLE)) AS created_utc
    FROM read_json_auto('{path.as_posix()}', compression='zstd')
    WHERE parent_id LIKE 't3_%';
    """)

con.close()

print("Ingestion complete.")
