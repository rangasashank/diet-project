import pandas as pd
import json # Import the json library


def labeled_json_to_df(json_file_path) -> pd.DataFrame:
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
# df = load_and_flatten_label_studio_data('./scripts/labeled_keto_data.json')

