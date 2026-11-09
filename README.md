# Set Algebra Compiler — Lexer, SLR(1) Parser & Evaluator

A Python implementation of a **compiler front end and evaluator** for a small, set-algebra language. The project combines a hand-written lexer, a table-driven **SLR(1) parser**, syntax-tree construction, semantic type checking, and expression evaluation. Intermediate representations are exported as JSON so each compilation stage can be inspected.

## Highlights

- **Hand-written lexical analyzer:** recognizes keywords, identifiers, integer literals, punctuation, arithmetic, relational, logical and set operators; emits token/lexeme pairs.
- **Table-driven SLR(1) parsing:** processes the token stream using `ACTION` and `GOTO` transitions and shift/reduce operations; builds a hierarchical parse tree.
- **Semantic analysis:** tracks declared types in a symbol table and checks expressions against the language's integer, set and predicate rules.
- **Expression evaluation:** evaluates integer expressions, Boolean predicates and set membership; represents set expressions symbolically rather than enumerating infinite sets.
- **Inspectable JSON output:** exposes lexer tokens, parse trees, type-annotated trees and evaluation-annotated trees.
- **Zero third-party dependencies:** the project uses Python's standard library.

## Language at a glance

Programs contain zero or more declarations followed by a single `show` expression.

| Construct | Example | Purpose |
|---|---|---|
| Integer declaration | `let int a be 3 .` | Bind an integer variable |
| Set declaration | `let set s be { x : x > 3 } .` | Bind an integer set using a predicate |
| Arithmetic | `show 1 + 2 * 3 .` | Apply operator precedence |
| Relation | `show 3 > 2 .` | Evaluate a Boolean predicate |
| Set union / intersection | `U`, `I` | Combine set expressions |
| Membership | `show 5 @ s .` | Test whether an integer belongs to a set |
| Logic | `!`, `&`, `\|` | Negation, conjunction, disjunction |

A set such as `{ x : x > 3 }` is defined by a **predicate**, rather than by a finite enumeration of elements. The evaluator can preserve these expressions symbolically; the implementation does not generally simplify unions or intersections into canonical forms.

## Compiler pipeline

```text
Source file (.set / .txt)
         |
         v
    Lexer (lexer.py)  --------> lexer_out.json
         |
         v
  SLR(1) parser (parser.py) ---> parser_out.json
         |
         v
Type checker (type_checker.py) -> typing_out.json
         |
         v
 Evaluator (evaluation.py) ---> evaluation_out.json
```

The SLR parser reads the provided `SLR Parsing Table.csv` at runtime. Its reduction rules appear in `parser.py`; a companion textual grammar is retained in `SLR Grammar.txt`.

## Getting started

**Requirements:** Python 3 (tested with Python 3.13). No `pip install` step is needed.

```bash
git clone https://github.com/Chloe-Xia/Set-Algebra-Compiler.git
cd Set-Algebra-Compiler
python3 main.py examples/arithmetic.set
```

The last command reads:

```text
let int a be 3 .
let int b be 4 .
show a + b .
```

On successful execution, the root `value` in `evaluation_out.json` is `"7"`:

```bash
python3 -c "import json; print(json.load(open('evaluation_out.json'))['value'])"
# 7
```

> **Working directory matters:** Run commands from the repository root: `main.py` loads `SLR Parsing Table.csv` relative to the current directory. The program writes its JSON output files to that same directory and may emit additional debugging messages.

### Try other examples

```bash
python3 main.py examples/operator_precedence.set
python3 main.py examples/set_operations.set
python3 main.py examples/set_membership.set
python3 main.py examples/predicate.set
```

Examples include arithmetic precedence, symbolic set union, and membership evaluation.

## Generated output

| File | Contents |
|---|---|
| `lexer_out.json` | Ordered list of tokens and lexemes |
| `parser_out.json` | Hierarchical parse tree with terminals and grammar nonterminals |
| `typing_out.json` | Parse tree annotated with inferred or checked types |
| `evaluation_out.json` | Parse tree annotated with evaluated values |

The files are **generated artifacts**, not source files, and are excluded by `.gitignore`. The current program does not consistently clear all intermediate files after errors; avoid interpreting previous outputs as the result of a failed run.

## Repository structure

```text
Set-Algebra-Compiler/
├── main.py                  # CLI entry point and phase orchestration
├── lexer.py                 # Lexical analysis and token generation
├── parser.py                # Shift/reduce SLR(1) parser and parse tree
├── type_checker.py          # Symbol table and semantic type checking
├── evaluation.py            # Expression evaluation and JSON serialization
├── SLR Parsing Table.csv    # ACTION/GOTO table used by the parser
├── SLR Grammar.txt          # Reference grammar
├── examples/                # Small source programs
├── tests/                   # Standard-library smoke tests
├── .gitignore
└── README.md
```

## Verification

Run the included smoke tests:

```bash
python3 -m unittest discover -s tests -v
```

These tests check representative successful inputs and whether expected JSON values are produced. They are **not** a comprehensive validation suite or a claim of full compliance with the course specification.

