import json
from do_detection import read_json
import generate_markdown

#any csv which would be nice to be graphed in a spreadsheet can be generated in here.
def main():
    answer_model__question__answer_grade_comment = generate_markdown.load_results_with_grades(read_json( 'model_jobs.json')['grading_models'])


    #I want to see how similar each grade of the different grader models are to each other so I am going to generate a csv which
    #has as columns the different grading models and then per for each answer which was given a grade.

    grade_model_labels = []
    for answer_model_label, question__answer_grade_comment in answer_model__question__answer_grade_comment.items():
        for question_label, answer_grade_comment in question__answer_grade_comment.items():
            for grader_model_label, grade in answer_grade_comment["grades"].items():
                if grader_model_label not in grade_model_labels:
                    grade_model_labels.append( grader_model_label )
                
    with open( "graders_vs_grades.csv", "wt" ) as fout:
        fout.write( ",".join( ["Question"] + grade_model_labels ) + "\n" )
        for answer_model_label, question__answer_grade_comment in answer_model__question__answer_grade_comment.items():
            for question_label, answer_grade_comment in question__answer_grade_comment.items():
                grades = []
                for grade_model_label in grade_model_labels:
                    this_grade = answer_grade_comment["grades"][grade_model_label]['grade']
                    grades.append( f"{this_grade}" )
                fout.write( ",".join( [(question_label + " answered by " + answer_model_label).replace(',', ' ')] + grades ) + "\n" )


    #I want to figure out if different models are biased to themselves so I am going to print out a matrix of models answerers vs model graders.
    with open( "answerers_vs_graders.csv", "wt" ) as fout:
        fout.write( ",".join( ['Answerer'] + grade_model_labels ) + "\n" )
        for answer_model_label, question__answer_grade_comment in answer_model__question__answer_grade_comment.items():
            grades = []
            for grade_model_label in grade_model_labels:
                this_grade = generate_markdown.average_grade( answer_model__question__answer_grade_comment, answer_model_label_search=answer_model_label, grading_model_label_search=grade_model_label )
                grades.append( f"{this_grade}" )
            fout.write( ",".join( [(answer_model_label).replace(',', ' ')] + grades ) + "\n" )



if __name__ == '__main__': 
    main()