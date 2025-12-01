from ast import (
    And,
    Assign,
    BoolOp,
    Call,
    Compare,
    Constant,
    Eq,
    Expr,
    If,
    IfExp,
    Module,
    Name,
    Not,
    UnaryOp,
)
from unittest.mock import patch

from interp_lif import InterpLif


def test_pe_if_constant_branch():
    il = InterpLif()
    ast_tree = Module(
        [
            Assign([Name("x")], Constant(True)),
            If(
                Name("x"),
                [Assign([Name("y")], Constant(1))],
                [Assign([Name("y")], Constant(2))],
            ),
            Expr(Call(Name("print"), [Name("y")])),
        ]
    )
    result = il.pe(ast_tree)
    assert isinstance(result.body[0].test, Constant)
    assert result.body[0].test.value is True
    printed = result.body[1].value.args[0]
    assert isinstance(printed, Constant)
    assert printed.value == 1


def test_interp_booleans_and_ifexp():
    il = InterpLif()
    ast_tree = Module(
        [
            If(
                BoolOp(And(), [Constant(True), UnaryOp(Not(), Constant(False))]),
                [
                    Assign(
                        [Name("y")],
                        IfExp(
                            Compare(Constant(1), [Eq()], [Constant(1)]),
                            Constant(10),
                            Constant(20),
                        ),
                    ),
                    Expr(
                        Call(
                            Name("print"),
                            [BoolOp(And(), [Compare(Name("y"), [Eq()], [Constant(10)]), Constant(True)])],
                        )
                    ),
                ],
                [Expr(Call(Name("print"), [Constant(False)]))],
            )
        ]
    )
    with patch("builtins.print") as mock_print:
        il.interp(ast_tree)
        mock_print.assert_called_once_with(True, end="\n")
