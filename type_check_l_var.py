from ast import (
    Add,
    Assign,
    BinOp,
    Call,
    Constant,
    Expr,
    Module,
    Name,
    Sub,
    UnaryOp,
    USub,
)

class TypeCheckLvar:
    def check_type_equal(self, t1, t2, e):
        if t1 != t2:
            msg = 'error: ' + repr(t1) + ' != ' + repr(t2) + ' in ' + repr(e)
            raise Exception(msg)

    def type_check_exp(self, e, env):
        match e:
            case BinOp(left, (Add() | Sub()), right):
                l = self.type_check_exp(left, env)
                self.check_type_equal(l, int, left)
                r = self.type_check_exp(right, env)
                self.check_type_equal(r, int, right)
                return int
            case UnaryOp(USub(), v):
                t = self.type_check_exp(v, env)
                self.check_type_equal(t, int, v)
                return int
            case Name(id):
                return env[id]
            case Constant(value) if isinstance(value, int):
                return int
            case Call(Name('input_int'), []):
                return int
            case _:
                raise Exception(f"type_check_exp: unexpected {e}")

    def type_check_stmts(self, ss, env):
        if len(ss) == 0:
            return
        match ss[0]:
            case Assign([Name(id)], value):
                t = self.type_check_exp(value, env)
                if id in env:
                    self.check_type_equal(env[id], t, value)
                else:
                    env[id] = t
                return self.type_check_stmts(ss[1:], env)
            case Expr(Call(Name('print'), [arg])):
                t = self.type_check_exp(arg, env)
                self.check_type_equal(t, int, arg)
                return self.type_check_stmts(ss[1:], env)
            case Expr(value):
                self.type_check_exp(value, env)
                return self.type_check_stmts(ss[1:], env)
            case _:
                raise Exception(f"type_check_stmts: unexpected {ss[0]}")

    def type_check_P(self, p):
        match p:
            case Module(body):
                self.type_check_stmts(body, {})
