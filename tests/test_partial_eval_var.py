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
from partial_eval_var import PartialEvalVar


def test_pe_exp_replaces_known_variable_with_constant():
    pe = PartialEvalVar(Module([]))

    result = pe.pe_exp(BinOp(Name("x"), Add(), Constant(2)), {"x": 40})

    assert isinstance(result, int)
    assert result == 42


def test_pe_exp_keeps_unknown_variable_symbolic():
    pe = PartialEvalVar(Module([]))

    result = pe.pe_exp(BinOp(Name("x"), Add(), Constant(2)), {})

    assert isinstance(result, BinOp)
    assert isinstance(result.left, Name)
    assert result.left.id == "x"
    assert isinstance(result.op, Add)
    assert isinstance(result.right, Constant)
    assert result.right.value == 2


def test_pe_stmt_tracks_constant_assignments_in_environment():
    pe = PartialEvalVar(Module([]))
    env = {}

    stmt = pe.pe_stmt(
        Assign([Name("x")], BinOp(Constant(10), Add(), Constant(32))), env
    )

    assert env == {"x": 42}
    assert isinstance(stmt, Assign)
    assert stmt.targets[0].id == "x"
    assert isinstance(stmt.value, Constant)
    assert stmt.value.value == 42


def test_pe_stmt_kills_binding_when_expression_is_not_constant():
    pe = PartialEvalVar(Module([]))
    env = {"x": 1}

    stmt = pe.pe_stmt(Assign([Name("x")], Call(Name("input_int"), [])), env)

    assert env == {}
    assert isinstance(stmt.value, Call)
    assert stmt.value.func.id == "input_int"


def test_pe_module_propagates_constants_across_assignments():
    program = Module(
        [
            Assign([Name("x")], BinOp(Constant(10), Add(), Constant(5))),
            Assign([Name("y")], BinOp(Name("x"), Add(), Constant(2))),
            Expr(Call(Name("print"), [Name("y")])),
        ]
    )

    out_program = PartialEvalVar(program).pe()

    assert isinstance(out_program.body[0].value, Constant)
    assert out_program.body[0].value.value == 15
    assert isinstance(out_program.body[1].value, Constant)
    assert out_program.body[1].value.value == 17
    assert isinstance(out_program.body[2].value, Call)
    assert isinstance(out_program.body[2].value.args[0], Constant)
    assert out_program.body[2].value.args[0].value == 17


def test_pe_module_stops_propagation_after_input_reassignment():
    program = Module(
        [
            Assign([Name("x")], Constant(5)),
            Assign([Name("x")], Call(Name("input_int"), [])),
            Assign([Name("y")], BinOp(Name("x"), Add(), Constant(1))),
            Expr(Call(Name("print"), [Name("y")])),
        ]
    )

    out_program = PartialEvalVar(program).pe()

    third = out_program.body[2]
    assert isinstance(third, Assign)
    assert isinstance(third.value, BinOp)
    assert isinstance(third.value.left, Name)
    assert third.value.left.id == "x"
    assert isinstance(third.value.right, Constant)
    assert third.value.right.value == 1


def test_pe_handles_unary_with_known_variable():
    program = Module(
        [
            Assign([Name("x")], Constant(5)),
            Assign([Name("y")], UnaryOp(USub(), Name("x"))),
        ]
    )

    out_program = PartialEvalVar(program).pe()

    assert isinstance(out_program.body[1], Assign)
    assert isinstance(out_program.body[1].value, Constant)
    assert out_program.body[1].value.value == -5
