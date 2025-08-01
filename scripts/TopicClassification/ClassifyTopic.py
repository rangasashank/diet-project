import ndjson
from typing import Dict
import os
import json



class Classifier:
    
    def __init__(self, file_path:str):
        pass

    def regularize_json_file(json_file_path):
        with open(json_file_path) as json_file:
            json_dict = ndjson.load(json_file)
        
        pass

    pass



def regularize_json_file(json_file_path:str, json_output_file_path:str):
    diet_subs_list = ["keto", "intermittentfasting", "plantbaseddiet", "vegan", "vegetarian"]
    diet_subs_set = set(diet_subs_list)
    json_list:list
    # print(json_file_path)
    # return

    # First clear out the output file:
    with open(json_output_file_path, 'w') as ndjson_output_file:
        pass
    # next read the input file line by line and make the conversions
    with open(json_file_path, 'rb') as json_file, open(json_output_file_path, 'a') as json_output_file:        
        json_list:list = []
        writer = ndjson.writer(json_output_file)
        # json_list:list = ndjson.load(json_file)

        for line in json_file:
            json_element:Dict =json.loads(line.strip())

        # for i in range(0, len(json_list)):
            # json_element:Dict = json_list[i]
            subreddit:str = json_element.get("subreddit")
            
            if subreddit is not None:
                    subreddit = subreddit.lower()
                    if subreddit  in diet_subs_set:
                        if subreddit in set(["plantbaseddiet", "vegan", "vegetarian"]):
                            json_element["topic"] = "plantbaseddiet"
                        else:
                              json_element["topic"] = subreddit
                    else:
                        json_element["topic"] = "none"    
            # ndjson.dump(json_element, json_output_file)
            writer.writerow(json_element)
            # json_list.append(json_element) 

            # if subreddit.lower() not in diet_subs_set
            
            pass
    # with open(json_file_path, 'w') as ndjson_output_file:

    #     ndjson.dump(json_list, ndjson_output_file)
            

        # print(json_list)
        # pass

base_input_dir = 'C:\\Users\\Kelly\\Desktop\\diet-project\\raw'
base_output_dir = 'C:\\Users\\Kelly\\Desktop\\diet-project\\raw_output'
for entry in os.listdir(base_input_dir):
    input_full_path = os.path.join(base_input_dir, entry)
    output_full_path = os.path.join(base_output_dir, entry+"_out")
    print(entry)
    regularize_json_file(input_full_path,output_full_path)

# regularize_json_file("C:\\Users\\Kelly\\Desktop\\diet-project\\raw\\pokemoncards_submissions", "C:\\Users\\Kelly\\Desktop\\diet-project\\raw_output\\pokemoncard_submissions_out")
# for 

