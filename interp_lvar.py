from ast import Assign, Name

from interp_lint import InterpLint


class InterpLvar(InterpLint):
    def pe_exp(self, e, env):
        match e:
            case Name(id):
                return env[id]
            case _:
                return super().pe_exp(e, env)

    def pe_stmt(self, s, env):
        match s:
            case Assign([Name(id)], value):
                v = self.pe_exp(value, env)
                env[id] = v
                return None, env
            case _:
                return super().pe_stmt(s, env)

    def interp_exp(self, e, env):
        match e:
            case Name(id):
                return env[id]
            case _:
                return super().interp_exp(e, env)

    def interp_stmt(self, s, env, cont):
        match s:
            case Assign([Name(id)], value):
                env[id] = self.interp_exp(value, env)
                return self.interp_stmts(cont, env)
            case _:
                return super().interp_stmt(s, env, cont)
