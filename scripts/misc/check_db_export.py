# Quick sanity: posts with at least one top comment

import duckdb

con = duckdb.connect("../../diet.db")

df = con.execute("""
-- Quick sanity: posts with at least one top comment
SELECT subreddit, COUNT(*) AS n_posts
FROM posts
WHERE id IN (SELECT DISTINCT post_id FROM comments)
GROUP BY subreddit;
""").fetchdf()

print(df)