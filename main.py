import lexer
from lexer import Lexer
from parser import parse_slr_table, Parser
import type_checker
from type_checker import SemanticAnalyzer
import evaluation
import sys
import json

# WARNING:
# - You are not allowed to use any external libraries other than the standard library
# - Please do not modify the file name of the entry file 'main.py'
# - Our autograder will test your code by runing 'python main.py <test_file>'
#   The current directory will be the same directory as the entry file
#   So please make sure your import statement is correct

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python main.py <test_file>")
        sys.exit(1)

    file_name = sys.argv[1]

    action_table, goto_table = parse_slr_table("SLR Parsing Table.csv")

    with open(file_name, 'r') as f:
        # read file to string
        source_code = f.read()
        # your implementation

        # lexical
        tokens = Lexer(source_code)
        # get the tokens and write it to a file
        with open("lexer_out.json", "w") as json_file:
            json.dump(tokens, json_file, indent=2)

        # parse
        parser = Parser(action_table, goto_table)
        syntax_tree = parser.parse(tokens)

        # retrieve the syntax tree in JSON format and write it to a file
        with open('parser_out.json', 'w') as f:
            json.dump(syntax_tree.to_dict(), f, separators=(',', ':'))

        # type checking
        analyzer = SemanticAnalyzer(syntax_tree)
        if analyzer.type_check():
            # get the syntax tree and write it to a file
            analyzer.write_typing_out("typing_out.json")
        else:
            print("Type error detected!")

    # evaluate
    if syntax_tree:
        evaluation_analyzer = evaluation.Evaluaion(syntax_tree, type_checker.SymbolTable)
        print(type_checker.SymbolTable)
        evaluation_analyzer.evaluation(evaluation_analyzer.syntax_tree)

        try:
            # retrieve the syntax tree in JSON format and write it to a file
            with open('evaluation_out.json', 'w', encoding='utf-8') as json_file:
                if not evaluation_analyzer.error:
                    json_file.write(evaluation_analyzer.to_json_format_value())
                    print("\nevaluation Analysis Result written to 'evaluation_out.json'")
                else:
                    json_file.write("{}")
                    print("\nevaluation Analysis failed. Empty JSON written to 'evaluation_out.json'")
        except Exception as e:
            print(f"Error writing to evaluation_out.json: {e}")
    else:
        with open('evaluation_out.json', 'w', encoding='utf-8') as json_file:
            json_file.write("{}")
        print("\nevaluation Analysis failed. Empty JSON written to 'evaluation_out.json'")
        exit(1)
