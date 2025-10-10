from ast import Add, Assign, BinOp, Call, Constant, Expr, Module, Name
from unittest.mock import patch

from interp_lvar import InterpLvar


def test_pe():
    il = InterpLvar()
    ast_tree = Module(
        [
            Assign([Name("x")], BinOp(Constant(1), Add(), Constant(2))),
            Expr(Call(Name("print"), [Name("x")])),
        ]
    )
    result = il.pe(ast_tree)
    assert str(result) == "print(3)"


def test_interp():
    il = InterpLvar()
    ast_tree = Module(
        [
            Assign([Name("x")], BinOp(Constant(1), Add(), Constant(2))),
            Expr(Call(Name("print"), [Name("x")])),
        ]
    )
    with patch("builtins.print") as mock_print:
        il.interp(ast_tree)
        mock_print.assert_called_once_with(3, end="\n")
