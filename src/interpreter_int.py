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


class InterpeterInt:
    def __init__(self, module: Module):
        self.module = module

    def interp_exp(self, exp, env=None):
        match exp:
            case Constant(value=value):
                return value
            case Call(func=Name(id="input_int"), args=[]):
                return int(input())
            case Call():
                raise ValueError(f"unsupported call expression: {exp!r}")
            case UnaryOp(op=USub(), operand=operand):
                return -self.interp_exp(operand, env)
            case UnaryOp(op=op):
                raise ValueError(f"unsupported unary operator: {op!r}")
            case BinOp(left=left, op=Add(), right=right):
                return self.interp_exp(left, env) + self.interp_exp(right, env)
            case BinOp(left=left, op=Sub(), right=right):
                return self.interp_exp(left, env) - self.interp_exp(right, env)
            case BinOp(op=op):
                raise ValueError(f"unsupported binary operator: {op!r}")
            case _:
                raise ValueError(f"unsupported expression: {exp!r}")

    def interp_stmt(self, stmt, cont=None, env=None):
        if cont is None:
            cont = []
        if env is None:
            env = {}
        match stmt:
            case Expr(value=Call(func=Name(id="print"), args=[arg])):
                print(self.interp_exp(arg, env))
            case Expr(value=Call(func=Name(id="print"), args=args)):
                raise ValueError(
                    f"print expects one argument: Call(Name('print'), {args!r})"
                )
            case Expr(value=value):
                self.interp_exp(value, env)
            case _:
                raise ValueError(f"unsupported statement: {stmt!r}")
        return self.interp_stmts(cont, env)

    def interp_stmts(self, stmts=None, env=None):
        if stmts is None:
            stmts = self.module.body
        if env is None:
            env = {}
        if not stmts:
            return env
        return self.interp_stmt(stmts[0], stmts[1:], env)

    def interp(self, env=None):
        return self.interp_stmts(self.module.body, env)
