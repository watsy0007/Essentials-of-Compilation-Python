from lint_compiler.ast_nodes import (
    Add,
    BinOp,
    Call,
    Constant,
    Expr,
    Module,
    Name,
    USub,
    UnaryOp,
)


def test_construct_book_expression_ast():
    eight = Constant(8)
    neg_eight = UnaryOp(USub(), eight)
    read = Call(Name("input_int"), [])
    ast1_1 = BinOp(read, Add(), neg_eight)

    assert eight.value == 8

    assert isinstance(neg_eight.op, USub)
    assert neg_eight.operand is eight

    assert isinstance(read.func, Name)
    assert read.func.id == "input_int"
    assert read.args == []

    assert ast1_1.left is read
    assert isinstance(ast1_1.op, Add)
    assert ast1_1.right is neg_eight


def test_construct_lint_program_ast():
    eight = Constant(8)
    neg_eight = UnaryOp(USub(), eight)
    read = Call(Name("input_int"), [])
    ast1_1 = BinOp(read, Add(), neg_eight)

    stmt = Expr(Call(Name("print"), [ast1_1]))
    program = Module([stmt])

    assert len(program.body) == 1
    assert isinstance(program.body[0], Expr)

    print_call = program.body[0].value
    assert isinstance(print_call, Call)
    assert isinstance(print_call.func, Name)
    assert print_call.func.id == "print"
    assert print_call.args == [ast1_1]
