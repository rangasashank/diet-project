#!/usr/bin/env python3
"""
scripts/add_sentiment_vader.py

Reads a Parquet or JSONL file with a `text` column, computes VADER sentiment in parallel,
and writes out a new Parquet with VADER compound scores and categorical labels.
"""

import argparse
import json
import pandas as pd
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from multiprocessing import Pool, cpu_count

def process_chunk(args):
    """Worker: compute VADER on one DataFrame chunk."""
    df_chunk, text_col, pos_thr, neg_thr = args
    analyzer = SentimentIntensityAnalyzer()
    # compute compound scores
    df_chunk["vader_compound"] = (
        df_chunk[text_col].fillna("").apply(lambda txt: analyzer.polarity_scores(txt)["compound"])
    )
    # classify into 3 bins
    df_chunk["vader_sentiment"] = df_chunk["vader_compound"].apply(
        lambda s: "positive" if s >= pos_thr
                  else ("negative" if s <= neg_thr else "neutral")
    )
    return df_chunk

def chunk_dataframe(df, n_chunks):
    """Split df into roughly equal chunks."""
    return np.array_split(df, n_chunks)

def read_jsonl_in_chunks(path, chunksize):
    """Yield DataFrame of up to chunksize JSON lines at a time."""
    batch = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            batch.append(json.loads(line))
            if len(batch) >= chunksize:
                yield pd.DataFrame(batch)
                batch = []
        if batch:
            yield pd.DataFrame(batch)

def main():
    p = argparse.ArgumentParser(
        description="Add VADER sentiment in parallel to a dataset with a `text` column."
    )
    p.add_argument("-i", "--input",      required=True,
                   help="Input file: .parquet or .jsonl")
    p.add_argument("-o", "--output",     required=True,
                   help="Output Parquet path (e.g. exports/train_vader.parquet)")
    p.add_argument("-t", "--text-col",   default="text",
                   help="Name of the text column to analyze")
    p.add_argument("-n", "--n-workers",  type=int, default=cpu_count(),
                   help="Number of parallel workers")
    p.add_argument("-c", "--chunksize",  type=int, default=100_000,
                   help="Lines per chunk when reading JSONL")
    p.add_argument("--pos-thr", type=float, default=0.05,
                   help="VADER positive threshold")
    p.add_argument("--neg-thr", type=float, default=-0.05,
                   help="VADER negative threshold")
    args = p.parse_args()

    pool = Pool(args.n_workers)
    tasks = []

    if args.input.endswith(".parquet"):
        # read full DF, split into `n_workers` pieces
        df = pd.read_parquet(args.input)
        for subdf in chunk_dataframe(df, args.n_workers):
            tasks.append((subdf, args.text_col, args.pos_thr, args.neg_thr))

    elif args.input.endswith(".jsonl"):
        # stream JSONL in batches
        for batch_df in read_jsonl_in_chunks(args.input, args.chunksize):
            tasks.append((batch_df, args.text_col, args.pos_thr, args.neg_thr))
    else:
        raise ValueError("Input must be .parquet or .jsonl")

    # map tasks to workers
    results = pool.map(process_chunk, tasks)
    pool.close()
    pool.join()

    # concatenate all chunks and write out
    df_out = pd.concat(results, ignore_index=True)
    df_out.to_parquet(args.output, index=False, compression="zstd")
    print(f"Wrote {len(df_out)} rows with VADER sentiment to {args.output}")

if __name__ == "__main__":
    main()