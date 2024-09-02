import json
from collections import defaultdict
import os

def get_question_url( question_label ):
    return f"./questions/{question_label}.md".replace( " ", "_" )

def get_answering_models_url( answer_model_label ):
    return f"./answering_models/{answer_model_label}.md".replace( " ", "_" )

def get_answer_url( question_label, answer_model_label ):
    return f"./answers/{answer_model_label}/{question_label}.md".replace( " ", "_" )

def get_index_url():
    return "./index.md"

def get_rel_url( target, base ):
    return os.path.relpath( target, os.path.dirname(base) )

def produce_question_page( question_label, answer_model__answer_grade_comment, question ):
    url = get_question_url( question_label )
    os.makedirs( os.path.dirname(url), exist_ok=True )

    grade_sum = 0
    grade_count = 0
    for answer_model_label, answer_grade_comment in answer_model__answer_grade_comment.items():
        grade_sum += answer_grade_comment['grade']
        grade_count += 1
    grade_average = grade_sum/grade_count

    with open( url, "wt" ) as fout:
        fout.write( f"""
[Index]({get_rel_url(get_index_url(),url)})
# {question_label}
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
        answer_model_labels.sort( key=lambda question_label: answer_model__answer_grade_comment[question_label]["grade"] )

        #for question_label, answer_grade_comment in question__answer_grade_comment.items():
        for answer_model_label in answer_model_labels:
            answer_grade_comment = answer_model__answer_grade_comment[answer_model_label]
            answer_url = get_answer_url( question_label, answer_model_label )
            answer_url_rel = os.path.relpath( answer_url, os.path.dirname(url) )
            grade = answer_grade_comment['grade']

            fout.write( f" * [{grade} {answer_model_label}]({answer_url_rel})\n" )


def produce_answer_model_page( answer_model_label, question__answer_grade_comment, answer_model ):
    url = get_answering_models_url( answer_model_label )
    os.makedirs( os.path.dirname(url), exist_ok=True )

    grade_sum = 0
    grade_count = 0
    for question_label, answer_grade_comment in question__answer_grade_comment.items():
        grade_sum += answer_grade_comment['grade']
        grade_count += 1
    grade_average = grade_sum/grade_count

    with open( url, "wt" ) as fout:
        fout.write( f"""
[Index]({get_rel_url(get_index_url(),url)})
# {answer_model_label}

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
        question_labels.sort( key=lambda question_label: question__answer_grade_comment[question_label]["grade"] )

        #for question_label, answer_grade_comment in question__answer_grade_comment.items():
        for question_label in question_labels:
            answer_grade_comment = question__answer_grade_comment[question_label]
            answer_url = get_answer_url( question_label, answer_model_label )
            answer_url_rel = os.path.relpath( answer_url, os.path.dirname(url) )
            grade = answer_grade_comment['grade']

            fout.write( f" * [{grade}: {question_label}]({answer_url_rel})\n" )

def produce_answer_page( question_label, answer_model_label, answer_grade_comment, question_answer_concern, answer_model ):
    url = get_answer_url( question_label, answer_model_label )
    os.makedirs( os.path.dirname(url), exist_ok=True )

    answer_model_url = get_answering_models_url( answer_model_label )
    answer_model_url_rel = os.path.relpath( answer_model_url, os.path.dirname(url) )

    question_url = get_question_url( question_label )
    question_url_rel = os.path.relpath( question_url, os.path.dirname(url) )


    with open( url, "wt" ) as fout:
        fout.write( f"""
[Index]({get_rel_url(get_index_url(),url)})
# [{answer_model_label}]({answer_model_url_rel}) answer to [{question_label}]({question_url_rel})

## Question [{question_label}]({question_url_rel})
{question_answer_concern["question"]}

## Target answer from notes
{question_answer_concern["answer"]}

## Concern to grade by
{question_answer_concern["concern"]}

## Answer given by [{answer_model_label}]({answer_model_url_rel})
{answer_grade_comment["answer"]}

## Grade
{answer_grade_comment["grade"]}

## Comment given with grade
{answer_grade_comment['grade_comment']}
""" )

def br( text ):
    #replace \n with <br>
    return text.replace( '\n', '&#10;' ).replace( '|', "&#124;").replace( '"', "&quot;").replace( "'", "&#39;")

def block_quote( indent, text ):
    space = " " * indent
    return f"{space}> " + text.replace( "\n", f"\n{space}> " )


def produce_index_page(question_array,model_array,answer_model__question__answer_grade_comment):
    url = get_index_url()
            
    #Now write the results as a markdown table matrix.
    result = ""
    result += "\n"
    result += "|   |" + "|".join( [ f"[<span title='{br(model_info['system'])}'>{model_info['label']}</span>]({get_rel_url( get_answering_models_url( model_info['label'] ), url )})" for model_info in model_array ] ) + "|\n"
    result += "|---|" + "|".join( [ "---" for model_info in model_array ] ) + "|\n"

    #generate the average grade for each model.
    for model_info in model_array:
        grade_sum = 0
        grade_count = 0
        
        for question in question_array:
            grade_sum += answer_model__question__answer_grade_comment[model_info['label']][question['label']]['grade']
            grade_count += 1
        answer_model__question__answer_grade_comment[model_info['label']]['average_grade'] = grade_sum / grade_count

    result += "|Average Grade|" + "|".join( [ f"{answer_model__question__answer_grade_comment[model_info['label']]['average_grade']:.1f}" for model_info in model_array ] ) + "|\n"
    
    for question in question_array:
        question_result_array = []

        for model_info in model_array:
            answer_model_label = model_info['label']
            grade = answer_model__question__answer_grade_comment[answer_model_label][question['label']]['grade']

            #output a cell with color going from green to red where 100 is green 
            #and 0 is red with a span title showing the grade_comment and the text being the score.
            html_color_code = f"style='color:rgb({int(255*(1-grade/100))},{int(255*grade/100)},0)'"

            

            #question_result_array.append( "<span title='" + br(answer_model__question__answer_grade_comment[answer_model_label][question['label']]['grade_comment'] + '\n\nModel Answer: ' + answer_model__question__answer_grade_comment[model_info['label']][question['label']]['answer']) + "' " + html_color_code + ">" + str(int(grade)) + "</span>" )
            question_result_array.append( "[<span " + html_color_code + ">" + str(int(grade)) + f"</span>]({get_rel_url(get_answer_url(question['label'],answer_model_label),url)})" )
            
        result += f"|[<span title='{br(question['question'])}'>{question['label']}</span>]({get_rel_url(get_question_url(question['label']),url)})|" + "|".join( question_result_array ) + "|\n"  

    result += "\n\n"
    result += "## Translation Concerns\n\n"

    for model_info in model_array:
        worst_concern = None
        worst_grade = 100
        worst_question = None
        for question in question_array:
            grade = answer_model__question__answer_grade_comment[model_info['label']][question['label']]['grade']
            if grade < worst_grade:
                worst_concern = answer_model__question__answer_grade_comment[model_info['label']][question['label']]['grade_comment']
                worst_question = question
                worst_grade = grade

        result += "\n"
        result += f"* [{model_info['label']}'s]({get_rel_url(get_answering_models_url(model_info['label']),url)}) worse response:\n"
        result += f"  + Question Label: [{worst_question['label']}]({get_rel_url(get_answer_url(worst_question['label'],model_info['label']),url)})\n"
        result += f"  + Grade: {worst_grade}\n"
        result += f"  + Model's answer:\n"
        result += f"{block_quote(4,answer_model__question__answer_grade_comment[model_info['label']][worst_question['label']]['answer'])}\n"
        result += f"  + Reference Answer:\n"
        result += f"{block_quote(4,worst_question['answer'])}\n"
        result += f"  + Concern:\n"
        result += f"{block_quote(4,worst_concern)}\n"

    with open(url, 'w') as f:
        f.write(result)


def main():
    with open( "results.json", "rt" ) as fin:
        answer_model__question__answer_grade_comment = json.load(fin)

    #flip the structure for convenience
    question__answer_model__answer_grade_comment = defaultdict( lambda: {} )
    for answer_model_label, question__answer_grade_comment in answer_model__question__answer_grade_comment.items():
        for question_label, answer_grade_comment in question__answer_grade_comment.items():
            question__answer_model__answer_grade_comment[question_label][answer_model_label] = answer_grade_comment
                   
    with open( "content.json", "rt" ) as fin:
        question_array = json.load(fin)

    question__question_answer_concern = {}
    for question in question_array:
        question__question_answer_concern[question["label"]] = question

    with open( "models.json", "rt" ) as fin:
        model_array = json.load(fin)

    answer_model__answer_model = {}
    for model in model_array:
        answer_model__answer_model[model["label"]] = model

    #question page.
    for question_label, answer_model__answer_grade_comment in question__answer_model__answer_grade_comment.items():
        produce_question_page( question_label, answer_model__answer_grade_comment, question__question_answer_concern[question_label] )

    #answer model page.
    for answer_model_label, question__answer_grade_comment in answer_model__question__answer_grade_comment.items():
        produce_answer_model_page( answer_model_label, question__answer_grade_comment, answer_model__answer_model[answer_model_label] )

    #answer page
    for question_label, answer_model__answer_grade_comment in question__answer_model__answer_grade_comment.items():
        for answer_model_label, answer_grade_comment in answer_model__answer_grade_comment.items():
            produce_answer_page( question_label, answer_model_label, answer_grade_comment, question__question_answer_concern[question_label], answer_model__answer_model[answer_model_label] )

    #index page.
    produce_index_page(question_array,model_array,answer_model__question__answer_grade_comment)

if __name__ == "__main__":
    main()