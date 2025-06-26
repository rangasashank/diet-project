#!/usr/bin/env python3
import os
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch

def main():
    # Paths
    input_path  = os.path.join("../exports", "train.parquet")
    output_path = os.path.join("../exports", "train_roberta.parquet")

    # 1) Load the dataset
    print(f"Loading dataset from {input_path}…")
    ds = load_dataset("parquet", data_files=input_path, split="train")

    # 2) Prepare tokenizer & model (FP16 on GPU)
    model_name = "cardiffnlp/twitter-roberta-base-sentiment"
    print("Loading tokenizer and model (FP16)…")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
    )
    model = model.to("cuda:0")

    # 3) Build a batched pipeline on device 0
    clf = pipeline(
        "sentiment-analysis",
        model=model,
        tokenizer=tokenizer,
        device=0,          # your GPU
        batch_size=64,     # tune up to fill VRAM
        #batch_size=512, # takes 8.1/12 GB on 4070ti
        truncation=True,
        max_length=512       # ← enforce RoBERTa’s limit
    )

    # 4) Define the mapping function
    def batch_sentiment(batch):
        texts = batch["text"]
        outs  = clf(texts)  # returns list of {"label","score"}
        # attach new fields
        batch["sentiment"]  = [o["label"] for o in outs]
        batch["sent_score"] = [o["score"] for o in outs]
        return batch

    # 5) Map across the dataset (streams batches → pipeline → adds columns)
    print("Running sentiment analysis…")
    ds = ds.map(
        batch_sentiment,
        batched=True,
        batch_size=64,       # match your pipeline batch_size
        #batch_size=512,
        desc="Sentiment → dataset"
    )

    # 6) Save augmented dataset back to Parquet
    print(f"Saving to {output_path}…")
    ds.to_parquet(output_path)
    print("Done! ✅")

if __name__ == "__main__":
    main()