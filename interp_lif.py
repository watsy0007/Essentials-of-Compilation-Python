from ast import (
    And,
    BoolOp,
    Compare,
    Constant,
    Eq,
    Gt,
    GtE,
    If,
    IfExp,
    Lt,
    LtE,
    Name,
    Not,
    NotEq,
    Or,
    UnaryOp,
)
import operator

from interp_lvar import InterpLvar


class InterpLif(InterpLvar):
    def _is_bool_constant(self, e):
        return isinstance(e, Constant) and isinstance(e.value, bool)

    def pe_boolop(self, op, values, env):
        left = self.pe_exp(values[0], env)

        if isinstance(op, And):
            if self._is_bool_constant(left):
                if not left.value:
                    return Constant(False)
                right = self.pe_exp(values[1], env)
                if self._is_bool_constant(right):
                    return Constant(right.value)
                return right
            right = self.pe_exp(values[1], env)
            if self._is_bool_constant(right) and not right.value:
                return Constant(False)
            return BoolOp(op, [left, right])

        if isinstance(op, Or):
            if self._is_bool_constant(left):
                if left.value:
                    return Constant(True)
                right = self.pe_exp(values[1], env)
                if self._is_bool_constant(right):
                    return Constant(right.value)
                return right
            right = self.pe_exp(values[1], env)
            if self._is_bool_constant(right) and right.value:
                return Constant(True)
            return BoolOp(op, [left, right])

        return BoolOp(op, [left, self.pe_exp(values[1], env)])

    def pe_compare(self, left, op, right, env):
        l_e = self.pe_exp(left, env)
        r_e = self.pe_exp(right, env)

        cmp_ops = {
            Eq: operator.eq,
            NotEq: operator.ne,
            Lt: operator.lt,
            LtE: operator.le,
            Gt: operator.gt,
            GtE: operator.ge,
        }
        fn = cmp_ops.get(type(op))

        # Constant fold if both operands are constants
        if fn and isinstance(l_e, Constant) and isinstance(r_e, Constant):
            return Constant(fn(l_e.value, r_e.value))

        return Compare(l_e, [op], [r_e])

    def pe_stmts(self, stmts, env):
        new_env = env
        new_stmts = []
        for stmt in stmts:
            stmt_pe, new_env = self.pe_stmt(stmt, new_env)
            if stmt_pe:
                new_stmts.append(stmt_pe)
        return new_stmts, new_env

    def pe_exp(self, e, env):
        match e:
            case BoolOp(op, values):
                return self.pe_boolop(op, values, env)
            case Compare(left, [op], [right]):
                return self.pe_compare(left, op, right, env)
            case UnaryOp(Not(), value):
                v = self.pe_exp(value, env)
                if self._is_bool_constant(v):
                    return Constant(not v.value)
                return UnaryOp(Not(), v)
            case IfExp(test, body, orelse):
                test_pe = self.pe_exp(test, env)
                if self._is_bool_constant(test_pe):
                    return self.pe_exp(body if test_pe.value else orelse, env)
                return IfExp(test_pe, self.pe_exp(body, env), self.pe_exp(orelse, env))
            case Constant(v) if isinstance(v, bool):
                return e
            case _:
                return super().pe_exp(e, env)

    def pe_stmt(self, s, env):
        match s:
            case If(test, body, orelse):
                test_pe = self.pe_exp(test, env)
                body_pe, then_env = self.pe_stmts(body, env.copy())
                orelse_pe, else_env = self.pe_stmts(orelse, env.copy())
                if self._is_bool_constant(test_pe):
                    new_env = then_env if test_pe.value else else_env
                else:
                    new_env = env
                return If(test_pe, body_pe, orelse_pe), new_env
            case _:
                return super().pe_stmt(s, env)

    def interp_exp(self, e, env):
        match e:
            case BoolOp(And(), [e1, e2]):
                left = self.interp_exp(e1, env)
                if not bool(left):
                    return False
                return bool(self.interp_exp(e2, env))
            case BoolOp(Or(), [e1, e2]):
                left = self.interp_exp(e1, env)
                if bool(left):
                    return True
                return bool(self.interp_exp(e2, env))
            case Compare(left, [op], [right]):
                l_v = self.interp_exp(left, env)
                r_v = self.interp_exp(right, env)
                cmp_ops = {
                    Eq: operator.eq,
                    NotEq: operator.ne,
                    Lt: operator.lt,
                    LtE: operator.le,
                    Gt: operator.gt,
                    GtE: operator.ge,
                }
                fn = cmp_ops[type(op)]
                return fn(l_v, r_v)
            case UnaryOp(Not(), value):
                return not bool(self.interp_exp(value, env))
            case IfExp(test, body, orelse):
                if bool(self.interp_exp(test, env)):
                    return self.interp_exp(body, env)
                return self.interp_exp(orelse, env)
            case Constant(v) if isinstance(v, bool):
                return v
            case _:
                return super().interp_exp(e, env)

    def interp_stmt(self, s, env, cont):
        match s:
            case If(test, body, orelse):
                if bool(self.interp_exp(test, env)):
                    return self.interp_stmts(body + cont, env)
                return self.interp_stmts(orelse + cont, env)
            case _:
                return super().interp_stmt(s, env, cont)
