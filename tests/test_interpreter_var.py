import pytest

from ast_nodes import Add, Assign, BinOp, Call, Constant, Expr, Module, Name, Sub
from interpreter_var import InterpreterVar


def test_assign_constant_to_variable():
    program = Module([Assign([Name("x")], Constant(42))])
    interp = InterpreterVar(program)

    env = interp.interp()

    assert env["x"] == 42


def test_assign_expression_to_variable():
    program = Module([Assign([Name("x")], BinOp(Constant(10), Add(), Constant(32)))])
    interp = InterpreterVar(program)

    env = interp.interp()

    assert env["x"] == 42


def test_use_variable_in_expression():
    program = Module(
        [
            Assign([Name("x")], Constant(10)),
            Assign([Name("y")], BinOp(Name("x"), Add(), Constant(5))),
        ]
    )
    interp = InterpreterVar(program)

    env = interp.interp()

    assert env["x"] == 10
    assert env["y"] == 15


def test_print_variable(capsys):
    program = Module(
        [
            Assign([Name("x")], Constant(42)),
            Expr(Call(Name("print"), [Name("x")])),
        ]
    )
    interp = InterpreterVar(program)

    interp.interp()

    captured = capsys.readouterr()
    assert captured.out == "42\n"


def test_multiple_assignments():
    program = Module(
        [
            Assign([Name("x")], Constant(1)),
            Assign([Name("x")], BinOp(Name("x"), Add(), Constant(1))),
            Assign([Name("x")], BinOp(Name("x"), Add(), Constant(1))),
        ]
    )
    interp = InterpreterVar(program)

    env = interp.interp()

    assert env["x"] == 3


def test_undefined_variable_raises_error():
    program = Module([Assign([Name("x")], Name("y"))])
    interp = InterpreterVar(program)

    with pytest.raises(ValueError, match="undefined variable: y"):
        interp.interp()


def test_complex_expression_with_variables():
    program = Module(
        [
            Assign([Name("a")], Constant(5)),
            Assign([Name("b")], Constant(10)),
            Assign(
                [Name("c")],
                BinOp(BinOp(Name("a"), Add(), Name("b")), Sub(), Constant(3)),
            ),
        ]
    )
    interp = InterpreterVar(program)

    env = interp.interp()

    assert env["a"] == 5
    assert env["b"] == 10
    assert env["c"] == 12


def test_interp_stmt_runs_continuation_with_assignments(capsys):
    first = Assign([Name("x")], Constant(10))
    cont = [Expr(Call(Name("print"), [Name("x")]))]
    interp = InterpreterVar(Module([]))

    interp.interp_stmt(first, cont, {})

    captured = capsys.readouterr()
    assert captured.out == "10\n"
