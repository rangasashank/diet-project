import duckdb
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Connect to the existing DuckDB store
def main():
    con = duckdb.connect('diet.db')

    # Register VADER UDF for compound score
    analyzer = SentimentIntensityAnalyzer()
    con.create_function('vader_score', lambda txt: analyzer.polarity_scores(txt)['compound'])

    # Create (or replace) a view that adds VADER scores and labels to the train_text view
    con.execute("""
    CREATE OR REPLACE VIEW train_vader AS
    SELECT
        id,
        diet,
        text,
        score,
        created_ts,
        split,
        -- Raw compound sentiment score
        vader_score(text) AS vader,
        -- Categorical label based on VADER thresholds
        CASE
            WHEN vader_score(text) >= 0.05 THEN 'positive'
            WHEN vader_score(text) <= -0.05 THEN 'negative'
            ELSE 'neutral'
        END AS vader_label
    FROM train_text
    """)

    # Export the enriched view to Parquet, partitioned by split
    con.execute("""
    COPY train_vader
    TO 'data/train_vader.parquet'
    (FORMAT PARQUET, PARTITION_BY (split));
    """)

    print("Export complete: 'data/train_vader.parquet' partitioned by split.")

if __name__ == '__main__':
    main()
