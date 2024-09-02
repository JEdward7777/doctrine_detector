import json, os
from collections import defaultdict

def main():
    with open( "results.json", "rt" ) as fin:
        results = json.load(fin)

    results_new = defaultdict( lambda: defaultdict( lambda: {} ))
    for model_label, question__answer_grade_comment in results.items():
        for question_label, answer_grade_comment in question__answer_grade_comment.items():
            results_new[model_label][question_label] = {
                "answer": answer_grade_comment["answer"],
                "grades": {
                    "openai_gpt-3.5-turbo_1": {
                        "grade": answer_grade_comment["grade"],
                        "grade_comment": answer_grade_comment["grade_comment"]
                    }
                }
            }

            
    with open( "results.json~", 'w' ) as f:
        #json.dump( results, f, indent=2 )
        f.write( json.dumps( results_new, indent=2 ) )
    #now move the file
    os.replace( "results.json~", "results.json" )

if __name__ == "__main__":
    main()