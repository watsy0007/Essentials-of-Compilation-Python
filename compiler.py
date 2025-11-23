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

        def ensure(v: str):
            graph.setdefault(v, set())

        def connect(u: str, v: str):
            if u == v:
                return
            ensure(u)
            ensure(v)
            graph[u].add(v)
            graph[v].add(u)

        for instr in p.instrs:
            live = live_after.get(instr, set())
            reads = self.read_vars(instr)
            writes = self.write_vars(instr)

            for v in live | reads | writes:
                ensure(v)

            if isinstance(instr, Instr) and instr.op == "movq":
                src = instr.args[0]
                live -= self.locations(src)

            for w in writes:
                for v in live:
                    connect(w, v)

        return graph


    ############################################################################
    # Color Graph
    ############################################################################

    def color_graph(
        self,
        interference_graph: dict[str, set[str]],
        variables: list[str],
        precolored: dict[str, int] | None = None,
    ) -> dict[str, int]:
        """DSatur graph coloring with stable tie-breaks (degree, then input order)."""
        colors: dict[str, int] = dict(precolored or {})
        order = {v: idx for idx, v in enumerate(variables)}
        pending = [v for v in variables if v not in colors]

        def key(v: str) -> tuple[int, int, int]:
            neighbors = interference_graph.get(v, set())
            sat = len({colors[n] for n in neighbors if n in colors})
            return (sat, len(neighbors), -order.get(v, 0))

        while pending:
            var = max(pending, key=key)
            neighbor_colors = {colors[n] for n in interference_graph.get(var, set()) if n in colors}
            color = 0
            while color in neighbor_colors:
                color += 1
            colors[var] = color
            pending.remove(var)

        return {v: colors[v] for v in variables}


    ############################################################################
    # Allocate Registers
    ############################################################################

    def allocate_registers(self, p: X86Program) -> X86Program:
        """Replace some Var operands with physical registers using graph coloring."""
        available_registers = ["rcx", "rdx", "rsi", "rdi", "r8", "r9", "r10", "r11"]
        precolored = {reg: idx for idx, reg in enumerate(available_registers)}

        live_after = self.uncover_live(p)
        interference_graph = self.build_interference(p, live_after)
        variables = sorted(self.collect_vars(p.instrs))
        color_assignment = self.color_graph(interference_graph, variables, precolored)

        register_map: dict[str, Reg] = {
            var: Reg(available_registers[color])
            for var, color in color_assignment.items()
            if color < len(available_registers)
        }

        new_instrs = []
        for instr in p.instrs:
            new_args = []
            for arg in instr.args:
                if isinstance(arg, Var) and arg.name in register_map:
                    new_args.append(register_map[arg.name])
                else:
                    new_args.append(arg)
            new_instrs.append(Instr(instr.op, new_args))

        return X86Program(new_instrs)


    ############################################################################
    # Assign Homes
    ############################################################################

    def collect_vars(self, instrs: list[Instr]) -> set[str]:
        return set((arg.name for instr in instrs for arg in instr.args if isinstance(arg, Var)))

    def assign_homes_arg(self, a: Arg, home: dict[Var, Arg]) -> dict:
        if isinstance(a, Var):
            return home[a.name]
        return a

    def assign_homes_instr(self, i: Instr, home: dict[Var, Arg]) -> Instr:
        new_args = [self.assign_homes_arg(arg, home) for arg in i.args]
        return Instr(i.op, new_args)

    def assign_homes(self, p: X86Program) -> X86Program:
        variables = self.collect_vars(p.instrs)
        home = {}
        stack_offset = -8

        for var_name in sorted(variables):
            home[var_name] = Deref("rbp", stack_offset)
            stack_offset -= 8

        var_size = len(variables)
        stack_space = var_size * 8

        if stack_offset % 16 != 0:
            stack_offset += 8

        new_instrs = [self.assign_homes_instr(i, home) for i in p.instrs]

        prologue = [Instr("pushq", [Reg("rbp")]), Instr("movq", [Reg("rsp"), Reg("rbp")])]
        if stack_space > 0:
            prologue.append(Instr("subq", [Immediate(stack_space), Reg("rsp")]))

        epilogue = []

        if stack_space > 0:
            epilogue.append(Instr("addq", [Immediate(stack_space), Reg("rsp")]))

        epilogue.extend([Instr("popq", [Reg("rbp")]), Instr("retq", [])])

        return X86Program(prologue + new_instrs + epilogue)

    ############################################################################
    # Patch Instructions
    ############################################################################

    def patch_instr(self, i: Instr) -> list[Instr]:
        match i:
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

    def prelude_and_conclusion(self, p: X86Program) -> X86Program:
        label = label_name("main")
        prelude = [Instr(".globl", [Label(label)]), Instr(f"{label}:", [])]
        return X86Program(prelude + p.instrs)
