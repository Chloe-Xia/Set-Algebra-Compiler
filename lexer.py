import json

# Define the keywords
KEYWORDS = {'let', 'be', 'show', 'int', 'set', 'simplify'}

# Helper function to add a token to the token list
def add_token(tokens, token, token_type):
    if token:
        tokens.append({"token": token_type, "lexeme": token})

# Function to handle the lexing process
def Lexer(input_text):
    tokens = []  # List to store tokens
    current_token = ''  # To accumulate characters of current token
    state = 'START'  # Initial state
    count = 0
    i = 0  # Pointer to traverse the input text
    while i < len(input_text):
        char = input_text[i]

        try:
            if state == 'START':
                if char.isdigit():
                    # Handle numbers
                    current_token = char
                    state = 'NUMBER'
                elif char.islower():
                    # Handle identifiers
                    current_token = char  # Start accumulating identifier characters
                    state = 'ID'
                elif char in {'U', 'I'}:
                    # Handle special case for 'U' and 'I'
                    add_token(tokens, char, char)  # Treat 'U' or 'I' as their own token
                    state = 'START'
                elif char in {'+', '-', '*', '@', '<', '>', '&', '|', '!', '='}:
                    # Handle operators
                    add_token(tokens, char, char)
                    state = 'START'
                elif char in {'.', '(', ')', '{', '}', ':'}:
                    # Handle symbols
                    add_token(tokens, char, char)
                    state = 'START'
                elif char.isspace():
                    # Ignore spaces
                    state = 'START'
                elif char == '#':
                    # Enter comment state
                    state = 'COMMENT'
                else:
                    raise ValueError(f"Unexpected character: {char}")

            elif state == 'ID':  # Handle identifiers and keywords
                if char.islower():
                    # Continue accumulating identifier characters
                    current_token += char
                    state = 'ID'  # Stay in 'ID' state while accumulating identifier
                else:
                    if current_token in KEYWORDS:
                        add_token(tokens, current_token, current_token)  # Treat as keyword
                        current_token = ''
                        state = 'START'
                        continue
                    elif char.isdigit():
                        # Switch to number state if digits are found after identifier
                        add_token(tokens, current_token, 'id')  # Submit current identifier token
                        current_token = char
                        state = 'NUMBER'
                    elif char in {'U', 'I'}:
                        # Special handling for 'U' or 'I'
                        add_token(tokens, current_token, 'id')
                        add_token(tokens, char, char)  # Add 'U' or 'I' as its own token
                        current_token = ''
                        state = 'START'
                    elif char in {'+', '-', '*', '@', '<', '>', '&', '|', '!', '='} or char in {'.', '(', ')', '{', '}',
                                                                                            ':'} or char.isspace():
                        # Check if the current token is a keyword or identifier
                        if current_token in KEYWORDS:
                            add_token(tokens, current_token, current_token)  # Treat as keyword
                        else:
                            add_token(tokens, current_token, 'id')  # Treat as normal identifier
                        current_token = ''
                        state = 'START'
                        continue
                    elif char == '#':
                        # Enter comment state
                        state = 'COMMENT'

                    else:
                        raise ValueError(f"Unexpected character in ID: {char}")

            elif state == 'NUMBER':  # Handle numbers
                if char.isdigit():
                    # Continue accumulating digits
                    if count > 10:
                        raise ValueError(f"Unexpected length of number ( num > 10 )")
                    elif current_token == '0' and count == 0:
                        add_token(tokens, current_token, 'num')
                        count = 0
                        current_token = char
                        state = 'NUMBER'
                    else:
                        current_token += char
                        count += 1
                        state = 'NUMBER'
                elif char.islower():
                    # Switch to identifier state if letters appear after a number
                    add_token(tokens, current_token, 'num')
                    count = 0
                    current_token = char
                    state = 'ID'
                elif char in {'+', '-', '*', '@', '<', '>', '&', '|', '!', '='} or char in {'.', '(', ')', '{', '}',
                                                                                            ':'} or char.isspace():
                    # Submit the number token
                    add_token(tokens, current_token, 'num')
                    count = 0
                    current_token = ''
                    state = 'START'
                    continue
                elif char in {'U', 'I'}:
                    # Special handling for 'U' or 'I'
                    add_token(tokens, current_token, 'num')
                    add_token(tokens, char, char)  # Add 'U' or 'I' as its own token
                    current_token = ''
                    state = 'START'
                elif char == '#':
                    # Enter comment state
                    state = 'COMMENT'
                else:
                    raise ValueError(f"Unexpected character: {char}")

            elif state == 'COMMENT':
                if char == '\n':
                    state = 'START'

            i += 1  # Move to next character

        except ValueError as e:
            print(f"Error: {e}")
            return []

    # Handle any remaining token at the end
    if current_token:
        if current_token in KEYWORDS:
            add_token(tokens, current_token, current_token)  # If it's a keyword
        elif current_token.isdigit():
            add_token(tokens, current_token, 'num')  # If it's a number
        else:
            add_token(tokens, current_token, 'id')  # Otherwise, it's an identifier

    return tokens  # Return the JSON formatted tokens

# Function to read input until an empty line and process the lexing
def process_input():
    print("Please enter the code content and end with a blank line:")
    input_lines = []

    # Read multi-line input
    while True:
        line = input()
        if line == '':  # Stop reading on empty line
            break
        input_lines.append(line)

    # Join all the lines into a single string
    source_code = '\n'.join(input_lines)

    # Use the Lexer to analyze the input
    tokens = Lexer(source_code)

    with open("lexer_out.json", "w") as json_file:
            json.dump(tokens, json_file, indent=2)

    return tokens

    print("Parsed Tokens (JSON format):")
    print(lexer_output)

# Main execution
if __name__ == '__main__':
    process_input()