from lint_compiler.ast_nodes import (
    Add,
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
from lint_compiler.interpreter_int import InterpeterInt


def test_interp_exp_arithmetic():
    interp = InterpeterInt(Module([]))

    exp = BinOp(
        BinOp(Constant(10), Add(), Constant(7)),
        Sub(),
        UnaryOp(USub(), Constant(3)),
    )

    assert interp.interp_exp(exp) == 20


def test_interp_stmt_print(capsys):
    stmt = Expr(Call(Name("print"), [BinOp(Constant(8), Add(), Constant(2))]))
    interp = InterpeterInt(Module([]))

    interp.interp_stmt(stmt)

    captured = capsys.readouterr()
    assert captured.out == "10\n"


def test_interp_stmts_from_module(capsys):
    program = Module(
        [
            Expr(Call(Name("print"), [Constant(1)])),
            Expr(Call(Name("print"), [BinOp(Constant(10), Sub(), Constant(3))])),
        ]
    )

    interp = InterpeterInt(program)
    interp.interp_stmts()

    captured = capsys.readouterr()
    assert captured.out == "1\n7\n"


def test_interp_convenience_method(capsys):
    program = Module(
        [
            Expr(Call(Name("print"), [Constant(42)])),
            Expr(Call(Name("print"), [BinOp(Constant(5), Add(), Constant(6))])),
        ]
    )

    interp = InterpeterInt(program)
    interp.interp()

    captured = capsys.readouterr()
    assert captured.out == "42\n11\n"
