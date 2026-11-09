import json
from parser import check2

class TreeNode:
    def __init__(self, name=None, token=None, lexeme=None, children=None):
        # Initialize the TreeNode add new attribute 'type'
        self.name = name
        self.token = token
        self.lexeme = lexeme
        self.children = children if children else [] # Default to an empty list if no children provided
        self.type = None # Type will be determined during semantic analysis

class SymbolTable:
    def __init__(self):
        self.table = {}

    def add(self, var_name, var_type, value=None):
        # Add a variable with its type and optional value to the symbol table
        self.table[var_name] = {"type": var_type, "value": value}
        print(f"Added to symbol table: {var_name} -> {var_type} (value: {value})")

    def lookup(self, var_name):
        # Lookup the type of a variable in the symbol table
        print(f"Looking up {var_name} in symbol table: {self.table}")
        return self.table.get(var_name, {}).get("type", "type_error")

    def lookup_value(self, var_name):
        # Lookup the value of a variable in the symbol table
        return self.table.get(var_name, {}).get("value", None)

    def __str__(self):
        # String representation of the symbol table for debugging
        return str(self.table)

class SemanticAnalyzer:
    def __init__(self, syntax_tree):
        self.syntax_tree = syntax_tree
        self.symbol_table = SymbolTable()
        self.has_error = False # Tracks if any semantic errors are detected

    def add_to_symbol_table(self, var_name, var_type):
        # Add a variable and its type to the symbol table
        self.symbol_table.add(var_name, var_type)

    def lookup_symbol_table(self, var_name):
        # Lookup a variable's type in the symbol table
        return self.symbol_table.lookup(var_name)

    def check_node(self, node):
        if node.token:  # Handle terminal nodes
            if node.token == "num":
                node.type = "integer"
            elif node.token == "id":
                node.type = "void" # Default type for identifiers in this context
            elif node.token in ["show", ".", "<", ">", "=", "@", "&", "|", "!"]:
                node.type = "void"
            else:
                node.type = "void"
        elif node.name:  # Handle non-terminal nodes
            for child in node.children:
                self.check_node(child)

            # Apply semantic rules based on the node's name
            if node.name == "S'":
                # Rule: S' -> S
                node.type = node.children[0].type

            elif node.name == "S":
                if len(node.children) == 3:  # Rule: S -> D' C .
                    D_prime, C = node.children[0], node.children[1]
                    if D_prime.type != "type_error" and C.type != "type_error":
                        node.type = "program"
                    else:
                        node.type = "type_error"
                        self.has_error = True
                else:  # Rule: S -> C .
                    node.type = node.children[0].type

            elif node.name.startswith("D'"):
                if len(node.children) == 2:  # Rule: D'1 -> D D'2
                    D, D_prime2 = node.children[0], node.children[1]
                    if D.type == "declaration" and D_prime2.type == "declarations":
                        node.type = "declarations"
                    else:
                        node.type = "type_error"
                        self.has_error = True
                else:  # Rule: D' -> D
                    D = node.children[0]
                    if D.type == "declaration":
                        node.type = "declarations"
                    else:
                        node.type = "type_error"
                        self.has_error = True

            elif node.name == "D":
                # Rule: D -> let T id be E .
                var_type, var_name, expression = node.children[1], node.children[2], node.children[4]
                if expression.type != var_type.type:
                    node.type = "type_error"
                    self.has_error = True
                else:
                    self.symbol_table.add(var_name.lexeme, var_type.type)
                    node.type = "declaration"

            elif node.name == "T":
                # Rule: T -> int or T -> set
                if node.children[0].token == "int":
                    node.type = "integer"
                elif node.children[0].token == "set":
                    node.type = "set"

            elif node.name == "E":
                # Rule: E -> E' or E -> E2 op E'
                if len(node.children) == 1:
                    node.type = node.children[0].type
                elif len(node.children) == 3:
                    E2, operator, E_prime = node.children
                    if operator.lexeme == "U":
                        if E2.type == "set" and E_prime.type == "set":
                            node.type = "set"
                        else:
                            node.type = "type_error"
                            self.has_error = True
                    elif operator.lexeme in ["+", "-"]:
                        if E2.type == "integer" and E_prime.type == "integer":
                            node.type = "integer"
                        else:
                            node.type = "type_error"
                            self.has_error = True

            elif node.name == "E'":
                # Rule: E' -> E'' or E' -> E' op E''
                if len(node.children) == 1:
                    node.type = node.children[0].type
                elif len(node.children) == 3:
                    E_prime2, operator, E_double = node.children
                    if operator.lexeme == "I":
                        if E_prime2.type == "set" and E_double.type == "set":
                            node.type = "set"
                        else:
                            node.type = "type_error"
                            self.has_error = True
                    elif operator.lexeme == "*":
                        if E_prime2.type == "integer" and E_double.type == "integer":
                            node.type = "integer"
                        else:
                            node.type = "type_error"
                            self.has_error = True

            elif node.name == "E''":
                # Rule: E'' -> num or E'' -> id or E'' -> E or E'' -> { Z P }
                if node.children[0].token == "num":
                    node.type = "integer"
                elif node.children[0].token == "id":
                    var_name = node.children[0].lexeme
                    node.type = self.symbol_table.lookup(var_name)
                elif len(node.children) == 3:  # ( E )
                    node.type = node.children[1].type
                elif len(node.children) == 4:  # { Z P }
                    Z, P = [child for child in node.children if child.name in ("Z", "P")]
                    if P.type == "predicate":
                        node.type = "set"
                    else:
                        node.type = "type_error"
                        self.has_error = True

            elif node.name == "Z":
                # Rule: Z -> id
                var_name = node.children[0].lexeme
                self.symbol_table.add(var_name, "integer")
                node.type = "void"

            elif node.name == "P":
                # Rule: P -> P' or P1 -> P2 | P'
                if len(node.children) == 3:
                    P2, operator, P_prime = node.children
                    if P2.type == "predicate" and P_prime.type == "predicate":
                        node.type = "predicate"
                    else:
                        node.type = "type_error"
                        self.has_error = True
                elif len(node.children) == 1:
                    node.type = node.children[0].type

            elif node.name == "P'":
                # Rule: P' -> P'' or P'1 -> P'2 | P''
                if len(node.children) == 3:
                    P_prime2, operator, P_double = node.children
                    if P_prime2.type == "predicate" and P_double.type == "predicate":
                        node.type = "predicate"
                    else:
                        node.type = "type_error"
                        self.has_error = True
                elif len(node.children) == 1:
                    node.type = node.children[0].type

            elif node.name == "P''":
                # Rule: P'' -> R or P'' -> ( P ) or P'' -> ! R
                if len(node.children) == 1 and node.children[0].name == "R":
                    R = node.children[0]
                    if R.type == "relation":
                        node.type = "predicate"
                    else:
                        node.type = "type_error"
                        self.has_error = True
                elif len(node.children) == 3:
                    node.type = node.children[1].type
                elif len(node.children) == 2:
                    R = node.children[1]
                    if R.type == "relation":
                        node.type = "predicate"
                    else:
                        node.type = "type_error"
                        self.has_error = True

            elif node.name == "R":
                # Rule: R -> E1 op E2
                E1, operator, E2 = node.children
                if operator.lexeme in {"<", ">", "="}:
                    if E1.type == "integer" and E2.type == "integer":
                        node.type = "relation"
                    else:
                        node.type = "type_error"
                        self.has_error = True
                elif operator.lexeme == "@":
                    if E1.type == "integer" and E2.type == "set":
                        node.type = "relation"
                    else:
                        node.type = "type_error"
                        self.has_error = True

            elif node.name == "C":
                # Rule: C -> show A
                node.type = node.children[1].type

            elif node.name == "A":
                # Rule: A -> E or A -> P
                child = node.children[0]
                if child.type != "type_error":
                    node.type = "calculation"
                else:
                    node.type = "type_error"
                    self.has_error = True

    def type_check(self):
        # Perform type checking on the syntax tree
        self.check_node(self.syntax_tree)
        return not self.has_error

    def serialize_tree(self, node):
        # Convert the syntax tree into a dictionary format for JSON output
        if node.token:
            return {
                "token": node.token,
                "lexeme": node.lexeme,
                "type": node.type,
            }
        else:
            return {
                "name": node.name,
                "type": node.type,
                "children": [self.serialize_tree(child) for child in node.children],
            }

    def write_typing_out(self, filename="typing_out.json"):
        # Write the serialized syntax tree to a JSON file
        with open(filename, "w") as f:
            json.dump(self.serialize_tree(self.syntax_tree), f, indent=4)

if __name__ == '__main__':
    tree = check2()
    analyzer = SemanticAnalyzer(tree)

    if analyzer.type_check():
        analyzer.write_typing_out("typing_out.json")
    else:
        print("Type error detected!")

