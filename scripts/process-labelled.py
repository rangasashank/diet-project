import json

def filter_labelled_data(input_file_path, output_file_path):
    """
    Filters a JSON file to include only entries with a valid sentiment label.

    Args:
        input_file_path (str): The path to the input JSON file.
        output_file_path (str): The path where the filtered JSON data will be saved.
    """
    labelled_data = []
    valid_labels = ["positive", "negative", "neutral", "off-topic"]

    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_file_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {input_file_path}. Check file format.")
        return

    for entry in data:
        sentiment_found = False
        if 'annotations' in entry and entry['annotations']:
            for annotation in entry['annotations']:
                if 'result' in annotation and annotation['result']:
                    for result_item in annotation['result']:
                        if 'value' in result_item and 'choices' in result_item['value']:
                            # Assuming sentiment is the first choice in the list if multiple exist
                            if result_item['from_name'] == 'sentiment' and result_item['value']['choices']:
                                sentiment_value = result_item['value']['choices'][0]
                                if sentiment_value in valid_labels:
                                    labelled_data.append(entry)
                                    sentiment_found = True
                                    break # Move to the next entry once a valid sentiment is found
                if sentiment_found:
                    break # Break from inner loop as well

    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(labelled_data, f, indent=4)
        print(f"Filtered data saved to {output_file_path}")
    except IOError:
        print(f"Error: Could not write to output file at {output_file_path}")

# --- How to use the script ---
# Replace 'your_input_file.json' with the actual path to your uploaded JSON file.
# Replace 'output_labelled_data.json' with your desired output file name.
input_json_file = './scripts/project-3-at-2025-07-25-01-13-e58b7b9c.json'
output_json_file = './exports/output_labelled_data.json'

filter_labelled_data(input_json_file, output_json_file)