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


class PartialEvalInt:
    def __init__(self, module: Module):
        self.module = module

    def pe_neg(self, value):
        match value:
            case int() as n:
                return -n
            case _:
                return UnaryOp(USub(), self._to_exp(value))

    def pe_add(self, left, right):
        match (left, right):
            case (int() as l, int() as r):
                return l + r
            case _:
                return BinOp(self._to_exp(left), Add(), self._to_exp(right))

    def pe_sub(self, left, right):
        match (left, right):
            case (int() as l, int() as r):
                return l - r
            case _:
                return BinOp(self._to_exp(left), Sub(), self._to_exp(right))

    def pe_exp(self, exp):
        match exp:
            case Constant(value=value):
                return value
            case Call(func=Name(id="input_int"), args=[]):
                return exp
            case UnaryOp(op=USub(), operand=operand):
                return self.pe_neg(self.pe_exp(operand))
            case BinOp(left=left, op=Add(), right=right):
                return self.pe_add(self.pe_exp(left), self.pe_exp(right))
            case BinOp(left=left, op=Sub(), right=right):
                return self.pe_sub(self.pe_exp(left), self.pe_exp(right))
            case _:
                raise ValueError(f"unsupported expression: {exp!r}")

    def pe_stmt(self, stmt):
        match stmt:
            case Expr(value=Call(func=Name(id="print"), args=[arg])):
                return Expr(Call(Name("print"), [self._to_exp(self.pe_exp(arg))]))
            case Expr(value=value):
                return Expr(self._to_exp(self.pe_exp(value)))
            case _:
                raise ValueError(f"unsupported statement: {stmt!r}")

    def pe_stmts(self, stmts):
        return [self.pe_stmt(stmt) for stmt in stmts]

    def pe(self):
        return Module(self.pe_stmts(self.module.body))

    @staticmethod
    def _to_exp(value):
        match value:
            case int() as n:
                return Constant(n)
            case _:
                return value
