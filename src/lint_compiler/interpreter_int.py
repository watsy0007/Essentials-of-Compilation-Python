from .ast_nodes import (
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


class InterpeterInt:
    def __init__(self, module: Module):
        self.module = module

    def interp_exp(self, exp):
        match exp:
            case Constant(value=value):
                return value
            case Call(func=Name(id="input_int"), args=[]):
                return int(input())
            case Call():
                raise ValueError(f"unsupported call expression: {exp!r}")
            case UnaryOp(op=USub(), operand=operand):
                return -self.interp_exp(operand)
            case UnaryOp(op=op):
                raise ValueError(f"unsupported unary operator: {op!r}")
            case BinOp(left=left, op=Add(), right=right):
                return self.interp_exp(left) + self.interp_exp(right)
            case BinOp(left=left, op=Sub(), right=right):
                return self.interp_exp(left) - self.interp_exp(right)
            case BinOp(op=op):
                raise ValueError(f"unsupported binary operator: {op!r}")
            case _:
                raise ValueError(f"unsupported expression: {exp!r}")

    def interp_stmt(self, stmt):
        match stmt:
            case Expr(value=Call(func=Name(id="print"), args=[arg])):
                print(self.interp_exp(arg))
            case Expr(value=Call(func=Name(id="print"), args=args)):
                raise ValueError(
                    f"print expects one argument: Call(Name('print'), {args!r})"
                )
            case Expr(value=value):
                self.interp_exp(value)
            case _:
                raise ValueError(f"unsupported statement: {stmt!r}")

    def interp_stmts(self, stmts=None):
        if stmts is None:
            stmts = self.module.body
        for stmt in stmts:
            self.interp_stmt(stmt)

    def interp(self):
        self.interp_stmts(self.module.body)
