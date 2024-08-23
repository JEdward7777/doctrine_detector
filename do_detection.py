from collections import defaultdict
import json
from openai import OpenAI
import ollama
import re
import time
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
        return json.load(f)
    

def load_model(model_info,keys):
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
        open_ai_key = keys[model_info['key']]
        client = OpenAI(api_key=open_ai_key)
        def openai_completion( question ):
            completion = client.chat.completions.create(
                model=model_info['model'],
                messages=[
                    {"role": "system", "content": model_info['system']},
                    {"role": "user",   "content": question
                    }
                ]
            )
            return completion.choices[0].message.content
        model = openai_completion
    elif model_info['service'] == 'ollama':
        def ollama_completion( question ):
            response = ollama.chat(model=model_info['model'], messages=[
                {"role": "system", "content": model_info['system']},
                {'role': 'user',    'content': question } ])
            return response['message']['content']
        model = ollama_completion

    return model

def grade_response( model, response, answer, concern ):
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

    prompt = f"""
Please grade the following response:
```
{response}
```
based on the following answer:
```
{answer}
```
and the following concern:
```
{concern}
```

The grade should be an integer between 0 and 100 where 0 is the lowest grade and 100 is the highest grade.
Include a comment on the grade.
""".strip()
    
    found_grade = False

    while not found_grade:
    
        result = model( prompt )
        
        #now find the first number in the response and use that as the grade
        number_finder = re.compile(r'[\d\.]+')

        match = number_finder.search( result )
        if match:
            grade = float(match.group(0))
            grade_comment = result
            found_grade = True
        else:
            #sleep so that we can see that there is a problem and not burn up all the credits.
            time.sleep(1)
            print( f"Grade not found in response: '{result}'. Retrying..." )

    return grade, grade_comment

def run_model_tests():
    content = read_json('content.json')
    models = read_json('models.json')
    keys = read_json( 'keys.json' )

    answer_grading_model_info = read_json( 'answer_grading_model.json' )
    answer_grading_model = load_model( answer_grading_model_info, keys )
    
    #results[model][question]
    results = defaultdict(lambda: defaultdict(lambda: {}))
    for model_info in models:
        model = load_model(model_info,keys)

        for question in content:
            result = {}
            results[model_info['label']][question['label']] = result
            print( f"Model {model_info['label']} running question {question['label']}...", end=" " )
            result["answer"] = model( question['question'] )
            print( f"grading..." )
            result["grade"],result["grade_comment"] = grade_response( answer_grading_model, result["answer"], question['answer'], question['concern'] )
            
    with open( "results.json", 'w' ) as f:
        json.dump( results, f, indent=4 )

def br( text ):
    #replace \n with <br>
    return text.replace( '\n', '&#10;' ).replace( '|', "&#124;").replace( '"', "&quot;").replace( "'", "&#39;")

def block_quote( indent, text ):
    space = " " * indent
    return f"{space}> " + text.replace( "\n", f"\n{space}> " )

def write_results_to_markdown():
    content = read_json('content.json')
    models = read_json('models.json')
    results = read_json( 'results.json' )
            
    #Now write the results as a markdown table matrix.

    result = ""

    result += "|   |" + "|".join( [ f"<span title='{br(model_info['system'])}'>{model_info['label']}</span>" for model_info in models ] ) + "|\n"
    result += "|---|" + "|".join( [ "---" for model_info in models ] ) + "|\n"

    
    for question in content:
        question_result_array = []

        for model_info in models:
            grade = results[model_info['label']][question['label']]['grade']

            #output a cell with color going from green to red where 100 is green 
            #and 0 is red with a span title showing the grade_comment and the text being the score.
            html_color_code = f"style='color:rgb({int(255*(1-grade/100))},{int(255*grade/100)},0)'"

            # question_result_array.append( 
            #     f"<span title='{
            #         br(
            #             results[model_info['label']][question['label']]['grade_comment'] + 
            #             '\n\nModel Answer: ' + 
            #                results[model_info['label']][question['label']]['answer']
            #         )
            #     }' {html_color_code}>{int(grade)}</span>" )

            question_result_array.append( "<span title='" + br(results[model_info['label']][question['label']]['grade_comment'] + '\n\nModel Answer: ' + results[model_info['label']][question['label']]['answer']) + "' " + html_color_code + ">" + str(int(grade)) + "</span>" )
            
        result += f"|<span title='{br(question['question'])}'>{question['label']}</span>|" + "|".join( question_result_array ) + "|\n"  

    result += "\n\n"
    result += "## Translation Concerns\n\n"

    for model_info in models:
        worst_concern = None
        worst_grade = 100
        worst_question = None
        for question in content:
            grade = results[model_info['label']][question['label']]['grade']
            if grade < worst_grade:
                worst_concern = results[model_info['label']][question['label']]['grade_comment']
                worst_question = question
                worst_grade = grade

        result += "\n"
        result += f"* {model_info['label']}'s worse response:\n"
        result += f"  + Question Label: {worst_question['label']}\n"
        result += f"  + Grade: {worst_grade}\n"
        result += f"  + Model's answer:\n"
        result += f"{block_quote(4,results[model_info['label']][worst_question['label']]['answer'])}\n"
        result += f"  + Reference Answer:\n"
        result += f"{block_quote(4,worst_question['answer'])}\n"
        result += f"  + Concern:\n"
        result += f"{block_quote(4,worst_concern)}\n"

    with open('results.md', 'w') as f:
        f.write(result)


def main():
    #run_model_tests()
    write_results_to_markdown()


if __name__ == "__main__":
    main()