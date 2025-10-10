from ast import Add, BinOp, Call, Constant, Expr, Module, Name, Sub, UnaryOp, USub

from utils import add64, input_int, neg64, sub64


class InterpLint:
    def pe_neg(self, r, env):
        match r:
            case Constant(v):
                return Constant(neg64(v))
            case _:
                return UnaryOp(USub(), r)

    def pe_add(self, r1, r2, env):
        match (r1, r2):
            case (Constant(v1), Constant(v2)):
                return Constant(add64(v1, v2))
            case _:
                return BinOp(r1, Add(), r2)

    def pe_sub(self, r1, r2, env):
        match (r1, r2):
            case (Constant(v1), Constant(v2)):
                return Constant(sub64(v1, v2))
            case _:
                return BinOp(r1, Sub(), r2)

    def pe_exp(self, e, env):
        match e:
            case BinOp(e1, Add(), e2):
                return self.pe_add(self.pe_exp(e1, env), self.pe_exp(e2, env), env)
            case BinOp(e1, Sub(), e2):
                return self.pe_sub(self.pe_exp(e1, env), self.pe_exp(e2, env), env)
            case UnaryOp(USub(), e1):
                return self.pe_neg(self.pe_exp(e1, env), env)
            case Constant(_):
                return e
            case Call(Name("input_int"), []):
                return e

    def interp_exp(self, e, env):
        match e:
            case BinOp(e1, Add(), e2):
                l_e = self.interp_exp(e1, env)
                r_e = self.interp_exp(e2, env)
                return add64(l_e, r_e)
            case BinOp(e1, Sub(), e2):
                l_e = self.interp_exp(e1, env)
                r_e = self.interp_exp(e2, env)
                return sub64(l_e, r_e)
            case UnaryOp(USub(), e1):
                return neg64(self.interp_exp(e1, env))
            case Constant(value):
                return value
            case Call(Name("input_int"), []):
                return input_int()
            case _:
                raise Exception("error in interp_exp, unexpected " + repr(e))

    def pe_stmt(self, s, env):
        match s:
            case Expr(Call(Name("print"), [arg])):
                return Expr(Call(Name("print"), [self.pe_exp(arg, env)])), env
            case Expr(arg):
                return Expr(self.pe_exp(arg, env)), env

    def pe(self, p, env: dict | None = None):
        new_env = env or {}
        match p:
            case Module(body):
                stmts = []
                for s in body:
                    stmt, new_env = self.pe_stmt(s, new_env)
                    if not stmt:
                        continue
                    stmts.append(stmt)
                return Module(stmts)  # type: ignore

    def interp_stmt(self, s, env, cont):
        match s:
            case Expr(Call(Name("print"), [arg])):
                val = self.interp_exp(arg, env)
                print(val, end="\n")
                return self.interp_stmts(cont, env)
            case Expr(value):
                self.interp_exp(value, env)
                return self.interp_stmts(cont, env)
            case _:
                raise Exception("error in interp_stmt, unexpected " + repr(s))

    def interp_stmts(self, ss, env):
        match ss:
            case []:
                return 0
            case [s, *ss]:
                return self.interp_stmt(s, env, ss)

    def interp(self, p):
        match p:
            case Module(body):
                return self.interp_stmts(body, {})
            case _:
                raise Exception("error in interp, unexpected " + repr(p))
