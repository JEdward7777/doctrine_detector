from do_detection import extract_grade, read_json
import generate_markdown


def main():
    grading_models = read_json( 'model_jobs.json')['grading_models']
    answer_model__question__answer_grade_comment = generate_markdown.load_results_with_grades(read_json( 'model_jobs.json')['grading_models'])

    for answer_model_label, question__answer_grade_comment in answer_model__question__answer_grade_comment.items():
        for question_label, answer_grade_comment in question__answer_grade_comment.items():
            for grader_label, grade_info in answer_grade_comment["grades"].items():
                grade = grade_info['grade']
                grade_comment = grade_info['grade_comment']

                new_grade,_ = extract_grade( grade_comment )

                if new_grade != grade:
                    print( "=======")
                    print( grade_comment )
                    print( f"\n\nOld grade {grade}\nNew grade {new_grade}")

                    print( "hi" )

if __name__ == "__main__": main()