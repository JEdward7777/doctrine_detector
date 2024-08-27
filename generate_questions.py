import json
import os
import time
import do_detection

def main():

    keys = do_detection.read_json( 'keys.json' )
    answer_generating_model_info = do_detection.read_json( 'model_jobs.json' )['question_generating_model']
    question_generating_model = do_detection.load_model( answer_generating_model_info, keys )
    content = do_detection.read_json('content.json')

    existing_labels = [question['label'] for question in content]

    #iterate through all the markdown files in data/uW_tw and add questions to content.json
    selected_dir = "data/uW_tw/bible/kt/"
    for filename in os.listdir(selected_dir):
        if filename.endswith(".md"):
            with open(os.path.join(selected_dir, filename), "r") as f:
                markdown = f.read()

                prompt = f"""
The following is the file {filename}.
```
{markdown}
```

Please extract 1 to 3 Christian questions based on the content of the file. The questions should be as specific as possible.
The output should be in json format with the following structure:

```json
[
    {{
        "label": "<label>",
        "question": "<question>",
        "answer": "<answer>",
        "concern": "<concern>"
    }},
    ...
]
```
""".strip()

                valid_result = False
                while not valid_result:

                    result = question_generating_model( prompt )
                    try:
                        result_json = json.loads(result)
                        #test if result_json is a dictionary.  If it is, then see if it only has one key, and it if does grab that and loop.
                        while isinstance(result_json, dict) and len(result_json) == 1:
                            print( f"result_json is a dictionary with only one key \"{list(result_json.keys())[0]}\".  Looping through it..." )
                            result_json = result_json[list(result_json.keys())[0]]
                        if isinstance(result_json, dict) and "label" in result_json and "question" in result_json:
                            #looks like one answer was returned, so wrap it in a list.
                            result_json = [result_json]
                        for question in result_json:
                            #first make sure the label is unique
                            if question['label'] in existing_labels:
                                number_suffix = 2
                                while f"{question['label']} {number_suffix}" in existing_labels:
                                    number_suffix += 1
                                question['label'] = f"{question['label']} {number_suffix}"

                            print( f"Generated question \"{question['label']}\":\nQ: {question['question']}\nA: {question['answer']}\nC: {question['concern']}" )
                            valid_result = True

                            content.append(question)
                            existing_labels.append(question['label'])
                    except Exception as e:
                        print(e)
                        print("Invalid result. Retrying...")
                        time.sleep( 5 ) #sleep so that we can see that there is a problem and not burn up all the credits.

    with open( "content.json", 'w' ) as f:
        json.dump( content, f, indent=4 )

if __name__ == "__main__":
    main()