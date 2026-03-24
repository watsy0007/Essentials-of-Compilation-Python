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
from partial_eval_int import PartialEvalInt


class PartialEvalVar(PartialEvalInt):
    def pe_exp(self, exp, env=None):
        if env is None:
            env = {}
        match exp:
            case Constant(value=value):
                return value
            case Name(id=var):
                if var in env:
                    return env[var]
                return exp
            case Call(func=Name(id="input_int"), args=[]):
                return exp
            case UnaryOp(op=USub(), operand=operand):
                return self.pe_neg(self.pe_exp(operand, env))
            case BinOp(left=left, op=Add(), right=right):
                return self.pe_add(self.pe_exp(left, env), self.pe_exp(right, env))
            case BinOp(left=left, op=Sub(), right=right):
                return self.pe_sub(self.pe_exp(left, env), self.pe_exp(right, env))
            case _:
                raise ValueError(f"unsupported expression: {exp!r}")

    def pe_stmt(self, stmt, env=None):
        if env is None:
            env = {}
        match stmt:
            case Assign(targets=[Name(id=var)], value=value):
                pe_value = self.pe_exp(value, env)
                if isinstance(pe_value, int):
                    env[var] = pe_value
                else:
                    env.pop(var, None)
                return Assign([Name(var)], self._to_exp(pe_value))
            case Expr(value=Call(func=Name(id="print"), args=[arg])):
                return Expr(Call(Name("print"), [self._to_exp(self.pe_exp(arg, env))]))
            case Expr(value=value):
                return Expr(self._to_exp(self.pe_exp(value, env)))
            case _:
                raise ValueError(f"unsupported statement: {stmt!r}")

    def pe_stmts(self, stmts, env=None):
        if env is None:
            env = {}
        return [self.pe_stmt(stmt, env) for stmt in stmts]

    def pe(self):
        return Module(self.pe_stmts(self.module.body, {}))
