import re

class SyntaxTreeNode:
    def __init__(self, name=None, token=None, lexeme=None, value=None):
        # Initialize the TreeNode add new attribute 'value'
        self.name = name
        self.token = token
        self.lexeme = lexeme
        self.children = []
        self.result = None
        self.type = None  # Type (used to distinguish between terminators and non terminators)
        self.value = value

    def to_dict(self):
        # Convert nodes to dictionary form
        if self.token:  # If it is a terminator node
            return {"token": self.token, "lexeme": self.lexeme}
        else:  # If it is not a terminator node
            return {"name": self.name, "children": [child.to_dict() for child in self.children]}

    def to_json_string(self, indent=0):
        # Generate formatted JSON string
        space = " " * (indent * 4)
        if self.token:  # terminator node
            return f'{space}{{"token": "{self.token}", "lexeme": "{self.lexeme}"}}'
        else:  # non-terminator node
            children_json = ",\n".join([child.to_json_string(indent + 1) for child in self.children])
            return f'{space}{{"name": "{self.name}", "children": [\n{children_json}\n{space} ]}}'

    def adjust_format(self):
        # Handle nested non leaf nodes in children and adjust them to the correct position
        if self.children:
            for child in self.children:
                # 如果子节点包含 token 和 lexeme 直接转移
                if 'token' in child.__dict__ and child.token:
                    # If the child node contains tokens and lexeme, transfer them directly
                    self.token = child.token
                    self.lexeme = child.lexeme
                    self.children.remove(child)
                else:
                    child.adjust_format()  # Recursive adjustment of child nodes
        return self

def parse_and_check(left_operand, expression):
    # Define operators and corresponding logical operations
    operators = {
        'U': lambda x, y: x or y,  # union
        'I': lambda x, y: x and y  # intersection
    }

    # Remove curly braces and split the expression
    expression = re.sub(r'\s+', ' ', expression.strip())
    sets = re.findall(r'\{[^}]*\}', expression)  # Match all set expressions
    ops = re.findall(r'[UI]', expression)  # Match all operators

    # Evaluate a single conditional expression
    def eval_condition(condition, variable, value):
        # Replace variables with actual values
        condition = condition.replace(variable, str(value)).replace('=', '==').replace('&', 'and').replace('|', 'or').replace('!', 'not ')
        return eval(condition)

    # Evaluate a single set expression
    def eval_set_expression(expr):
        expr = expr.strip('{}')
        variable, condition = expr.split(":")
        variable = variable.strip()
        return eval_condition(condition, variable, left_operand)

    # Evaluate all set expression
    results = [eval_set_expression(s) for s in sets]

    # Calculate based on operator priority
    while 'I' in ops:
        # Handle Intersection ('I' has higher precedence)
        i_idx = ops.index('I')  # Find the first 'I' operator
        lhs = results[i_idx]
        rhs = results[i_idx + 1]
        result = operators['I'](lhs, rhs)  # Apply intersection
        # Replace the processed sets and operator in the results and operators list
        results[i_idx] = result
        results.pop(i_idx + 1)
        ops.pop(i_idx)

    # Calculate the remaining union
    final_result = results[0]
    for i, op in enumerate(ops):
        final_result = operators[op](final_result, results[i + 1])

    return final_result


class Evaluaion:
    def __init__(self, syntax_tree: SyntaxTreeNode, symbol_table: dict):
        self.syntax_tree = syntax_tree
        self.symbol_table = {}
        self.error = False

    def evaluation(self, node: SyntaxTreeNode):
        if not node.children:
            if node.token == "num":
                # node.type = "integer"
                node.value = int(node.lexeme)
            else:
                # node.type = "void"
                node.value = "void"
            return

        for child in node.children:
            self.evaluation(child)

        if node.name == "S'":  # Rule 0
            node.value = node.children[0].value

        elif node.name == "S":  # Rules 1-2
            if len(node.children) == 3:  # Rule 1: S -> D' C .
                D_prime, C = node.children[0], node.children[1]
                if D_prime.value != "value_error" and C.value != "value_error":
                    node.value = node.children[1].value
                else:
                    node.value = "value_error"
            else:  # Rule 2: S -> C .
                node.value = node.children[0].value

        elif node.name == "D'":
            if len(node.children) == 2:  # Rule 3: D' -> D D'
                D, D_prime = node.children
                if D.value != "value_error" and D_prime.value != "value_error":
                    node.value = "void"
                else:
                    node.value = "value_error"
            else:  # Rule 4: D' -> D
                node.value = node.children[0].value

        elif node.name == "D":  # Rule 5: D -> let T id be E .
            var_type, var_name, expression = node.children[1], node.children[2], node.children[4]
            if expression.value != "value_error":
                self.symbol_table[var_name.lexeme] = {"type": var_type.type, "value": expression.value}
                node.value = "void"
            else:
                node.value = "value_error"

        elif node.name == "T":  # Rules 6-7
            if node.children[0].token == "int":  # Rule 6: T -> int
                node.value = "void"
            elif node.children[0].token == "set":  # Rule 7: T -> set
                node.value = "void"

        elif node.name == "E":  # Rules 8-11: E -> E', E U E', E + E', E - E'

            if len(node.children) == 3:  # Check if it's E -> E op E'
                lhs = node.children[0]
                op = node.children[1]
                rhs = node.children[2]

                # Ensure child nodes have been evaluated
                if (type(lhs.value) == int or type(lhs.value) == set) and (
                        type(rhs.value) == int or type(rhs.value) == set):
                    if op.lexeme == "+":  # Rule 10: E -> E + E'
                        if type(lhs.value) == int and type(rhs.value) == int:
                            node.value = lhs.value + rhs.value
                        else:
                            node.value = "value_error"
                    elif op.lexeme == "-":  # Rule 11: E -> E - E'
                        if type(lhs.value) == int and type(rhs.value) == int:
                            node.value = lhs.value - rhs.value
                        else:
                            node.value = "value_error"
                elif type(lhs.value) == str and type(rhs.value) == str:

                    # Handle set expressions
                    node.value = f"{lhs.value} U {rhs.value}"
                else:
                    node.value = "value_error"

            else:  # Rule 8: E -> E'
                node.value = node.children[0].value

        elif node.name == "E'":  # Rules 12-14
            if len(node.children) == 3:
                # Get child nodes by index
                lhs = node.children[0]
                op = node.children[1]
                rhs = node.children[2]

                # Get operand values, fetch from symbol table if id
                left_operand = lhs.value
                right_operand = rhs.value

                if lhs.token == "id":
                    left_operand = self.symbol_table.get(lhs.lexeme, {}).get("value", "value_error")
                if rhs.token == "id":
                    right_operand = self.symbol_table.get(rhs.lexeme, {}).get("value", "value_error")

                # Perform operations based on operator
                if op.lexeme == "I":  # Rule 13: E' -> E' I E''
                    if type(left_operand) == str and type(right_operand) == str:
                        # If both sides are string set expressions
                        node.value = f"{left_operand} I {right_operand}"
                elif op.lexeme == "*":  # Rule 14: E' -> E' * E''
                    if type(left_operand) == int and type(right_operand) == int:
                        node.value = left_operand * right_operand
            else:  # Rule 12: E' -> E''
                node.value = node.children[0].value

        elif node.name == "E''":
            # print(len(node.children))
            if len(node.children) == 1:
                # num or id already evaluated at terminal
                node.value = node.children[0].value  # E'' -> num
                if node.children[0].token == "id":  # E'' -> id
                    var_name = node.children[0].lexeme
                    print(self.symbol_table)
                    if var_name in self.symbol_table and "value" in self.symbol_table[var_name]:
                        # Global variable, get value from symbol table
                        node.value = self.symbol_table[var_name]["value"]
                    elif var_name in self.symbol_table and self.symbol_table.get(var_name, {}).get("type", "value_error") == "integer":
                        # Represents a variable, considered valid without specific value
                        node.value = var_name
                    else:
                        node.value = "value_error"
                        self.error = True

            elif len(node.children) == 3:  # Rule 17: E'' -> ( E )
                node.value = node.children[1].value
            elif len(node.children) == 4:  # Rule 18: E'' -> { Z P }
                Z, P = node.children[1], node.children[2]
                if P.value == "value_error":
                    if Z.value in self.symbol_table and "expressions" in self.symbol_table[Z.value]:
                        # Global variable, get expressions from symbol table
                        expressions = self.symbol_table[Z.value]["expressions"]
                        if type(expressions) == list and expressions:
                            P.value = expressions[0]  # Take the first expression, or use ' '.join(expressions) to concatenate
                        else:
                            P.value = "value_error"

                if P.type == "predicate":
                    node.value = f"{{ {Z.children[0].lexeme}: {P.value} }}"
                else:
                    node.value = "value_error"
                    self.error = True

        elif node.name == "Z":  # Rule 19
            var_name = node.children[0].lexeme
            self.symbol_table[var_name] = {"type": "integer"}

            # print(var_name)
            node.value = var_name

        elif node.name == "P":  # Rules 20-21
            if len(node.children) == 3:  # Rule 20: P -> P | P'
                left_node = node.children[0]
                operator_node = node.children[1]
                right_node = node.children[2]

                if left_node.type == "predicate" and right_node.type == "predicate":
                    # Assume P's child nodes have correctly set the result attribute, perform logical OR
                    node.value = f"({left_node.value} {operator_node.lexeme} {right_node.value})"
                    node.result = left_node.result or right_node.result
                else:
                    node.value = "value_error"
                    self.error = True
                    node.result = False  # If type error, set result to False
            else:  # Rule 21: P -> P'
                node.value = node.children[0].value
                node.result = node.children[0].result  # Directly inherit P's result

        elif node.name == "P'":  # Rules 22
            if len(node.children) == 3:  # Rule 22: P' -> P' & P''
                left_node = node.children[0]
                op = node.children[1]
                right_node = node.children[2]

                if op.lexeme == "&" and left_node.type == "predicate" and right_node.type == "predicate":
                    node.value = f"({left_node.value} {op.lexeme} {right_node.value})"
                    node.result = left_node.result and right_node.result
                    # print(node.value)
                else:
                    node.value = "value_error"
                    self.error = True
                    node.result = False  # If type error, set result to False
            else:  # Rule 21: P' -> P''
                single_child = node.children[0]
                node.value = single_child.value
                node.result = single_child.result  # Directly inherit P'' result

        elif node.name == "P''":  # Rules 24-26
            if len(node.children) == 1:  # Rule 24: P'' -> R
                node.value = node.children[0].value
                node.result = node.children[0].result  # Directly inherit R's result
            elif len(node.children) == 3:  # Rule 25: P'' -> ( P )
                node.value = node.children[1].value
                node.result = node.children[1].result  # Directly inherit inner P's result
            elif len(node.children) == 2:  # Rule 26: P'' -> ! R
                op = node.children[0]
                R_node = node.children[1]

                if op.lexeme == "!" and R_node.type == "relation":
                    # Perform logical NOT operation
                    node.value = f"{op.lexeme} {R_node.value}"
                    node.result = not R_node.result
                else:
                    node.value = "value_error"
                    self.error = True
                    node.result = False  # If type error, set result to False

        elif node.name == "R":  # Rules 27-30: R -> E < E, R -> E > E, R -> E = E, R -> E @ E
            lhs = node.children[0].value

            comparison_result = "value_error"
            operator_lexeme = node.children[1].lexeme

            rhs = node.children[2].value
            # If any operand is value_error, the entire expression is value_error
            if lhs == "value_error" or rhs == "value_error":
                node.value = "value_error"
                node.result = "value_error"  # Save result as value_error
                print("Value error in comparison expression.")
            else:
                # If operands are variable names (id), check if they have corresponding values in the symbol table
                if type(lhs) == str:
                    if lhs in self.symbol_table and "value" in self.symbol_table[lhs]:
                        lhs = self.symbol_table[lhs]["value"]
                    else:
                        print(f"Error: Variable '{lhs}' is not defined or has no value.")
                        node.value = lhs
                        node.result = lhs

                if type(rhs) == str:
                    if rhs in self.symbol_table and "value" in self.symbol_table[rhs]:
                        rhs = self.symbol_table[rhs]["value"]
                    else:
                        print(f"Error: Variable '{rhs}' is not defined or has no value.")
                        node.value = rhs
                        node.result = rhs

                # Perform comparisons based on operator
                if operator_lexeme == "<":
                    if type(lhs) == int and type(rhs) == int:
                        # Both operands are integers, perform direct comparison
                        comparison_result = lhs < rhs
                        print(comparison_result)
                    elif type(rhs) == str:
                        # Right operand is a variable name, store the expression in the symbol table
                        self.update_symbol_table_rhs(rhs, lhs, "<")
                    elif type(lhs) == str:
                        # Left operand is a variable name, store the expression in the symbol table
                        self.update_symbol_table_lhs(lhs, rhs, "<")
                    else:
                        # Type error
                        comparison_result = "value_error"

                elif operator_lexeme == ">":
                    if type(lhs) == int and type(rhs) == int:
                        # Both operands are integers, perform direct comparison
                        comparison_result = lhs > rhs
                    elif type(rhs) == str:
                        # Right operand is a variable name, store the expression in the symbol table
                        self.update_symbol_table_rhs(rhs, lhs, ">")

                    elif type(lhs) == str:
                        # Left operand is a variable name, store the expression in the symbol table
                        self.update_symbol_table_lhs(lhs, rhs, ">")

                    else:
                        comparison_result = "value_error"
                        print(f"Type error in Rule 28: R -> E > E")

                elif operator_lexeme == "=":
                    if type(lhs) == int and type(rhs) == int:
                        # Both operands are integers, perform direct comparison
                        comparison_result = lhs == rhs
                    elif type(rhs) == str:
                        # Right operand is a variable name, store the expression in the symbol table
                        self.update_symbol_table_rhs(rhs, lhs, "=")

                    elif type(lhs) == str:
                        # Left operand is a variable name, store the expression in the symbol table
                        self.update_symbol_table_lhs(lhs, rhs, "=")
                    else:
                        comparison_result = "value_error"
                        print(f"Type error in Rule 29: R -> E = E")

                elif operator_lexeme == "@":
                    # print(f"Original right_operand: {rhs}")
                    if type(rhs) == str:
                        # Directly check if the left operand satisfies the right operand's condition
                        # print(lhs)
                        comparison_result = parse_and_check(lhs, rhs)
                        print(type(comparison_result))
                    else:
                        comparison_result = "value_error"
                        print(f"Type error in Rule 30: R -> E @ E")
                else:
                    comparison_result = "invalid_operator"
                    print("Invalid operator in comparison expression.")

                # Set value to the expression string, result to the comparison result
                node.value = f"{lhs} {operator_lexeme} {rhs}"
                node.result = comparison_result

        elif node.name == "C":  # Rule 31: C -> show A
            node.value = node.children[1].value

        elif node.name == "A":  # Rules 32-33: A -> E|P
            child = node.children[0]

            if child.name == "E":  # If child node is expression E
                # A node directly inherits E node's value and result
                node.value = child.value
                node.result = getattr(child, 'result',
                                      "void")  # Use E's result attribute if it exists, otherwise "void"
            elif child.name == "P":  # If child node is predicate P
                # A node's value attribute is set to P node's result attribute (boolean value)
                node.value = str(child.result).lower()
        else:
            node.value = "value_error"

        if node.value in {"value_error"}:
            self.error = True
            return

    def node_to_dict_value(self, node, level=0):
        indent = " " * (level * 2)
        if node.token:  # Terminal
            result = f'{indent}{{\n'
            result += f'{indent}  "token": "{node.token}",\n {indent} "lexeme": "{node.lexeme}",\n{indent}  "value": "{getattr(node, "value", "void")}"\n'
            result += f'{indent}}}'
        else:  # non-Terminal
            result = f'{indent}{{\n'
            result += f'{indent}  "name": "{node.name}",\n{indent}  "value": "{getattr(node, "value", "void")}",\n{indent}  "children": [\n'
            child_results = [self.node_to_dict_value(child, level + 2) for child in node.children]
            result += ",\n".join(child_results)
            result += f'\n{indent}  ]\n'
            result += f'{indent}}}'

        return result

    def to_json_format_value(self):
        return self.node_to_dict_value(self.syntax_tree)

    def update_symbol_table_rhs(self, rhs, lhs, operator):
        if rhs not in self.symbol_table:
            self.symbol_table[rhs] = {
                "type": "integer",
                "value": None,
                "expressions": []
            }
        elif "expressions" not in self.symbol_table[rhs]:
            self.symbol_table[rhs]["expressions"] = []

        # Store the expression
        expression_str = f"{lhs} {operator} {rhs}"
        self.symbol_table[rhs]["expressions"].append(expression_str)
        print(f"Updated symbol table for {rhs}: {self.symbol_table[rhs]}")

    def update_symbol_table_lhs(self, lhs, rhs, operator):
        if lhs not in self.symbol_table:
            self.symbol_table[lhs] = {
                "type": "integer",
                "value": None,
                "expressions": []
            }
        elif "expressions" not in self.symbol_table[lhs]:
            self.symbol_table[lhs]["expressions"] = []

        # Store the expression
        expression_str = f"{lhs} {operator} {rhs}"
        self.symbol_table[lhs]["expressions"].append(expression_str)
        print(f"Updated symbol table for {rhs}: {self.symbol_table[lhs]}")
