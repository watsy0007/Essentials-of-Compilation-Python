from ast import Add, BinOp, Call, Constant, Expr, Module, Name
from unittest.mock import patch

from interp_lint import InterpLint


def test_pe():
    il = InterpLint()
    ast_tree = Module([Expr(Call(Name("print"), [BinOp(Constant(1), Add(), Constant(2))]))])
    result = il.pe(ast_tree)
    assert str(result) == "print(3)"


def test_interp():
    il = InterpLint()
    ast_tree = Module([Expr(Call(Name("print"), [BinOp(Constant(1), Add(), Constant(2))]))])
    with patch("builtins.print") as mock_print:
        il.interp(ast_tree)
        mock_print.assert_called_once_with(3, end="\n")
