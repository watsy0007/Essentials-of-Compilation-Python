from ast_nodes import Add, Assign, BinOp, Call, Constant, Expr, Module, Name, Sub
from interpreter_var import InterpreterVar
from partial_eval_var import PartialEvalVar


def program_constant_propagation() -> Module:
    return Module(
        [
            Assign([Name("x")], BinOp(Constant(40), Add(), Constant(2))),
            Assign([Name("y")], BinOp(Name("x"), Add(), Constant(1))),
            Expr(Call(Name("print"), [Name("y")])),
        ]
    )


def program_mixed_dynamic() -> Module:
    return Module(
        [
            Assign([Name("x")], Constant(5)),
            Assign([Name("x")], Call(Name("input_int"), [])),
            Assign([Name("y")], BinOp(Name("x"), Sub(), Constant(3))),
            Expr(Call(Name("print"), [Name("y")])),
        ]
    )


if __name__ == "__main__":
    print("LVar Partial Evaluation Demo")

    original_a = program_constant_propagation()
    optimized_a = PartialEvalVar(original_a).pe()
    print("Program A original:", original_a)
    print("Program A optimized:", optimized_a)
    print("Program A output:")
    InterpreterVar(optimized_a).interp()

    original_b = program_mixed_dynamic()
    optimized_b = PartialEvalVar(original_b).pe()
    print("Program B original:", original_b)
    print("Program B optimized:", optimized_b)
    print("Program B output (please enter an integer):")
    InterpreterVar(optimized_b).interp()
