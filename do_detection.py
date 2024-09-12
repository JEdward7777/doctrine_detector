from collections import defaultdict
import os
import pyjson5 as json5
import json
from openai import OpenAI
import ollama
import re
import time


def remove_chars_bad_for_filename(in_string):
    bad_chars = ['<', '>', ':', '"', '|', '?', '*', ' ', '`', '’', "'"]
    for char in bad_chars:
        in_string = in_string.replace(char, '_')
    return in_string

def get_grade_json( question_label, answer_model_label, grading_model_label ):
    return remove_chars_bad_for_filename(f"./results/answers/{answer_model_label}/{question_label}_grades/{grading_model_label}.json")

def read_json( filename):
    """
    Reads a json file from disk and returns the loaded data as a python
    object.

    Parameters
    ----------
    filename : str
        The name of the file to read

    Returns
    -------
    data : object
        The loaded data from the file
    """
    with open(filename, 'r') as f:
        return json5.load(f)
        #return json.load(f)
    

def load_model(model_info,connections):
    """
    Loads a model from a service such as openai or ollama.

    Parameters
    ----------
    model_info : dict
        A dictionary containing information about the model to be loaded.
        The dictionary should contain the following keys:
            - key: The key to use for the model. This key should be in
                   the keys dictionary.
            - model: The name of the model to load.
            - system: The system message to pass to the model.
            - service: The name of the service to use to load the model.
                      This should be either 'openai' or 'ollama'.
    keys : dict
        A dictionary containing the keys to use for the models. The keys
        should be the names of the models, and the values should be the
        keys to use for the models.

    Returns
    -------
    model : callable
        A callable that takes a string as input and returns a string as
        output. This callable should be used to ask the model questions.
    """
    model = None
    if model_info['service'] == 'openai':
        open_ai_key = connections[model_info['key']]['key']
        client = OpenAI(api_key=open_ai_key)
        def openai_completion( question ):
            if "response_format" not in model_info:
                completion = client.chat.completions.create(
                    model=model_info['model'],
                    messages=[
                        {"role": "system", "content": model_info['system']},
                        {"role": "user",   "content": question
                        }
                    ]
                )
            else:
                completion = client.chat.completions.create(
                    model=model_info['model'],
                    response_format=model_info['response_format'],
                    messages=[
                        {"role": "system", "content": model_info['system']},
                        {"role": "user",   "content": question
                        }
                    ]
                )

            return completion.choices[0].message.content
        model = openai_completion
    elif model_info['service'] == 'ollama':
        ollama_url = connections[model_info.get('key', '') or "ollama"]['host'] or os.getenv('OLLAMA_HOST') or "http://127.0.0.1:11434"
        ollama_client = ollama.Client(ollama_url)

        def ollama_completion( question ):
            response = ollama_client.chat(model=model_info['model'], messages=[
                {"role": "system", "content": model_info['system']},
                {'role': 'user',    'content': question } ])
            return response['message']['content']
        model = ollama_completion

    return model

def grade_response( *, model, question, concern, teacher_answer, student_answer, prompt_template ):
    """
    Grades the response based on the answer and the concern.

    Parameters
    ----------
    model : callable
        A callable that takes a string as input and returns a string as
        output.
    response : str
        The response from the model
    answer : str
        The correct answer
    concern : str
        The concern for which to grade the answer.

    Returns
    -------
    grade : float
        The grade of the response
    grade_comment : str
        A comment on the grade
    """

    default_prompt = """
Please grade the following response:
```
{student_answer}
```
based on the following answer:
```
{teacher_answer}
```
and the following concern:
```
{concern}
```

The grade should be an integer between 0 and 100 where 0 is the lowest grade and 100 is the highest grade.
Include a comment on the grade.
""".strip()
    


    prompt = prompt_template if prompt_template is not None else default_prompt

    prompt = prompt.format( student_answer=student_answer, teacher_answer=teacher_answer, concern=concern, question=question )

    if "{" in prompt: raise Exception( "Unprocessed key in prompt" )
    
    found_grade = False

    while not found_grade:
    
        result = model( prompt )
        try:
            grade, grade_comment = extract_grade(result )
            found_grade = True
        except Exception:
            #sleep so that we can see that there is a problem and not burn up all the credits.
            time.sleep(1)
            print( f"Grade not found in response: '{result}'. Retrying..." )

    return grade, grade_comment

def extract_grade( result ):
        
    #now find the first number in the response and use that as the grade
    number_finder = re.compile(r'\d+(\.\d+)?')

    match = number_finder.search( result )
    if match:
        grade = float(match.group(0))
        grade_comment = result
    else:
        raise Exception( "Grade not found" )
    
    return grade, grade_comment


def run_model_tests():
    content = read_json('content.json')
    models = read_json('models.json')
    connections = read_json( 'connections.json' )

    answer_grading_model_infos = read_json( 'model_jobs.json' )['grading_models']
    grading_models = {}
    for grading_model_label, answer_grading_model_info in answer_grading_model_infos.items():
        grading_models[grading_model_label] = load_model( answer_grading_model_info, connections )
    
    #results[model][question]
    results = defaultdict(lambda: defaultdict(lambda: {}))

    #if results.json already exists load it in.
    try:
        with open( "results.json", 'r' ) as f:
            results_loaded = json.load( f )
            for model_key, model_results in results_loaded.items():
                for question_key, question_results in model_results.items():
                    results[model_key][question_key] = question_results
    except:
        print( "results.json not found. Starting from scratch." )


    for model_info in models:
        model = load_model(model_info,connections)

        for question in content:
            added_something = False

            #shortcut if this question has already been run
            if question['label'] not in results[model_info['label']]:
                result = {}
                results[model_info['label']][question['label']] = result
                print( f"Model {model_info['label']} running question {question['label']}...", end=" " )
                result["answer"] = model( question['question'] )
                added_something = True


            print( f"grading..." )
            for grading_model_label, answer_grading_model in grading_models.items():

                grade_filename = get_grade_json( question['label'], model_info['label'], grading_model_label )

                if not os.path.exists( grade_filename ):
                    with open( grade_filename, 'w' ) as f:
                        graded = False
                        while not graded:
                            try:
                                prompt_template = answer_grading_model_infos[grading_model_label]["prompt_template"] if "prompt_template" in answer_grading_model_infos[grading_model_label] else None
                                grade, comment = grade_response( model=answer_grading_model, student_answer=results[model_info['label']][question['label']]["answer"], question=question['question'], teacher_answer=question['answer'], concern=question['concern'], prompt_template=prompt_template )
                                grade_result = {
                                    "grade": grade,
                                    "grade_comment": comment
                                }
                                graded = True
                            except:
                                print( f"Failed to grade model {grading_model_label} on question {question['label']}" )
                                time.sleep( 5 )

                        f.write( json.dumps( grade_result, indent=2 ) )

            if added_something:
                with open( "results.json~", 'w' ) as f:
                    #json.dump( results, f, indent=2 )
                    f.write( json.dumps( results, indent=2 ) )
                #now move the file
                os.replace( "results.json~", "results.json" )

def br( text ):
    #replace \n with <br>
    return text.replace( '\n', '&#10;' ).replace( '|', "&#124;").replace( '"', "&quot;").replace( "'", "&#39;")

def block_quote( indent, text ):
    space = " " * indent
    return f"{space}> " + text.replace( "\n", f"\n{space}> " )


def main():
    run_model_tests()


if __name__ == "__main__":
    main()