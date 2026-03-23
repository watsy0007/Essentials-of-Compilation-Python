from ast_nodes import (
    Add,
    Assign,
    BinOp,
    Call,
    Constant,
    Expr,
    Module,
    Name,
    USub,
    UnaryOp,
)
from interpreter_int import InterpeterInt
from interpreter_var import InterpreterVar


def program_book_example() -> Module:
    eight = Constant(8)
    neg_eight = UnaryOp(USub(), eight)
    read = Call(Name("input_int"), [])
    ast1_1 = BinOp(read, Add(), neg_eight)
    return Module([Expr(Call(Name("print"), [ast1_1]))])


def program_no_input() -> Module:
    exp = BinOp(Constant(20), Add(), UnaryOp(USub(), Constant(3)))
    return Module([Expr(Call(Name("print"), [exp]))])


def program_var_example() -> Module:
    return Module(
        [
            Assign([Name("x")], Call(Name("input_int"), [])),
            Assign([Name("y")], BinOp(Name("x"), Add(), Constant(5))),
            Expr(Call(Name("print"), [Name("y")])),
        ]
    )


if __name__ == "__main__":
    print("Program A (no input): print(20 + -3)")
    InterpeterInt(program_no_input()).interp()

    print("Program B (book example): print(input_int() + -8)")
    print("Please enter an integer:")
    InterpeterInt(program_book_example()).interp()

    print("Program C (variables): x = input_int(); y = x + 5; print(y)")
    print("Please enter an integer:")
    InterpreterVar(program_var_example()).interp()
