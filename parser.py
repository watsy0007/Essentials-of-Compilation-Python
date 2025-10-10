from ast import Add, Assign, BinOp, Call, Constant, Expr, Module, Name, Sub, UnaryOp, USub

from lark import Lark, Transformer

from interp_lvar import InterpLvar

grammar = r"""
%import common.WS
%import common.CNAME -> NAME
%import common.NEWLINE
%import common.INT
_NL: NEWLINE+

exp: exp "+" exp_hi             -> add
    | exp "-" exp               -> sub
    | NAME                      -> name
    | exp_hi

exp_hi: INT                     -> int
    | "input_int" "(" ")"       -> input_int
    | "-" exp                   -> usub
    | "(" exp ")"               -> paren

stmt: exp                       -> expr
    | "print" "(" exp ")"       -> print
    | NAME "=" exp              -> assign

stmt_list:                      -> empty_stmt
    | stmt                      -> single_stmt
    | stmt _NL stmt_list        -> add_stmt

start: stmt_list                -> module

%ignore WS
"""


class ToyTransformer(Transformer):
    int = lambda self, n: Constant(int(n[0].value))
    sub = lambda self, n: BinOp(n[0], Sub(), n[1])
    add = lambda self, n: BinOp(n[0], Add(), n[1])
    usub = lambda self, n: UnaryOp(USub(), n[0])

    name = lambda self, n: Name(n[0].value)
    exp = lambda self, n: n[0]
    expr = lambda self, n: Expr(n[0])
    print = lambda self, n: Expr(Call(Name("print"), [n[0]]))
    assign = lambda self, n: Assign([Name(n[0].value)], n[1])

    empty_stmt = lambda self, n: []
    single_stmt = lambda self, n: [n[0]]
    add_stmt = lambda self, n: [n[0]] + n[1]
    module = lambda self, n: Module(n[0])


def main():
    la = Lark(grammar, parser="lalr")

    code = """
x = 10
print(1 + 2 - 5)
print(x - 1)
    """
    tree = la.parse(code)
    print("tree:\n", tree.pretty())
    result = ToyTransformer().transform(tree)
    print("original:\nast:\t", repr(result), f"\ncode:\n>>>>>\n{result}", "\n<<<<<\n")

    v = InterpLvar().pe(result)
    print("after partial evaluation:\nast:\t", repr(v), f"\ncode:\n>>>>>\n{v}", "\n<<<<<\n")

    print("execution:")
    InterpLvar().interp(v)


if __name__ == "__main__":
    main()
