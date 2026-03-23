from ast_nodes import Add, BinOp, Call, Constant, Expr, Module, Name, USub, UnaryOp


def build_book_style_program() -> Module:
    eight = Constant(8)
    neg_eight = UnaryOp(USub(), eight)
    read = Call(Name("input_int"), [])
    ast1_1 = BinOp(read, Add(), neg_eight)
    return Module([Expr(Call(Name("print"), [ast1_1]))])


def test_build_book_style_program_shape():
    program = build_book_style_program()

    assert isinstance(program, Module)
    assert len(program.body) == 1

    stmt = program.body[0]
    assert isinstance(stmt, Expr)

    call_print = stmt.value
    assert isinstance(call_print, Call)
    assert isinstance(call_print.func, Name)
    assert call_print.func.id == "print"
    assert len(call_print.args) == 1

    expr = call_print.args[0]
    assert isinstance(expr, BinOp)
    assert isinstance(expr.left, Call)
    assert isinstance(expr.left.func, Name)
    assert expr.left.func.id == "input_int"
    assert expr.left.args == []
    assert isinstance(expr.op, Add)
    assert isinstance(expr.right, UnaryOp)
    assert isinstance(expr.right.op, USub)
    assert isinstance(expr.right.operand, Constant)
    assert expr.right.operand.value == 8
