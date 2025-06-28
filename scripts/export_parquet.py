import duckdb
from pathlib import Path

# Connect to DuckDB database
con = duckdb.connect("diet.db")
con.execute("PRAGMA threads=8;")  # tweak to utilize all cores

# Create exports directory if it doesn't exist
export_dir = Path(__file__).parent.parent / 'exports'
export_dir.mkdir(parents=True, exist_ok=True)

# Aggregation query with top-3 comments per post
AGG_QUERY = f"""
COPY (
  WITH top_comments AS (
    SELECT post_id, body
    FROM (
      SELECT post_id, body,
             ROW_NUMBER() OVER (PARTITION BY post_id ORDER BY score DESC) AS rn
      FROM comments
    ) filtered
    WHERE rn <= 3
  )
  SELECT
    p.id,
    p.subreddit AS diet_label,
    CONCAT_WS('\n\n',
      p.title || '\n' || p.selftext,
      COALESCE(STRING_AGG(top_comments.body, '\n\n'), '')
    ) AS text
  FROM posts p
  LEFT JOIN top_comments ON p.id = top_comments.post_id
  WHERE p.score > 1
  GROUP BY p.id, p.subreddit, p.title, p.selftext
) TO '{(export_dir / 'train.parquet').as_posix()}' (FORMAT 'parquet', COMPRESSION 'zstd');
"""

# Execute export
print("Exporting aggregated data to Parquet...")
con.execute(AGG_QUERY)

con.close()
print("Parquet export complete.")
