from ast_nodes import (
    Add,
    Assign,
    BinOp,
    Call,
    Constant,
    Expr,
    Module,
    Name,
    Sub,
    USub,
    UnaryOp,
)
from interpreter_var import InterpreterVar


def program_chain_assignments() -> Module:
    return Module(
        [
            Assign([Name("x")], Constant(10)),
            Assign([Name("y")], BinOp(Name("x"), Add(), Constant(5))),
            Assign([Name("z")], BinOp(Name("y"), Sub(), Constant(2))),
            Expr(Call(Name("print"), [Name("z")])),
        ]
    )


def program_with_input() -> Module:
    return Module(
        [
            Assign([Name("x")], Call(Name("input_int"), [])),
            Assign([Name("y")], UnaryOp(USub(), Name("x"))),
            Assign([Name("z")], BinOp(Name("y"), Add(), Constant(8))),
            Expr(Call(Name("print"), [Name("z")])),
        ]
    )


if __name__ == "__main__":
    print("LVar Interpreter Demo")

    print("Program A: x=10; y=x+5; z=y-2; print(z)")
    InterpreterVar(program_chain_assignments()).interp()

    print("Program B: x=input_int(); y=-x; z=y+8; print(z)")
    print("Please enter an integer:")
    InterpreterVar(program_with_input()).interp()
