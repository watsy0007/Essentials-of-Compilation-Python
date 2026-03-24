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
from x86_ast import Callq, Deref, Immediate, Instr, Reg, Retq, Var, X86Program


class CompilerVar:
    def __init__(self):
        self._tmp_counter = 0

    def _new_tmp(self):
        name = f"tmp_{self._tmp_counter}"
        self._tmp_counter += 1
        return Name(name)

    def remove_complex_operands(self, module):
        self._tmp_counter = 0
        body = []
        for stmt in module.body:
            body.extend(self._rco_stmt(stmt))
        return Module(body)

    def _rco_stmt(self, stmt):
        match stmt:
            case Assign(targets=[Name(id=_) as target], value=value):
                simple_value, setup = self._rco_exp(value)
                return setup + [Assign([target], simple_value)]
            case Expr(value=Call(func=Name(id="print"), args=[arg])):
                atom, setup = self._rco_atom(arg)
                return setup + [Expr(Call(Name("print"), [atom]))]
            case Expr(value=value):
                simple_value, setup = self._rco_exp(value)
                return setup + [Expr(simple_value)]
            case _:
                raise ValueError(
                    f"unsupported statement in remove_complex_operands: {stmt!r}"
                )

    def _rco_atom(self, exp):
        simple_exp, setup = self._rco_exp(exp)
        if isinstance(simple_exp, (Constant, Name)):
            return simple_exp, setup
        tmp = self._new_tmp()
        return tmp, setup + [Assign([tmp], simple_exp)]

    def _rco_exp(self, exp):
        match exp:
            case Constant() | Name():
                return exp, []
            case Call(func=Name(id="input_int"), args=[]):
                return exp, []
            case Call():
                raise ValueError(
                    f"unsupported call expression in remove_complex_operands: {exp!r}"
                )
            case UnaryOp(op=USub(), operand=operand):
                atom, setup = self._rco_atom(operand)
                return UnaryOp(USub(), atom), setup
            case UnaryOp(op=op):
                raise ValueError(
                    f"unsupported unary operator in remove_complex_operands: {op!r}"
                )
            case BinOp(left=left, op=Add() as op, right=right):
                left_atom, left_setup = self._rco_atom(left)
                right_atom, right_setup = self._rco_atom(right)
                return BinOp(left_atom, op, right_atom), left_setup + right_setup
            case BinOp(left=left, op=Sub() as op, right=right):
                left_atom, left_setup = self._rco_atom(left)
                right_atom, right_setup = self._rco_atom(right)
                return BinOp(left_atom, op, right_atom), left_setup + right_setup
            case BinOp(op=op):
                raise ValueError(
                    f"unsupported binary operator in remove_complex_operands: {op!r}"
                )
            case _:
                raise ValueError(
                    f"unsupported expression in remove_complex_operands: {exp!r}"
                )

    def select_instructions(self, module):
        instrs = []
        for stmt in module.body:
            instrs.extend(self._select_stmt(stmt))
        return X86Program(instrs)

    def _select_stmt(self, stmt):
        match stmt:
            case Assign(targets=[Name(id=var)], value=value):
                return self._select_assign(var, value)
            case Expr(value=Call(func=Name(id="print"), args=[arg])):
                src = self._select_atom(arg)
                return [Instr("movq", [src, Reg("rdi")]), Callq("_print_int", 1)]
            case Expr(value=Call(func=Name(id="input_int"), args=[])):
                return [Callq("_read_int", 0)]
            case Expr(value=value):
                raise ValueError(
                    f"unsupported expression statement in select_instructions: {value!r}"
                )
            case _:
                raise ValueError(
                    f"unsupported statement in select_instructions: {stmt!r}"
                )

    def _select_assign(self, var, value):
        dst = Var(var)
        match value:
            case Constant() | Name():
                return [Instr("movq", [self._select_atom(value), dst])]
            case UnaryOp(op=USub(), operand=operand):
                src = self._select_atom(operand)
                instrs = []
                if src != dst:
                    instrs.append(Instr("movq", [src, dst]))
                instrs.append(Instr("negq", [dst]))
                return instrs
            case BinOp(left=left, op=Add(), right=right):
                left_arg = self._select_atom(left)
                right_arg = self._select_atom(right)
                instrs = []
                if left_arg != dst:
                    instrs.append(Instr("movq", [left_arg, dst]))
                instrs.append(Instr("addq", [right_arg, dst]))
                return instrs
            case BinOp(left=left, op=Sub(), right=right):
                left_arg = self._select_atom(left)
                right_arg = self._select_atom(right)
                instrs = []
                if left_arg != dst:
                    instrs.append(Instr("movq", [left_arg, dst]))
                instrs.append(Instr("subq", [right_arg, dst]))
                return instrs
            case Call(func=Name(id="input_int"), args=[]):
                return [Callq("_read_int", 0), Instr("movq", [Reg("rax"), dst])]
            case _:
                raise ValueError(
                    f"unsupported assignment value in select_instructions: {value!r}"
                )

    def _select_atom(self, atom):
        match atom:
            case Constant(value=value):
                return Immediate(value)
            case Name(id=var):
                return Var(var)
            case _:
                raise ValueError(f"expected atomic expression, got {atom!r}")

    def assign_homes(self, program):
        vars_in_use = []
        seen = set()
        for instr in program.body:
            if isinstance(instr, Instr):
                for arg in instr.args:
                    if isinstance(arg, Var) and arg.name not in seen:
                        seen.add(arg.name)
                        vars_in_use.append(arg.name)

        homes = {}
        for index, name in enumerate(vars_in_use, start=1):
            homes[name] = Deref("rbp", -8 * index)

        stack_space = len(vars_in_use) * 8
        if stack_space % 16 != 0:
            stack_space += 8

        body = [self._assign_instr_homes(instr, homes) for instr in program.body]
        return X86Program(body, stack_space=stack_space, homes=homes)

    def _assign_instr_homes(self, instr, homes):
        if isinstance(instr, Instr):
            return Instr(
                instr.op, [self._assign_arg_home(arg, homes) for arg in instr.args]
            )
        return instr

    def _assign_arg_home(self, arg, homes):
        if isinstance(arg, Var):
            return homes[arg.name]
        return arg

    def patch_instructions(self, program):
        patched = []
        for instr in program.body:
            patched.extend(self._patch_instr(instr))
        return X86Program(
            patched,
            stack_space=program.stack_space,
            main_label=program.main_label,
            homes=program.homes,
        )

    def _patch_instr(self, instr):
        if not isinstance(instr, Instr):
            return [instr]
        if instr.op == "movq" and instr.args[0] == instr.args[1]:
            return []
        if instr.op in ("movq", "addq", "subq"):
            src, dst = instr.args
            if isinstance(src, Deref) and isinstance(dst, Deref):
                return [
                    Instr("movq", [src, Reg("rax")]),
                    Instr(instr.op, [Reg("rax"), dst]),
                ]
        return [instr]

    def prelude_and_conclusion(self, program):
        prelude = [
            Instr("pushq", [Reg("rbp")]),
            Instr("movq", [Reg("rsp"), Reg("rbp")]),
        ]
        if program.stack_space > 0:
            prelude.append(Instr("subq", [Immediate(program.stack_space), Reg("rsp")]))

        conclusion = []
        if program.stack_space > 0:
            conclusion.append(
                Instr("addq", [Immediate(program.stack_space), Reg("rsp")])
            )
        conclusion.extend(
            [
                Instr("popq", [Reg("rbp")]),
                Retq(),
            ]
        )

        return X86Program(
            prelude + program.body + conclusion,
            stack_space=program.stack_space,
            main_label=program.main_label,
            homes=program.homes,
        )

    def compile(self, module):
        no_complex = self.remove_complex_operands(module)
        selected = self.select_instructions(no_complex)
        homed = self.assign_homes(selected)
        patched = self.patch_instructions(homed)
        return self.prelude_and_conclusion(patched)
