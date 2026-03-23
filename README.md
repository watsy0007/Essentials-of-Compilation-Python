# learn_compilation_by_python

Learning compiler construction in Python from
"Essentials of Compilation: An Incremental Approach (Python)".

## Setup

```bash
uv sync
```

## Run tests

```bash
uv run pytest
```

## Run the interpreter demo

```bash
uv run python examples/run_lint.py
```

This demo runs two programs:
- `print(20 + -3)`
- `print(input_int() + -8)`

## Current components

- AST nodes for the LInt subset in `src/lint_compiler/ast_nodes.py`
- Interpreter in `src/lint_compiler/interpreter_int.py`
- Partial evaluator in `src/lint_compiler/partial_eval_int.py`
