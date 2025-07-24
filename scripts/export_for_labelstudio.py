#!/usr/bin/env python
"""
Export a random sample from diet.db → a single JSON array for Label Studio.

Each task contains:
  id          : reddit post ID
  subreddit   : weak diet label (prefilled, editable)
  text        : title, body, and up to 3 top comments (each clearly separated)
  diet        : ""  (optional manual diet tag)
  sentiment   : ""  (required manual sentiment tag)
"""
import argparse, json, duckdb, textwrap

SQL_TEMPLATE = textwrap.dedent("""\
    WITH ranked AS (
        SELECT post_id,
               body,
               score,
               ROW_NUMBER() OVER (PARTITION BY post_id ORDER BY score DESC) AS rnk
        FROM comments
    )
    SELECT p.id,
           p.subreddit,
           p.title,
           p.selftext,
           c1.body AS comment1,
           c2.body AS comment2,
           c3.body AS comment3
    FROM posts p
    LEFT JOIN ranked c1 ON p.id = c1.post_id AND c1.rnk = 1
    LEFT JOIN ranked c2 ON p.id = c2.post_id AND c2.rnk = 2
    LEFT JOIN ranked c3 ON p.id = c3.post_id AND c3.rnk = 3
    {diet_filter}
    ORDER BY RANDOM()
    LIMIT {limit}
""")

def build_tasks(rows):
    tasks = []
    for row in rows:
        pieces = []
        if row['title']:
            pieces.append(row['title'].strip())
        if row['selftext']:
            pieces.append(row['selftext'].strip())
        for i, com in enumerate(('comment1','comment2','comment3'), start=1):
            if row.get(com):
                pieces.append(f"-- Comment {i} --\n" + row[com].strip())
        tasks.append({
            "id":       row['id'],
            "subreddit":row['subreddit'],
            "text":     "\n\n".join(pieces),
            "diet":     "",
            "sentiment":""
        })
    return tasks

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db",      default="../diet.db")
    p.add_argument("--out",     default="../exports/labelstudio_tasks.json")
    p.add_argument("--n",       type=int, default=300)
    p.add_argument("--diets",   nargs="*")
    args = p.parse_args()

    con = duckdb.connect(args.db)
    diet_filter = ""
    if args.diets:
        vals = ", ".join(f"'{d}'" for d in args.diets)
        diet_filter = f"WHERE p.subreddit IN ({vals})"
    sql = SQL_TEMPLATE.format(diet_filter=diet_filter, limit=args.n)
    df = con.execute(sql).fetchdf().to_dict(orient="records")

    tasks = build_tasks(df)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(tasks)} tasks to {args.out}")

if __name__ == "__main__":
    main()
