import pandas as pd
import json # Import the json library
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score

# 1. Load your labeled data from JSON
def load_and_flatten_label_studio_data(json_file_path):
    texts = []
    labels = []
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for item in data:
        post_text = item['data']['text']
        # Extract the label from the 'annotations' array
        # Assuming each task has at least one annotation and one result
        if item.get('annotations') and item['annotations'][0].get('result'):
            for result_item in item['annotations'][0]['result']:
                if result_item.get('from_name') == 'sentiment' and result_item.get('type') == 'choices':
                    chosen_sentiment = result_item['value']['choices'][0] # Take the first choice
                    texts.append(post_text)
                    labels.append(chosen_sentiment)
                    break # Assuming only one sentiment label per task

    # Create a DataFrame
    df = pd.DataFrame({'text': texts, 'label': labels})
    return df

# Load data using the new function
df = load_and_flatten_label_studio_data('./scripts/labeled_keto_data.json')

# Map string labels to numerical values for model training
# This mapping must be consistent with your target_names in classification_report
label_map_to_int = {
    'positive': 1,
    'neutral': 2,
    'negative': 3,
    'offtopic': 4
}
df['label'] = df['label'].map(label_map_to_int)

# Filter out any rows where mapping might have failed (e.g., if a label was unexpected)
df.dropna(subset=['label'], inplace=True)
df['label'] = df['label'].astype(int) # Ensure labels are integers

# 2. Preprocess the data (already handled by load_and_flatten_label_studio_data for text type)
df['text'] = df['text'].astype(str)

# 3. Split into training and test sets
X_train, X_test, y_train, y_test = train_test_split(df['text'], df['label'], test_size=0.2, random_state=42)

# 4. Vectorize using TF-IDF
vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# 5. Train the model
model = LogisticRegression(max_iter=1000, class_weight='balanced')  # Use balanced class weights to handle class imbalance
model.fit(X_train_vec, y_train)

# 6. Evaluate the model
y_pred = model.predict(X_test_vec)

# Define target names in the correct order corresponding to your numerical mapping
# This is crucial for the classification report to display correctly
target_names_list = ['positive', 'neutral', 'negative', 'offtopic'] # Ensure this order matches your label_map_to_int values
print("Accuracy:", accuracy_score(y_test, y_pred))
print("Classification Report:\n", classification_report(y_test, y_pred, target_names=target_names_list))

# # Optional: Predict on new data
# def predict_tone(text):
#     vec = vectorizer.transform([text])
#     pred = model.predict(vec)[0]
#     # Reverse map integer prediction back to string label
#     label_map_from_int = {v: k for k, v in label_map_to_int.items()}
#     return label_map_from_int.get(pred, "unknown")

# # Example usage:
# print(predict_tone("I feel awful after eating carbs again."))