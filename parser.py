import csv
import sys
import json
from lexer import process_input

def parse_slr_table(file_path):
    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        lines = list(reader)  # Read all rows

    # Extract header and symbol rows
    header_fields = [field.strip() for field in lines[0]]
    symbols = [field.strip() for field in lines[1]]

    # Correct the state name
    if symbols[0] == "":
        symbols[0] = "state"

    # Determine the column range for action and goto
    try:
        action_index = header_fields.index("action")
        goto_index = header_fields.index("goto")
    except ValueError:
        raise ValueError("The CSV file is missing the 'action' or 'goto' column headings.")

    action_symbols = symbols[action_index:goto_index]
    goto_symbols = symbols[goto_index + 1:]

    # Initialize ACTION and GOTO tables
    action_table = {}
    goto_table = {}

    # Traverse data rows
    for row in lines[2:]:
        if not row[0].strip():  # Skip blank lines
            continue

        try:
            state = int(row[0].strip())  # Analyze status number
        except ValueError:
            continue

        # Initialize the table entries in the current state
        action_table[state] = {
            symbols[idx]: value.strip()
            for idx, value in enumerate(row[action_index:goto_index], start=action_index)
            if value.strip()
        }

        goto_table[state] = {
            symbols[idx]: int(value.strip())
            for idx, value in enumerate(row[goto_index + 1:], start=goto_index + 1)
            if value.strip().isdigit()
        }

    return action_table, goto_table


class Parser:
    def __init__(self, action_table, goto_table):
        self.action_table = action_table
        self.goto_table = goto_table
        self.stack = [0]  # Initialize stack, including state 0
        self.syntax_tree = None  # Grammar Tree Root Node

        # grammar rule
        self.grammar_rules = [
            ("S'", ["S"]),
            ("S", ["D'", "C", "."]),
            ("S", ["C", "."]),
            ("D'", ["D", "D'"]),
            ("D'", ["D"]),
            ("D", ["let", "T", "id", "be", "E", "."]),
            ("T", ["int"]),
            ("T", ["set"]),
            ("E", ["E'"]),
            ("E", ["E", "U", "E'"]),
            ("E", ["E", "+", "E'"]),
            ("E", ["E", "-", "E'"]),
            ("E'", ["E''"]),
            ("E'", ["E'", "I", "E''"]),
            ("E'", ["E'", "*", "E''"]),
            ("E''", ["num"]),
            ("E''", ["id"]),
            ("E''", ["(", "E", ")"]),
            ("E''", ["{", "Z", "P", "}"]),
            ("Z", ["id", ":"]),
            ("P", ["P", "|", "P'"]),
            ("P", ["P'"]),
            ("P'", ["P'", "&", "P''"]),
            ("P'", ["P''"]),
            ("P''", ["R"]),
            ("P''", ["(", "P", ")"]),
            ("P''", ["!", "R"]),
            ("R", ["E", "<", "E"]),
            ("R", ["E", ">", "E"]),
            ("R", ["E", "=", "E"]),
            ("R", ["E", "@", "E"]),
            ("C", ["show", "A"]),
            ("A", ["E"]),
            ("A", ["P"])
        ]

    class TreeNode:
        def __init__(self, name=None, token=None, value=None, children=None):
            self.name = name  # Non terminal symbol name
            self.token = token  # Terminator type
            self.lexeme = value  # The morpheme of the terminal symbol
            self.children = children if children is not None else []  # Child Node List

        def to_dict(self):
            if self.token:  # Terminal
                return {"token": self.token, "lexeme": self.lexeme}
            return {
                "name": self.name,
                "children": [child.to_dict() for child in self.children],
            }

    def parse(self, tokens):
        self.syntax_tree = self.TreeNode(name="S")  # Initialize the root node of the syntax tree
        tokens.append({"token": "$", "lexeme": "$"})  # Add end marker
        token_index = 0

        while True:
            state = self.stack[-1]
            current_token = tokens[token_index]["token"]

            if current_token not in self.action_table[state]:
                print("Syntax Error!")
                with open('parser_out.json', 'w') as f:
                    json.dump({}, f)
                sys.exit(0)

            action = self.action_table[state][current_token]

            if action.startswith('s'):  # Shift operate
                next_state = int(action[1:])
                self.stack.append(next_state)
                token_index += 1

                # Create terminator node
                new_node = self.TreeNode(token=current_token, value=tokens[token_index - 1]["lexeme"])
                self.syntax_tree.children.append(new_node)

            elif action.startswith('r'):  # Reduce operate
                production_index = int(action[1:])
                lhs, rhs = self.get_production(production_index)

                # Collecting sub nodes
                children = []
                for _ in range(len(rhs)):
                    self.stack.pop()
                    children.insert(0, self.syntax_tree.children.pop())

                # Create non terminal node
                new_node = self.TreeNode(name=lhs, children=children)
                self.syntax_tree.children.append(new_node)

                # Transitions
                state = self.stack[-1]
                if lhs not in self.goto_table[state]:
                    print("Syntax Error!")
                    with open('parser_out.json', 'w') as f:
                        json.dump({}, f)
                    sys.exit(0)

                self.stack.append(self.goto_table[state][lhs])

            elif action == 'acc':  # Accept operate
                if len(self.syntax_tree.children) == 1:
                    self.syntax_tree = self.syntax_tree.children[0]
                break

        return self.syntax_tree

    def get_production(self, index):
        return self.grammar_rules[index]

def check2():
    tokens = process_input()
    # print(tokens)

    action_table, goto_table = parse_slr_table("SLR Parsing Table.csv")
    # print("Action Table:", action_table)
    # print("Goto Table:", goto_table)
    parser = Parser(action_table, goto_table)
    syntax_tree = parser.parse(tokens)

    with open('parser_out.json', 'w') as f:
        json.dump(syntax_tree.to_dict(), f, separators=(',', ':'))
    print("Syntax tree written to parser_out.json")

    return syntax_tree

if __name__ == "__main__":
    check2()
