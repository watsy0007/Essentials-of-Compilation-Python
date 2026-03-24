from ast_nodes import Add, BinOp, Call, Constant, Expr, Module, Name, USub, UnaryOp
from interpreter_int import InterpeterInt
from partial_eval_int import PartialEvalInt


def program_no_input() -> Module:
    exp = BinOp(
        BinOp(Constant(10), Add(), Constant(2)),
        Add(),
        UnaryOp(USub(), Constant(3)),
    )
    return Module([Expr(Call(Name("print"), [exp]))])


def program_with_input() -> Module:
    exp = BinOp(
        Call(Name("input_int"), []), Add(), BinOp(Constant(5), Add(), Constant(6))
    )
    return Module([Expr(Call(Name("print"), [exp]))])


if __name__ == "__main__":
    print("LInt Partial Evaluation Demo")

    original_a = program_no_input()
    optimized_a = PartialEvalInt(original_a).pe()
    print("Program A original:", original_a)
    print("Program A optimized:", optimized_a)
    print("Program A output:")
    InterpeterInt(optimized_a).interp()

    original_b = program_with_input()
    optimized_b = PartialEvalInt(original_b).pe()
    print("Program B original:", original_b)
    print("Program B optimized:", optimized_b)
    print("Program B output (please enter an integer):")
    InterpeterInt(optimized_b).interp()
