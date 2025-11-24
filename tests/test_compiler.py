from ast import Add, Assign, BinOp, Call, Constant, Expr, Module, Name, UnaryOp, USub

from compiler import Compiler
from utils import label_name
from x86_ast import Deref, Immediate, Instr, Label, Reg, Var, X86Program


def test_remove_complex_operands():
    cc = Compiler()
    ast_tree = Module(
        [
            Assign([Name("x")], BinOp(Constant(42), Add(), UnaryOp(USub(), Constant(10)))),
            Expr(Call(Name("print"), [BinOp(Name("x"), Add(), Constant(10))])),
        ]
    )
    result = cc.remove_complex_operands(ast_tree)
    lines = ["tmp_0 = -10", "x = 42 + tmp_0", "tmp_1 = x + 10", "print(tmp_1)"]
    assert str(result) == "\n".join(lines)


def test_select_instructions():
    cc = Compiler()
    ast_tree = Module(
        [
            Assign([Name("tmp_0")], Constant(42)),
            Expr(Call(Name("print"), [Name("tmp_0")])),
        ]
    )
    result = cc.select_instructions(ast_tree)
    x86_ast_tree = X86Program(
        [
            Instr("movq", [Immediate(42), Var("tmp_0")]),
            Instr("movq", [Var("tmp_0"), Reg("rdi")]),
            Instr("callq", [Label(label_name("print_int"))]),
        ]
    )
    assert repr(result) == repr(x86_ast_tree)
    x86_lines = [
        "movq $42, tmp_0",
        "movq tmp_0, %rdi",
        f"callq {label_name('print_int')}",
    ]
    assert str(result) == "\t" + "\n\t".join(x86_lines) + "\n"


def test_color_graph():
    cc = Compiler()
    interference_graph = {
        "a": {"b"},
        "b": {"a", "c"},
        "c": {"b"},
    }

    variables = ["a", "b", "c", "d"]

    colors = cc.color_graph(interference_graph, variables)

    assert colors == {"a": 1, "b": 0, "c": 1, "d": 0}


def test_color_graph_with_precolored_nodes():
    cc = Compiler()
    interference_graph = {"v": {"rdi"}, "rdi": {"v"}}

    variables = ["v"]

    colors = cc.color_graph(interference_graph, variables, {"rdi": 0})

    assert colors == {"v": 1}


def test_assign_homes():
    x86_ast_tree = X86Program(
        [
            Instr("movq", [Immediate(42), Var("tmp_0")]),
            Instr("movq", [Var("tmp_0"), Reg("rdi")]),
            Instr("callq", [Label(label_name("print_int"))]),
        ]
    )

    cc = Compiler()

    result = cc.assign_homes(x86_ast_tree)
    x86_lines = [
        "movq $42, -8(%rbp)",
        "movq -8(%rbp), %rdi",
        f"callq {label_name('print_int')}",
    ]
    assert str(result) == "\t" + "\n\t".join(x86_lines) + "\n"


def test_assign_homes_with_locations():
    x86_ast_tree = X86Program(
        [
            Instr("movq", [Var("v"), Var("w")]),
        ]
    )

    cc = Compiler()
    homes = {"v": Deref("rbp", -8), "w": Reg("rcx")}
    result = cc.assign_homes(x86_ast_tree, homes)
    x86_lines = [
        "movq -8(%rbp), %rcx",
    ]
    assert str(result) == "\t" + "\n\t".join(x86_lines) + "\n"


def test_allocate_registers():
    program = X86Program(
        [
            Instr("movq", [Immediate(1), Var("a")]),
            Instr("movq", [Immediate(2), Var("b")]),
            Instr("addq", [Var("a"), Var("b")]),
            Instr("addq", [Var("b"), Var("a")]),
        ]
    )

    cc = Compiler()
    allocated = cc.allocate_registers(program)

    expected = X86Program(
        [
            Instr("movq", [Immediate(1), Reg("rcx")]),
            Instr("movq", [Immediate(2), Reg("rdx")]),
            Instr("addq", [Reg("rcx"), Reg("rdx")]),
            Instr("addq", [Reg("rdx"), Reg("rcx")]),
        ]
    )

    assert repr(allocated) == repr(expected)


def test_allocate_registers_biased_by_moves():
    program = X86Program(
        [
            Instr("movq", [Immediate(7), Var("a")]),
            Instr("movq", [Var("a"), Reg("rdi")]),
        ]
    )

    cc = Compiler()
    allocated = cc.allocate_registers(program)

    expected = X86Program(
        [
            Instr("movq", [Immediate(7), Reg("rdi")]),
            Instr("movq", [Reg("rdi"), Reg("rdi")]),
        ]
    )

    assert repr(allocated) == repr(expected)


def test_patch_instructions():
    cc = Compiler()

    x86_ast_tree = X86Program([Instr("movq", [Deref("rbp", -8), Deref("rbp", -16)])])
    result = cc.patch_instructions(x86_ast_tree)
    x86_lines = ["movq -8(%rbp), %rax", "movq %rax, -16(%rbp)"]
    assert str(result) == "\t" + "\n\t".join(x86_lines) + "\n"
    x86_ast_tree = X86Program([Instr("addq", [Deref("rbp", -8), Deref("rbp", -16)])])
    result = cc.patch_instructions(x86_ast_tree)
    x86_lines = ["movq -16(%rbp), %rax", "addq -8(%rbp), %rax", "movq %rax, -16(%rbp)"]
    assert str(result) == "\t" + "\n\t".join(x86_lines) + "\n"
    x86_ast_tree = X86Program([Instr("subq", [Deref("rbp", -8), Deref("rbp", -16)])])
    result = cc.patch_instructions(x86_ast_tree)
    x86_lines = ["movq -16(%rbp), %rax", "subq -8(%rbp), %rax", "movq %rax, -16(%rbp)"]
    assert str(result) == "\t" + "\n\t".join(x86_lines) + "\n"


def test_patch_instructions_removes_trivial_moves():
    cc = Compiler()
    x86_ast_tree = X86Program(
        [
            Instr("movq", [Deref("rbp", -8), Deref("rbp", -8)]),
            Instr("movq", [Reg("rax"), Reg("rax")]),
            Instr("movq", [Deref("rbp", -8), Deref("rbp", -16)]),
        ]
    )
    result = cc.patch_instructions(x86_ast_tree)
    x86_lines = ["movq -8(%rbp), %rax", "movq %rax, -16(%rbp)"]
    assert str(result) == "\t" + "\n\t".join(x86_lines) + "\n"


def test_prelude_and_conclusion():
    cc = Compiler()

    X86_ast_tree = X86Program([Instr("movq", [Deref("rbp", -16), Reg("rcx")])], used_callee={"rbx"})
    result = cc.prelude_and_conclusion(X86_ast_tree)
    x86_lines = [
        f".globl {label_name('main')}",
        f"{label_name('main')}:",
        "\tpushq %rbp",
        "\tmovq %rsp, %rbp",
        "\tpushq %rbx",
        "\tsubq $8, %rsp",
        "\tmovq -16(%rbp), %rcx",
        "\taddq $8, %rsp",
        "\tpopq %rbx",
        "\tpopq %rbp",
        "\tretq",
    ]
    assert str(result) == "\n".join(x86_lines) + "\n"
