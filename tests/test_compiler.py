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
        "pushq %rbp",
        "movq %rsp, %rbp",
        "subq $8, %rsp",
        "movq $42, -8(%rbp)",
        "movq -8(%rbp), %rdi",
        f"callq {label_name('print_int')}",
        "addq $8, %rsp",
        "popq %rbp",
        "retq",
    ]
    assert str(result) == "\t" + "\n\t".join(x86_lines) + "\n"


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


def test_prelude_and_conclusion():
    cc = Compiler()

    X86_ast_tree = X86Program([])
    result = cc.prelude_and_conclusion(X86_ast_tree)
    x86_lines = [
        f".globl {label_name('main')}",
        f"{label_name('main')}:",
    ]
    assert str(result) == "\n".join(x86_lines) + "\n"
