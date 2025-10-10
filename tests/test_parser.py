from lark import Lark

from parser import ToyTransformer, grammar


def test_parser():
    code = """
    x = 1
    print(x)
    """
    la = Lark(grammar, parser="lalr", transformer=ToyTransformer())
    result = la.parse(code)
    assert (
        repr(result)
        == "Module([Assign([Name('x')], Constant(1)), Expr(Call(Name('print'), [Name('x')]))])"
    )

    assert str(result) == "x = 1\nprint(x)"
