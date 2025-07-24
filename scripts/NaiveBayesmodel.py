import pandas as pd
import json
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report, accuracy_score

# Load and flatten the data
def load_and_flatten_label_studio_data(json_file_path):
    texts = []
    labels = []
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for item in data:
        post_text = item['data']['text']
        if item.get('annotations') and item['annotations'][0].get('result'):
            for result_item in item['annotations'][0]['result']:
                if result_item.get('from_name') == 'sentiment' and result_item.get('type') == 'choices':
                    chosen_sentiment = result_item['value']['choices'][0]
                    texts.append(post_text)
                    labels.append(chosen_sentiment)
                    break

    return pd.DataFrame({'text': texts, 'label': labels})

# Load data
df = load_and_flatten_label_studio_data('labeled_keto_data.json')

# Label encoding
label_map_to_int = {
    'positive': 1,
    'neutral': 2,
    'negative': 3,
    'offtopic': 4
}
df['label'] = df['label'].map(label_map_to_int)
df.dropna(subset=['label'], inplace=True)
df['label'] = df['label'].astype(int)

# Prepare text
df['text'] = df['text'].astype(str)
X_train, X_test, y_train, y_test = train_test_split(df['text'], df['label'], test_size=0.2, random_state=42)

# TF-IDF vectorization
vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# Train Naive Bayes
nb_model = MultinomialNB()
nb_model.fit(X_train_vec, y_train)

# Evaluate
y_pred = nb_model.predict(X_test_vec)

target_names = ['positive', 'neutral', 'negative', 'offtopic']
print("Accuracy:", accuracy_score(y_test, y_pred))
print("Classification Report:\n", classification_report(y_test, y_pred, target_names=target_names))



#Confusion matrix :

from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

cm = confusion_matrix(y_test, y_pred)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['positive', 'neutral', 'negative', 'offtopic'])
disp.plot(cmap=plt.cm.Blues)
plt.title("Confusion Matrix")
plt.show()
