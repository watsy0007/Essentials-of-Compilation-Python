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
    expr,
    stmt,
)
from functools import reduce
from operator import add

from utils import generate_name, label_name
from x86_ast import Arg, Deref, Immediate, Instr, Label, Reg, Var, X86Program

Binding = tuple[Name, expr]
Temporaries = list[Binding]


class Compiler:
    def is_atomic(self, e: expr) -> bool:
        return isinstance(e, (Constant, Name))

    ############################################################################
    # Remove Complex Operands
    ############################################################################

    def roc_exp(self, e: expr, need_atomic: bool) -> tuple[expr, Temporaries]:
        if self.is_atomic(e):
            return e, []

        match e:
            case UnaryOp(op, operand):
                operand, assigns = self.roc_exp(operand, True)
                if need_atomic:
                    tmp_var = generate_name("tmp")
                    new_unary = UnaryOp(op, operand)
                    tmp_assign = Assign([Name(tmp_var)], new_unary)
                    return Name(tmp_var), assigns + [tmp_assign]
                return UnaryOp(op, operand), assigns
            case BinOp(left, op, right):
                left, left_assigns = self.roc_exp(left, True)
                right, right_assigns = self.roc_exp(right, True)
                if need_atomic:
                    temp_var = generate_name("tmp")
                    new_binop = BinOp(left, op, right)
                    tmp_assign = Assign([Name(temp_var)], new_binop)
                    return Name(temp_var), left_assigns + right_assigns + [tmp_assign]
                return BinOp(left, op, right), left_assigns + right_assigns
            case Call(Name("input_int"), []):
                return e, []

            case _:
                return e, []

    def roc_stmt(self, s: expr) -> list[stmt]:
        match s:
            case Expr(Call(Name("print"), [arg])):
                if self.is_atomic(arg):
                    return [s]
                new_value, assigns = self.roc_exp(arg, True)
                return assigns + [Expr(Call(Name("print"), [new_value]))]
            case Assign([Name(id)], arg):
                if self.is_atomic(arg):
                    return [s]
                new_value, assigns = self.roc_exp(arg, False)
                return assigns + [Assign([Name(id)], new_value)]
            case Expr(arg):
                new_expr, assigns = self.roc_exp(arg, True)
                return assigns + [Expr(new_expr)]

    def remove_complex_operands(self, p: Module) -> Module:
        match p:
            case Module(body):
                stmts = [self.roc_stmt(s) for s in body]
                return Module(reduce(add, stmts))

    ############################################################################
    # Select Instructions
    ############################################################################

    def select_arg(self, e: expr) -> tuple[list[Arg], Arg]:
        match e:
            case Constant(v):
                return [], Immediate(v)
            case Name(id):
                return [], Var(id)
            case Call(Name("input_int"), []):
                # input_int() -> call read_int, result in %rax
                instrs = [Instr("callq", [Label("read_int")])]
                return instrs, Reg("rax")
            case UnaryOp(USub(), operand):
                # unary minus: -operand
                instrs, op_loc = self.select_arg(operand)
                tmp_var = generate_name("tmp")
                instrs.append(Instr("movq", [op_loc, Var(tmp_var)]))
                instrs.append(Instr("negq", [Var(tmp_var)]))
                return instrs, Var(tmp_var)

            case BinOp(left, Add(), right):
                # Addition: left + right
                instrs = []
                left_instrs, left_loc = self.select_arg(left)
                instrs.extend(left_instrs)
                right_instrs, right_loc = self.select_arg(right)
                instrs.extend(right_instrs)

                tmp_var = generate_name("tmp")
                instrs.append(Instr("movq", [left_loc, Var(tmp_var)]))
                instrs.append(Instr("addq", [right_loc, Var(tmp_var)]))
                return instrs, Var(tmp_var)

            case BinOp(left, Sub(), right):
                # Addition: left - right
                instrs = []
                left_instrs, left_loc = self.select_arg(left)
                instrs.extend(left_instrs)
                right_instrs, right_loc = self.select_arg(right)
                instrs.extend(right_instrs)

                tmp_var = generate_name("tmp")
                instrs.append(Instr("movq", [left_loc, Var(tmp_var)]))
                instrs.append(Instr("subq", [right_loc, Var(tmp_var)]))
                return instrs, Var(tmp_var)

            case _:
                raise Exception(f"select_expr: unexpected expression {e}")

    def select_stmt(self, s: stmt) -> list[Instr]:
        match s:
            case Assign([Name(id)], value):
                # handle assignment: id = value
                instrs, value_loc = self.select_arg(value)
                instrs.append(Instr("movq", [value_loc, Var(id)]))
                return instrs

            case Expr(Call(Name("print"), [arg])):
                # handle print(arg)
                instrs, arg_loc = self.select_arg(arg)
                # Move argument to %rdi (first function argument register in x86-64)
                instrs.append(Instr("movq", [arg_loc, Reg("rdi")]))
                instrs.append(Instr("callq", [Label(label_name("print_int"))]))
                return instrs

            case Expr(value):
                # Expression statement (result discarded)
                instrs, _ = self.select_expr(value)
                return instrs

    def select_instructions(self, p: Module) -> X86Program:
        match p:
            case Module(body):
                instrs = []
                for stmt in body:
                    instrs.extend(self.select_stmt(stmt))
                return X86Program(instrs)
    ############################################################################
    # Liveness Analysis
    ############################################################################

    def locations(self, e: Arg) -> set[str]:
        match e:
            case Reg(r):
                return {r}
            case Var(v):
                return {v}
            case Deref(r, _):
                return {r}
            case _:
                return set()

    def read_vars(self, i: Instr) -> set[str]:
        match i:
            case Instr("movq", [s, d]):
                reads = self.locations(s)
                if isinstance(d, Deref):
                    reads = reads | {d.reg}
                return reads
            case Instr("addq", [s, d]) | Instr("subq", [s, d]):
                return self.locations(s) | self.locations(d)
            case Instr("negq", [d]):
                return self.locations(d)
            case Instr("callq", _):
                return set()
            case Instr("pushq", [s]):
                return self.locations(s)
            case Instr("popq", [d]):
                if isinstance(d, Deref):
                    return {d.reg}
                return set()
            case Instr("retq", _):
                return {"rax", "rsp"}
            case _:
                return set()

    def write_vars(self, i: Instr) -> set[str]:
        caller_saved = {"rax", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r10", "r11"}
        match i:
            case Instr("movq", [_, d]) | Instr("addq", [_, d]) | Instr("subq", [_, d]) | Instr("negq", [d]) | Instr("popq", [d]):
                if isinstance(d, (Reg, Var)):
                    return self.locations(d)
                return set()
            case Instr("callq", _):
                return caller_saved
            case _:
                return set()

    def uncover_live(self, p: X86Program) -> dict[Instr, set[str]]:
        live_after = {}
        live = set()
        for i in reversed(p.instrs):
            live_after[i] = live
            read = self.read_vars(i)
            write = self.write_vars(i)
            live = (live - write) | read
        return live_after


    ############################################################################
    # Build Interference Graph
    ############################################################################

    def build_interference(self, p: X86Program, live_after: dict[Instr, set[str]]) -> dict[str, set[str]]:
        graph: dict[str, set[str]] = {}

        def add_vertex(v: str):
            graph.setdefault(v, set())

        def add_edge(u: str, v: str):
            if u == v:
                return
            add_vertex(u)
            add_vertex(v)
            graph[u].add(v)
            graph[v].add(u)

        for i in p.instrs:
            live = set(live_after.get(i, set()))
            writes = self.write_vars(i)

            # Ensure all seen variables/registers exist in graph even if isolated.
            for v in live | writes | self.read_vars(i):
                add_vertex(v)

            match i:
                case Instr("movq", [src, _]):
                    live = live - self.locations(src)

            for w in writes:
                for v in live:
                    add_edge(w, v)

        return graph


    ############################################################################
    # Assign Homes
    ############################################################################

    def collect_vars(self, instrs: list[Instr]) -> set[str]:
        return {arg.name for instr in instrs for arg in instr.args if isinstance(arg, Var)}

    def assign_homes_arg(self, a: Arg, home: dict[str, Arg]) -> Arg:
        if isinstance(a, Var):
            return home.get(a.name, a)
        return a

    def assign_homes_instr(self, i: Instr, home: dict[str, Arg]) -> Instr:
        new_args = [self.assign_homes_arg(arg, home) for arg in i.args]
        return Instr(i.op, new_args)

    def stack_space_required(self, home: dict[str, Arg]) -> int:
        """Compute bytes of stack space needed for homes that live on the stack."""
        offsets = [loc.offset for loc in home.values() if isinstance(loc, Deref)]
        if not offsets:
            return 0
        return -min(offsets)

    def assign_homes(self, p: X86Program, home: dict[str, Arg] | None = None) -> X86Program:
        if home is None:
            variables = self.collect_vars(p.instrs)
            stack_offset = -8
            home = {}

            for var_name in sorted(variables):
                home[var_name] = Deref("rbp", stack_offset)
                stack_offset -= 8

        new_instrs = [self.assign_homes_instr(i, home) for i in p.instrs]
        return X86Program(new_instrs, used_callee=p.used_callee)

    ############################################################################
    # Patch Instructions
    ############################################################################

    def patch_instr(self, i: Instr) -> list[Instr]:
        match i:
            case Instr("movq", [src, dst]) if src == dst:
                # Trivial move; drop it.
                return []
            case Instr("movq", [Deref(reg1, off1), Deref(reg2, off2)]):
                # movq mem1, mem2
                # ->
                # movq mem1, %rax
                # movq %rax, mem2
                return [
                    Instr("movq", [Deref(reg1, off1), Reg("rax")]),
                    Instr("movq", [Reg("rax"), Deref(reg2, off2)]),
                ]

            case Instr("addq", [Deref(reg1, off1), Deref(reg2, off2)]):
                # addq mem1, mem2
                # ->
                # movq mem2, %rax
                # addq mem1, %rax
                # movq %rax, mem2
                return [
                    Instr("movq", [Deref(reg2, off2), Reg("rax")]),
                    Instr("addq", [Deref(reg1, off1), Reg("rax")]),
                    Instr("movq", [Reg("rax"), Deref(reg2, off2)]),
                ]

            case Instr("subq", [Deref(reg1, off1), Deref(reg2, off2)]):
                # subq mem1, mem2
                # ->
                # movq mem2, %rax
                # subq mem1, %rax
                # movq %rax, mem2
                return [
                    Instr("movq", [Deref(reg2, off2), Reg("rax")]),
                    Instr("subq", [Deref(reg1, off1), Reg("rax")]),
                    Instr("movq", [Reg("rax"), Deref(reg2, off2)]),
                ]
        return [i]

    def patch_instructions(self, p: X86Program) -> X86Program:
        instrs = []
        for i in p.instrs:
            instrs.extend(self.patch_instr(i))
        return X86Program(instrs)

    ############################################################################
    # Prelude & Conclusion
    ############################################################################

    def align(self, n: int, multiple: int = 16) -> int:
        return ((n + (multiple - 1)) // multiple) * multiple

    def count_spilled_slots(self, p: X86Program) -> int:
        """Count stack slots used for spilled variables based on rbp-relative derefs."""
        offsets = set()
        for instr in p.instrs:
            for arg in instr.args:
                if isinstance(arg, Deref) and arg.reg == "rbp" and arg.offset < 0:
                    offsets.add(arg.offset)
        return len(offsets)

    def prelude_and_conclusion(self, p: X86Program) -> X86Program:
        label = label_name("main")
        used_callee = getattr(p, "used_callee", set())

        spilled_slots = self.count_spilled_slots(p)
        callee_count = len(used_callee)
        frame_bytes = self.align(8 * spilled_slots + 8 * callee_count) - 8 * callee_count

        prelude = [Instr(".globl", [Label(label)]), Instr(f"{label}:", []), Instr("pushq", [Reg("rbp")]), Instr("movq", [Reg("rsp"), Reg("rbp")])]
        for reg in sorted(used_callee):
            prelude.append(Instr("pushq", [Reg(reg)]))
        if frame_bytes > 0:
            prelude.append(Instr("subq", [Immediate(frame_bytes), Reg("rsp")]))

        epilogue = []
        if frame_bytes > 0:
            epilogue.append(Instr("addq", [Immediate(frame_bytes), Reg("rsp")]))
        for reg in reversed(sorted(used_callee)):
            epilogue.append(Instr("popq", [Reg(reg)]))
        epilogue.extend([Instr("popq", [Reg("rbp")]), Instr("retq", [])])

        return X86Program(prelude + p.instrs + epilogue, used_callee=used_callee)
