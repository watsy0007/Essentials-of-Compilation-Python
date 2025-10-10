from x86_ast import Immediate, Instr, Label, Reg, X86Program


def test_x86_program():
    instrs = [
        Instr(".globl", [Label("main")]),
        Instr("main:", []),
        Instr("movq", [Immediate(10), Reg("rax")]),
    ]
    ast = X86Program(instrs)
    print(ast)
    assert str(ast) == ".globl main\nmain:\n\tmovq $10, %rax\n"
