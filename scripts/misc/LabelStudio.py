import json
from pandas import DataFrame
class LabelStudioHelper:
    @staticmethod
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
        df = DataFrame({'text': texts, 'label': labels})
        return df
    