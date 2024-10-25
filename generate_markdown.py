"""
This module generates markdown files for all the questions, and answer models.
This markdown is then used to generate a webpage that shows the results of the
doctrine detector project.

The markdown files are placed in the results directory, and a index.md file is
created that links to all the questions and answer models.
"""

import json
from collections import defaultdict
import os

from do_detection import get_grade_json, remove_chars_bad_for_filename


def get_question_url( question_label ):
    """
    Returns the filename of the markdown file for a given question.

    Parameters
    ----------
    question_label : str
        The label of the question that was asked.

    Returns
    -------
    filename : str
        The filename of the markdown file.
    """
    return remove_chars_bad_for_filename(f"./results/questions/{question_label}.md" )

def get_answering_models_url( answer_model_label ):
    """
    Returns the filename of the markdown file for a given answer model.

    Parameters
    ----------
    answer_model_label : str
        The label of the model that produced the answer.

    Returns
    -------
    filename : str
        The filename of the markdown file.
    """
    return remove_chars_bad_for_filename(f"./results/answering_models/{answer_model_label}.md")

def get_grading_models_url( grading_model_label ):
    """
    Returns the filename of the markdown file for a given grading model.

    Parameters
    ----------
    grading_model_label : str
        The label of the model that produced the grade.

    Returns
    -------
    filename : str
        The filename of the markdown file.
    """
    return remove_chars_bad_for_filename(f"./results/grading_models/{grading_model_label}.md")

def get_answer_url( question_label, answer_model_label ):
    """
    Returns the filename of the markdown file for a given answer.

    Parameters
    ----------
    question_label : str
        The label of the question that was asked.
    answer_model_label : str
        The label of the model that produced the answer.

    Returns
    -------
    filename : str
        The filename of the markdown file.
    """
    return remove_chars_bad_for_filename(f"./results/answers/{answer_model_label}/" +
        f"{question_label}.md")

def get_grade_url( question_label, answer_model_label, grading_model_label ):
    """
    Returns the filename of the markdown file for a given grade.

    Parameters
    ----------
    question_label : str
        The label of the question that was asked.
    answer_model_label : str
        The label of the model that produced the answer.
    grading_model_label : str
        The label of the model that produced the grade.

    Returns
    -------
    filename : str
        The filename of the markdown file.
    """
    return remove_chars_bad_for_filename(f"./results/answers/{answer_model_label}/" +
        f"{question_label}_grades/{grading_model_label}.md")

def get_index_url():
    """
    Returns the filename of the index markdown file.

    Returns
    -------
    filename : str
        The filename of the index markdown file.
    """
    return remove_chars_bad_for_filename("./index.md")

def get_rel_url( target, base ):
    """
    Given a target and base path, returns a relative path from the base path to the target path.

    Parameters
    ----------
    target : str
        The target path.
    base : str
        The base path.

    Returns
    -------
    str
        A relative path from the base path to the target path.
    """
    result = os.path.relpath( target, os.path.dirname(base) )
    if not result.startswith( "." ):
        result = "./" + result
    return result


average_cache_results = {}
def average_grade(answer_model__question__answer_grade_comment, question_label_search=None,
    answer_model_label_search=None, grading_model_label_search=None):
    """
    Calculates the average grade based on the provided search parameters.

    This function utilizes a cache mechanism to store and retrieve the 
    average of grades for specific combinations of answer model labels, 
    question labels, and grading model labels. If the cache is not 
    initialized, it iterates through all grades in the provided data 
    structure to populate the cache.

    Parameters
    ----------
    answer_model__question__answer_grade_comment : dict
        A nested dictionary containing grades for each combination of 
        answer model, question, and grading model.
    question_label_search : str, optional
        The label of the question to search for. Defaults to None.
    answer_model_label_search : str, optional
        The label of the answer model to search for. Defaults to None.
    grading_model_label_search : str, optional
        The label of the grading model to search for. Defaults to None.

    Returns
    -------
    float
        The average grade for the specified search parameters. If no 
        grades are found for the given parameters, returns -1.
    """
    #generate the cache if it isn't done yet.
    if len(average_cache_results) == 0:
        for answer_model_label, question__answer_grade_comment in \
            answer_model__question__answer_grade_comment.items():
            for question_label, answer_grade_comment in question__answer_grade_comment.items():
                for grading_model_label, grade in answer_grade_comment["grades"].items():
                    keys = [
                        f"{answer_model_label},{question_label},{grading_model_label}",
                        f"{answer_model_label},{question_label},None",
                        f"{answer_model_label},None,{grading_model_label}",
                        f"{answer_model_label},None,None",
                        f"None,{question_label},{grading_model_label}",
                        f"None,{question_label},None",
                        f"None,None,{grading_model_label}",
                         "None,None,None",
                    ]

                    for key in keys:
                        if key not in average_cache_results:
                            average_cache_results[key] = {"sum":0,"count":0}

                        average_cache_results[key]["sum"] += grade["grade"]
                        average_cache_results[key]["count"] += 1

    key = f"{answer_model_label_search},{question_label_search},{grading_model_label_search}"
    if key not in average_cache_results:
        return -1
    return average_cache_results[key]["sum"] / average_cache_results[key]["count"]



def produce_question_page( question_label, answer_model__answer_grade_comment, question,
    answer_model__question__answer_grade_comment ):
    """
    Generates a markdown page for the given question label.

    This function writes out a markdown page containing the question,
    answer from notes, concern used for grading, average grade, and grades
    for each answer model. The grades are sorted by the average grade of
    the question.

    Parameters
    ----------
    question_label : str
        The label of the question.
    answer_model__answer_grade_comment : dict
        A nested dictionary containing grades for each combination of answer
        model and question.
    question : dict
        A dictionary containing the question, answer from notes, and concern
        used for grading.
    answer_model__question__answer_grade_comment : dict
        A nested dictionary containing grades for each combination of answer
        model, question, and grading model.

    Returns
    -------
    None
    """
    url = get_question_url( question_label )
    os.makedirs( os.path.dirname(url), exist_ok=True )


    grade_average = average_grade( answer_model__question__answer_grade_comment,
        question_label_search=question_label )

    with open( url, "wt", encoding="utf-8" ) as fout:
        fout.write( f"""
[Index]({get_rel_url(get_index_url(),url)})
# Question {question_label}
## Question
{question["question"]}

## Answer from notes
{question["answer"]}

## Concern used for grading
{question["concern"]}

## Average Grade
{grade_average}

## Grades
""" )

        answer_model_labels = list(answer_model__answer_grade_comment.keys())
        #sort the question_labels based on the grade:
        answer_model_labels.sort( key=lambda answer_model_label: average_grade(
            answer_model__question__answer_grade_comment, question_label_search=question_label,
            answer_model_label_search=answer_model_label ) )

        #for question_label, answer_grade_comment in question__answer_grade_comment.items():
        for answer_model_label in answer_model_labels:
            answer_url = get_answer_url( question_label, answer_model_label )
            answer_url_rel = os.path.relpath( answer_url, os.path.dirname(url) )
            grade = average_grade( answer_model__question__answer_grade_comment,
                question_label_search=question_label, answer_model_label_search=answer_model_label )

            fout.write( f" * [{grade} {answer_model_label}]({answer_url_rel})\n" )


def produce_answer_model_page( answer_model_label, question__answer_grade_comment, answer_model,
    answer_model__question__answer_grade_comment, question_array ):
    """
    Generates a markdown page for the given answer model label.

    This function writes out a markdown page containing the answer model's
    service, model, system prompt, average grade, and grades for each question.
    The grades are sorted by the average grade of the question. The function also
    writes out the result for the worse grade for this model.

    Parameters
    ----------
    answer_model_label : str
        The label of the answer model.
    question__answer_grade_comment : dict
        A nested dictionary containing grades for each combination of question
        and answer model.
    answer_model : dict
        A dictionary containing the answer model's service, model, and system
        prompt.
    answer_model__question__answer_grade_comment : dict
        A nested dictionary containing grades for each combination of answer
        model, question, and grading model.
    question_array : list
        A list of dictionaries containing the questions. Each dictionary contains
        the question label, question, answer from notes, and concern used for
        grading.

    Returns
    -------
    None
    """
    url = get_answering_models_url( answer_model_label )
    os.makedirs( os.path.dirname(url), exist_ok=True )

    grade_average = average_grade( answer_model__question__answer_grade_comment,
        answer_model_label_search=answer_model_label )

    with open( url, "wt", encoding="utf-8" ) as fout:
        fout.write( f"""
[Index]({get_rel_url(get_index_url(),url)})
# Answering Model {answer_model_label}

## Service
{answer_model['service']}

## Model
{answer_model['model']}

## System prompt
{answer_model['system']}

## Average Grade
{grade_average}

## Grades:
""" )
        question_labels = list(question__answer_grade_comment.keys())
        #sort the question_labels based on the grade:
        question_labels.sort( key=lambda question_label: average_grade(
            answer_model__question__answer_grade_comment, question_label_search=question_label,
            answer_model_label_search=answer_model_label ) )

        #for question_label, answer_grade_comment in question__answer_grade_comment.items():
        for question_label in question_labels:
            answer_url = get_answer_url( question_label, answer_model_label )
            answer_url_rel = os.path.relpath( answer_url, os.path.dirname(url) )
            grade = average_grade( answer_model__question__answer_grade_comment,
                question_label_search=question_label, answer_model_label_search=answer_model_label )

            fout.write( f" * [{grade}: {question_label}]({answer_url_rel})\n" )


        #now write out the result for the worse grade for this model:
        result = ""
        result += "\n\n"
        result += "## Translation Concerns\n\n"

        worst_concern = None
        worst_grade = 100
        worst_question = None
        for question in question_array:
            grade = average_grade( answer_model__question__answer_grade_comment,
                question_label_search=question['label'], answer_model_label_search=
                answer_model['label'] )
            if grade < worst_grade:
                worst_sub_grade = 100
                for grade_object in answer_model__question__answer_grade_comment[answer_model
                    ['label']][question['label']]["grades"].values():
                    if grade_object['grade'] < worst_sub_grade:
                        worst_sub_grade = grade_object['grade']
                        worst_concern = grade_object['grade_comment']
                worst_question = question
                worst_grade = grade

        result += "\n"
        result += f"* [{answer_model['label']}'s]({get_rel_url(get_answering_models_url(
            answer_model['label']),url)}) worse response:\n"
        result += f"  + Question Label: [{worst_question['label']}]({get_rel_url(get_answer_url(
            worst_question['label'],answer_model['label']),url)})\n"
        result += f"  + Grade: {worst_grade}\n"
        result +=  "  + Model's answer:\n"
        result += f"{block_quote(4,answer_model__question__answer_grade_comment[answer_model \
            ['label']][worst_question['label']]['answer'])}\n"
        result +=  "  + Reference Answer:\n"
        result += f"{block_quote(4,worst_question['answer'])}\n"
        result +=  "  + Concern:\n"
        result += f"{block_quote(4,worst_concern)}\n"

        fout.write(result)

def produce_answer_page( question_label, answer_model_label, answer_grade_comment,
    question_answer_concern, answer_model__question__answer_grade_comment ):
    """
    Produce an answer page at the given url that is a markdown table 
    row. The row has a column for each grading model, and a cell for the 
    grade and grade comment for each grading model.

    The page also includes a link to each grading model and question.
    """
    url = get_answer_url( question_label, answer_model_label )
    os.makedirs( os.path.dirname(url), exist_ok=True )

    answer_model_url = get_answering_models_url( answer_model_label )
    answer_model_url_rel = os.path.relpath( answer_model_url, os.path.dirname(url) )

    question_url = get_question_url( question_label )
    question_url_rel = os.path.relpath( question_url, os.path.dirname(url) )


    with open( url, "wt", encoding="utf-8" ) as fout:
        fout.write( f"""
[Index]({get_rel_url(get_index_url(),url)})
# Generated Answer from [{answer_model_label}]({answer_model_url_rel}) for [{question_label}]({
    question_url_rel})

## Question [{question_label}]({question_url_rel})
{question_answer_concern["question"]}

## Target answer from notes
{question_answer_concern["answer"]}

## Concern to grade by
{question_answer_concern["concern"]}

## Answer given by [{answer_model_label}]({answer_model_url_rel})
{answer_grade_comment["answer"]}

## Average Grade
{average_grade( answer_model__question__answer_grade_comment, question_label_search=
    question_label, answer_model_label_search=answer_model_label )}

## Grades
""" )
        for grading_model_label, grade in answer_grade_comment["grades"].items():
            fout.write( f" * [{grade['grade']}]({get_rel_url( get_grade_url( question_label,
                answer_model_label, grading_model_label ), url )}) [{grading_model_label}]" +
                f"({get_rel_url( get_grading_models_url( grading_model_label ), url )})\n" )



        fout.write( f"\n[&lt;- Link to Question]({get_rel_url(get_question_url( question_label ),
            url)})\n" )

def br( text ):
    """
    Replace special characters in a string with their HTML entities.

    Parameters
    ----------
    text : str
        The string to be processed.

    Returns
    -------
    str
        The string with special characters replaced by their HTML entities.
    """
    #replace \n with <br>
    return text.replace( '\n', '&#10;' ).replace( '|', "&#124;").replace( '"', "&quot;") \
        .replace( "'", "&#39;")

def block_quote( indent, text ):
    """
    Formats the given text as a block quote with a specified indent.

    Parameters
    ----------
    indent : int
        The number of spaces to indent the block quote.
    text : str
        The text to be formatted as a block quote.

    Returns
    -------
    str
        The formatted block quoted text.
    """
    space = " " * indent
    return f"{space}> " + text.replace( "\n", f"\n{space}> " )


def produce_index_page(question_array,model_array,answer_model__question__answer_grade_comment):
    """
    Produce an index page at the given url that is a table of models and questions.
    The table has a column for each model, and a row for each question. The cell at the
    intersection of a model and question is a link to the answer page for that model
    and question. The link is colored based on the grade of the answer, with green being
    100 and red being 0. The link also has a title that shows the grade_comment for the
    answer and the answer itself. The grade is also the text of the link.

    The models are sorted by their average grade, so that the model with the highest average
    grade is on the left. The questions are sorted alphabetically by label.

    The page also includes a link to each question and model.
    """
    url = get_index_url()

    #sort the models by their average grade.
    model_array.sort( key=lambda model_info: average_grade(
        answer_model__question__answer_grade_comment, answer_model_label_search=
        model_info['label']))

    #sort the questions by their label so that you can find them better.
    question_array.sort( key=lambda question: question['label'] )

    #Now write the results as a markdown table matrix.
    result = ""
    result += "# Index\n"
    result += "\n"
    result += "|   |" + "|".join( [ f"[<span title='{br(model_info['system'])}'>{model_info
        ['label']}</span>]({get_rel_url( get_answering_models_url( model_info['label'] ), url )
        })" for model_info in model_array ] ) + "|\n"
    result += "|---|" + "|".join( [ "---" for model_info in model_array ] ) + "|\n"



    result += "|Average Grade|" + "|".join( [ f"{average_grade(
        answer_model__question__answer_grade_comment, answer_model_label_search=
        model_info['label'] ):.1f}" for model_info in model_array ] ) + "|\n"
    for question in question_array:
        question_result_array = []

        for model_info in model_array:
            answer_model_label = model_info['label']
            grade = average_grade( answer_model__question__answer_grade_comment,
                question_label_search=question['label'], answer_model_label_search=
                answer_model_label )

            #output a cell with color going from green to red where 100 is green
            #and 0 is red with a span title showing the grade_comment and the text being the score.
            #html_color_code = f"style='color:rgb({int(255*(1-grade/100))},{int(255*grade/100)},0)'"



            #question_result_array.append( "<span title='" + br(
            #    answer_model__question__answer_grade_comment[answer_model_label][
            #    question['label']]['grade_comment'] + '\n\nModel Answer: ' +
            #    answer_model__question__answer_grade_comment[model_info['label']][question
            #    ['label']]['answer']) + "' " + html_color_code + ">" + str(int(grade)) +
            #    "</span>" )
            #question_result_array.append( "[<span " + html_color_code + ">" + str(int(grade)) +
            #     f"</span>]({get_rel_url(get_answer_url(question['label'],answer_model_label),
            #     url)})" )
            question_result_array.append( f"[{grade}]({get_rel_url(get_answer_url(
                question['label'],answer_model_label),url)})" )

        #result += f"|[<span title='{br(question['question'])}'>{question['label']}</span>]({
        #   get_rel_url(get_question_url(question['label']),url)})|" + "|".join(
        #   question_result_array ) + "|\n"
        result += f"|[{question['label']}]({get_rel_url(get_question_url(question['label']),
            url)})|" + "|".join( question_result_array ) + "|\n"


    with open(url, 'w', encoding='utf-8') as f:
        f.write(result)

def produce_grading_model_page( *, answer_model__question__answer_grade_comment,
    grading_model_infos, grading_model_label, question_array, answer_model_infos ):
    url = get_grading_models_url( grading_model_label )
    os.makedirs( os.path.dirname(url), exist_ok=True )


    answer_model_labels = list(answer_model__question__answer_grade_comment.keys())
    answer_model_labels.sort( key=lambda answer_model_label: average_grade(
        answer_model__question__answer_grade_comment, answer_model_label_search=answer_model_label,
        grading_model_label_search=grading_model_label ) )
    question_array.sort( key=lambda question: question['label'] )

    grading_model = grading_model_infos[grading_model_label]

    grade_average = average_grade( answer_model__question__answer_grade_comment,
        grading_model_label_search=grading_model_label )

    with open( url, "wt", encoding="utf-8" ) as fout:
        fout.write( f"""
[Index]({get_rel_url(get_index_url(),url)})
# Grading model {grading_model_label}

## Service
{grading_model['service']}

## Model
{grading_model['model']}

## System prompt
{grading_model['system']}

## Average Grade
{grade_average}

""" )

        #Now write the results as a markdown table matrix.
        result = ""
        result += "\n"
        result += "|   |" + "|".join( [ f"[<span title='{br(answer_model_infos[answer_model_label]
            ['system'])}'>{answer_model_label}</span>]({get_rel_url( get_answering_models_url( 
            answer_model_label ), url )})" for answer_model_label in answer_model_labels ] ) + "|\n"
        result += "|---|" + "|".join( [ "---" for _ in answer_model_labels ] ) + "|\n"



        result += "|Average Grade|" + "|".join( [ f"{average_grade(
            answer_model__question__answer_grade_comment, grading_model_label_search=grading_model_label, answer_model_label_search=answer_model_label ):.1f}" for answer_model_label in answer_model_labels ] ) + "|\n"

        for question in question_array:
            question_result_array = []
            question_label = question['label']

            for answer_model_label in answer_model_labels:
                grade = average_grade( answer_model__question__answer_grade_comment,
                    grading_model_label_search=grading_model_label, question_label_search=
                    question['label'], answer_model_label_search=answer_model_label )

                #output a cell with color going from green to red where 100 is green
                #and 0 is red with a span title showing the grade_comment and the text being the score.
                #html_color_code = f"style='color:rgb({int(255*(1-grade/100))},{int(255*grade/100)},0)'"

                #question_result_array.append( "<span title='" + br(answer_model__question__answer_grade_comment[answer_model_label][question['label']]['grade_comment'] + '\n\nModel Answer: ' + answer_model__question__answer_grade_comment[model_info['label']][question['label']]['answer']) + "' " + html_color_code + ">" + str(int(grade)) + "</span>" )
                #question_result_array.append( "[<span " + html_color_code + ">" + str(int(grade)) + f"</span>]({get_rel_url(get_grade_url(question_label,answer_model_label, grading_model_label),url)})" )
                question_result_array.append( f"[{grade}]({get_rel_url(get_grade_url(
                    question_label,answer_model_label, grading_model_label),url)})" )
            #result += f"|[<span title='{br(question['question'])}'>{question['label']}</span>]({get_rel_url(get_question_url(question_label),url)})|" + "|".join( question_result_array ) + "|\n"
            result += f"|[{question['label']}]({get_rel_url(get_question_url(question_label),
                url)})|" + "|".join( question_result_array ) + "|\n"
            
        
        fout.write( result )

def produce_grade_page( *, answer_model__question__answer_grade_comment, question_label, answer_model_label, grading_model_label, grade, question__question_answer_concern ):
    url = get_grade_url( question_label, answer_model_label, grading_model_label )
    os.makedirs( os.path.dirname(url), exist_ok=True )

    with open( url, "wt", encoding="utf-8" ) as fout:
        fout.write( f"""
[Index]({get_rel_url(get_index_url(),url)})
# Grade of [{grading_model_label}]({get_rel_url(get_grading_models_url(grading_model_label),url)}) for model [{answer_model_label}]({get_rel_url(get_answering_models_url(answer_model_label),url)}) for question [{question_label}]({get_rel_url(get_question_url(question_label),url)})

## Question [{question_label}]({get_rel_url(get_question_url(question_label),url)})
{question__question_answer_concern[question_label]['question']}

## Correct Answer
{question__question_answer_concern[question_label]['answer']}

## Stated Concern
{question__question_answer_concern[question_label]['concern']}

## [Answer]({get_rel_url(get_answer_url(question_label, answer_model_label),url)}) by [{answer_model_label}]({get_rel_url(get_answering_models_url(answer_model_label),url)})
{answer_model__question__answer_grade_comment[answer_model_label][question_label]['answer']}

## Grade by [{grading_model_label}]({get_rel_url(get_grading_models_url(grading_model_label),url)})
{grade['grade']}

## Comment by [{grading_model_label}]({get_rel_url(get_grading_models_url(grading_model_label),url)})
{grade['grade_comment']}

[&lt;- Link to Answer]({get_rel_url(get_answer_url(question_label, answer_model_label),url)})
""" )
        

def load_results_with_grades(grading_model_infos):
    with open( "results.json", "rt", encoding="utf-8" ) as fin:
        answer_model__question__answer = json.load(fin)

        for answer_model_label, question__answer in answer_model__question__answer.items():
            for question_label, answer in question__answer.items():
                answer["grades"] = {}
                for grading_model_label in grading_model_infos.keys():
                    grade_filename = get_grade_json( question_label, answer_model_label, grading_model_label )
                    if os.path.exists( grade_filename ):
                        with open( grade_filename, "rt", encoding="utf-8" ) as fin:
                            grade = json.load(fin)
                            answer["grades"][grading_model_label] = grade
    return answer_model__question__answer


def main():

    with open( 'model_jobs.json', encoding="utf-8" ) as fin:
        grading_model_infos = json.load(fin)['grading_models']

    answer_model__question__answer_grade_comment = load_results_with_grades(grading_model_infos)

    #flip the structure for convenience
    question__answer_model__answer_grade_comment = defaultdict( lambda: {} )
    for answer_model_label, question__answer_grade_comment in answer_model__question__answer_grade_comment.items():
        for question_label, answer_grade_comment in question__answer_grade_comment.items():
            question__answer_model__answer_grade_comment[question_label][answer_model_label] = answer_grade_comment

    grading_model__question__answer_model__grade = defaultdict( lambda: defaultdict(lambda: defaultdict(lambda:{})))
    for answer_model_label, question__answer_grade_comment in answer_model__question__answer_grade_comment.items():
        for question_label, answer_grade_comment in question__answer_grade_comment.items():
            for grading_model_label, grade in answer_grade_comment["grades"].items():
                grading_model__question__answer_model__grade[grading_model_label][question_label][answer_model_label] = grade

                   
    with open( "content.json", "rt", encoding="utf-8" ) as fin:
        question_array = json.load(fin)

    question__question_answer_concern = {}
    for question in question_array:
        question__question_answer_concern[question["label"]] = question

    with open( "models.json", "rt", encoding="utf-8" ) as fin:
        model_array = json.load(fin)

    answer_model__answer_model = {}
    for model in model_array:
        answer_model__answer_model[model["label"]] = model


    #grading model page
    for grading_model_label, question__answer_model__grade in \
        grading_model__question__answer_model__grade.items():
        produce_grading_model_page( answer_model__question__answer_grade_comment=
            answer_model__question__answer_grade_comment, grading_model_infos=grading_model_infos,
            grading_model_label=grading_model_label, question_array=question_array,
            answer_model_infos=answer_model__answer_model )

    #now produce grade comments.
    for grading_model_label, question__answer_model__grade in \
        grading_model__question__answer_model__grade.items():
        for question_label, answer_model__grade in question__answer_model__grade.items():
            for answer_model_label, grade in answer_model__grade.items():
                produce_grade_page( answer_model__question__answer_grade_comment=
                    answer_model__question__answer_grade_comment, question_label=question_label,
                    answer_model_label=answer_model_label, grading_model_label=grading_model_label,
                    grade=grade, question__question_answer_concern=
                    question__question_answer_concern )

    #question page.
    for question_label, answer_model__answer_grade_comment in \
        question__answer_model__answer_grade_comment.items():
        produce_question_page( question_label, answer_model__answer_grade_comment,
        question__question_answer_concern[question_label], answer_model__question__answer_grade_comment=answer_model__question__answer_grade_comment )

    #answer model page.
    for answer_model_label, question__answer_grade_comment in answer_model__question__answer_grade_comment.items():
        produce_answer_model_page( answer_model_label, question__answer_grade_comment,
            answer_model__answer_model[answer_model_label],
            answer_model__question__answer_grade_comment, question_array=question_array )

    #answer page
    for question_label, answer_model__answer_grade_comment in \
        question__answer_model__answer_grade_comment.items():
        for answer_model_label, answer_grade_comment in answer_model__answer_grade_comment.items():
            produce_answer_page( question_label, answer_model_label, answer_grade_comment,
                question__question_answer_concern[question_label], answer_model__question__answer_grade_comment )


    #index page.
    produce_index_page(question_array,model_array,answer_model__question__answer_grade_comment)

if __name__ == "__main__":
    main()
