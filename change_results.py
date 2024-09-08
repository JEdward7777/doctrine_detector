import json
import os

from do_detection import get_grade_json

def main():
    with open( "results.json", 'r' ) as f:
        answer_model__question__answer_grade_comment = json.load(f)

    for answer_model_label, question__answer_grade_comment in answer_model__question__answer_grade_comment.items():
        for question_label, answer_grade_comment in question__answer_grade_comment.items():
            for grading_model_label, grade in answer_grade_comment["grades"].items():
                output_file = get_grade_json( question_label, answer_model_label, grading_model_label )
                with open( output_file, 'wt' ) as f:
                    json.dump( grade, f, indent=2 )

            del answer_model__question__answer_grade_comment[answer_model_label][question_label]["grades"]

    with open( "results.json", 'w' ) as f:
        json.dump( answer_model__question__answer_grade_comment, f, indent=2 )

if __name__ == "__main__":
    main()