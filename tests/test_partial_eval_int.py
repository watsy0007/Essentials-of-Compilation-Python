from ast_nodes import (
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
from partial_eval_int import PartialEvalInt


def test_pe_exp_folds_to_integer():
    exp = BinOp(
        BinOp(Constant(10), Add(), Constant(2)), Sub(), UnaryOp(USub(), Constant(3))
    )

    pe = PartialEvalInt(Module([]))
    result = pe.pe_exp(exp)

    assert result == 15


def test_pe_exp_keeps_input_int_symbolic_and_folds_constants():
    exp = BinOp(
        Call(Name("input_int"), []), Add(), BinOp(Constant(5), Add(), Constant(6))
    )

    pe = PartialEvalInt(Module([]))
    result = pe.pe_exp(exp)

    assert isinstance(result, BinOp)
    assert isinstance(result.left, Call)
    assert isinstance(result.left.func, Name)
    assert result.left.func.id == "input_int"
    assert result.left.args == []
    assert isinstance(result.op, Add)
    assert isinstance(result.right, Constant)
    assert result.right.value == 11


def test_pe_neg_add_sub_auxiliaries():
    pe = PartialEvalInt(Module([]))

    assert pe.pe_neg(8) == -8
    assert pe.pe_add(3, 4) == 7
    assert pe.pe_sub(10, 2) == 8

    symbolic = Call(Name("input_int"), [])
    neg_symbolic = pe.pe_neg(symbolic)
    assert isinstance(neg_symbolic, UnaryOp)
    assert isinstance(neg_symbolic.op, USub)
    assert neg_symbolic.operand is symbolic


def test_pe_module_rewrites_statements():
    program = Module(
        [
            Expr(Call(Name("print"), [BinOp(Constant(5), Add(), Constant(7))])),
            Expr(BinOp(Call(Name("input_int"), []), Sub(), Constant(2))),
        ]
    )

    pe = PartialEvalInt(program)
    out_program = pe.pe()

    assert isinstance(out_program, Module)
    assert len(out_program.body) == 2

    print_stmt = out_program.body[0]
    assert isinstance(print_stmt, Expr)
    assert isinstance(print_stmt.value, Call)
    assert print_stmt.value.func.id == "print"
    assert isinstance(print_stmt.value.args[0], Constant)
    assert print_stmt.value.args[0].value == 12

    expr_stmt = out_program.body[1]
    assert isinstance(expr_stmt.value, BinOp)
    assert isinstance(expr_stmt.value.left, Call)
    assert isinstance(expr_stmt.value.op, Sub)
    assert isinstance(expr_stmt.value.right, Constant)
    assert expr_stmt.value.right.value == 2
