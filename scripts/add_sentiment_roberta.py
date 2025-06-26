from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

ds = load_dataset("parquet", data_files="../exports/train.parquet", split="train")

tok = AutoTokenizer.from_pretrained("cardiffnlp/twitter-roberta-base-sentiment")
clf = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment", tokenizer=tok, device=0)

def add_sentiment(batch):
    outs = clf(batch["text"], truncation=True, max_length=512)
    batch["sentiment"] = [o["label"] for o in outs]
    batch["sent_score"] = [o["score"] for o in outs]
    return batch

ds = ds.map(add_sentiment, batched=True, batch_size=32)
ds.to_parquet("../exports/train_roberta.parquet")