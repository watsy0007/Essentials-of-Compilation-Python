from ast import (
    BinOp,
    BoolOp,
    Compare,
    Constant,
    Eq,
    If,
    IfExp,
    Not,
    NotEq,
    Sub,
    UnaryOp,
)
from type_check_l_var import TypeCheckLvar

class TypeCheckLif(TypeCheckLvar):
    def type_check_exp(self, e, env):
        match e:
            case Constant(value) if isinstance(value, bool):
                return bool
            case BinOp(left, Sub(), right):
                l = self.type_check_exp(left, env); self.check_type_equal(l, int, left)
                r = self.type_check_exp(right, env); self.check_type_equal(r, int, right)
                return int
            case UnaryOp(Not(), v):
                t = self.type_check_exp(v, env); self.check_type_equal(t, bool, v)
                return bool
            case BoolOp(op, values):
                left = values[0]; right = values[1]
                l = self.type_check_exp(left, env); self.check_type_equal(l, bool, left)
                r = self.type_check_exp(right, env); self.check_type_equal(r, bool, right)
                return bool
            case Compare(left, [cmp], [right]) if isinstance(cmp, Eq) \
                                               or isinstance(cmp, NotEq):
                l = self.type_check_exp(left, env)
                r = self.type_check_exp(right, env)
                self.check_type_equal(l, r, e)
                return bool
            case Compare(left, [cmp], [right]):
                l = self.type_check_exp(left, env); self.check_type_equal(l, int, left)
                r = self.type_check_exp(right, env); self.check_type_equal(r, int, right)
                return bool
            case IfExp(test, body, orelse):
                t = self.type_check_exp(test, env); self.check_type_equal(bool, t, test)
                b = self.type_check_exp(body, env)
                o = self.type_check_exp(orelse, env)
                self.check_type_equal(b, o, e)
                return b
            case _:
                return super().type_check_exp(e, env)

    def type_check_stmts(self, ss, env):
        if len(ss) == 0:
            return
        match ss[0]:
            case If(test, body, orelse):
                t = self.type_check_exp(test, env); self.check_type_equal(bool, t, test)
                b = self.type_check_stmts(body, env)
                o = self.type_check_stmts(orelse, env)
                self.check_type_equal(b, o, ss[0])
                return self.type_check_stmts(ss[1:], env)
            case _:
                return super().type_check_stmts(ss, env)
