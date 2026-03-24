import subprocess
import tempfile
from pathlib import Path

import pytest

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
from compiler_var import CompilerVar
from x86_ast import Callq, Deref, Immediate, Instr, Reg, Retq, Var, X86Program
from x86_emitter import emit_program


def test_remove_complex_operands_introduces_temporaries():
    compiler = CompilerVar()
    program = Module(
        [
            Expr(
                Call(
                    Name("print"),
                    [
                        BinOp(
                            Constant(1),
                            Add(),
                            UnaryOp(USub(), Constant(2)),
                        )
                    ],
                )
            )
        ]
    )

    lowered = compiler.remove_complex_operands(program)

    assert len(lowered.body) == 3
    assert repr(lowered.body[0]) == repr(
        Assign([Name("tmp_0")], UnaryOp(USub(), Constant(2)))
    )
    assert repr(lowered.body[1]) == repr(
        Assign([Name("tmp_1")], BinOp(Constant(1), Add(), Name("tmp_0")))
    )
    assert repr(lowered.body[2]) == repr(Expr(Call(Name("print"), [Name("tmp_1")])))


def test_select_instructions_for_assign_and_print():
    compiler = CompilerVar()
    program = Module(
        [
            Assign([Name("x")], Constant(42)),
            Expr(Call(Name("print"), [Name("x")])),
        ]
    )

    x86 = compiler.select_instructions(program)

    assert x86.body == [
        Instr("movq", [Immediate(42), Var("x")]),
        Instr("movq", [Var("x"), Reg("rdi")]),
        Callq("_print_int", 1),
    ]


def test_assign_homes_maps_vars_to_stack_slots():
    compiler = CompilerVar()
    program = compiler.select_instructions(
        Module(
            [
                Assign([Name("x")], Constant(1)),
                Assign([Name("y")], Name("x")),
            ]
        )
    )

    homed = compiler.assign_homes(program)

    assert homed.stack_space == 16
    assert homed.homes["x"] == Deref("rbp", -8)
    assert homed.homes["y"] == Deref("rbp", -16)


def test_patch_instructions_rewrites_memory_to_memory_movq():
    compiler = CompilerVar()
    program = compiler.assign_homes(
        compiler.select_instructions(Module([Assign([Name("y")], Name("x"))]))
    )

    patched = compiler.patch_instructions(program)

    assert patched.body == [
        Instr("movq", [Deref("rbp", -8), Reg("rax")]),
        Instr("movq", [Reg("rax"), Deref("rbp", -16)]),
    ]


def test_prelude_and_conclusion_wrap_program_body():
    compiler = CompilerVar()
    body = [Instr("movq", [Immediate(7), Deref("rbp", -8)])]
    wrapped = compiler.prelude_and_conclusion(
        X86Program(body, stack_space=16, main_label="_main", homes={})
    )

    assert wrapped.body[0] == Instr("pushq", [Reg("rbp")])
    assert wrapped.body[1] == Instr("movq", [Reg("rsp"), Reg("rbp")])
    assert wrapped.body[2] == Instr("subq", [Immediate(16), Reg("rsp")])
    assert wrapped.body[-3] == Instr("addq", [Immediate(16), Reg("rsp")])
    assert wrapped.body[-2] == Instr("popq", [Reg("rbp")])
    assert wrapped.body[-1] == Retq()


def test_full_compile_produces_x86_program_with_retq():
    compiler = CompilerVar()
    program = Module([Expr(Call(Name("print"), [Constant(42)]))])

    result = compiler.compile(program)

    assert isinstance(result.body[-1], Retq)


def _runtime_path():
    return Path(__file__).resolve().parent.parent / "runtime" / "runtime.c"


def _clang_available():
    return (
        subprocess.run(
            ["clang", "--version"],
            capture_output=True,
            text=True,
            check=False,
        ).returncode
        == 0
    )


def _compile_cmd(asm_path, exe_path):
    return [
        "clang",
        "-arch",
        "x86_64",
        str(asm_path),
        str(_runtime_path()),
        "-o",
        str(exe_path),
    ]


def _run_cmd(exe_path):
    return ["arch", "-x86_64", str(exe_path)]


def _can_run_x86_64_binary():
    if not _clang_available():
        return False
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        asm_path = tmp / "check.s"
        exe_path = tmp / "check"
        asm_path.write_text(
            """.globl _main
_main:
    movq $0, %rax
    retq
""",
            encoding="utf-8",
        )
        compiled = subprocess.run(
            _compile_cmd(asm_path, exe_path),
            capture_output=True,
            text=True,
            check=False,
        )
        if compiled.returncode != 0:
            return False
        ran = subprocess.run(
            _run_cmd(exe_path),
            capture_output=True,
            text=True,
            check=False,
        )
        return ran.returncode == 0


_X86_64_RUNNABLE = _can_run_x86_64_binary()


@pytest.mark.skipif(
    not _X86_64_RUNNABLE,
    reason="clang x86_64 + runtime support is required for integration tests",
)
def test_integration_compile_and_run_arithmetic():
    compiler = CompilerVar()
    program = Module(
        [
            Assign([Name("x")], BinOp(Constant(40), Add(), Constant(2))),
            Expr(Call(Name("print"), [Name("x")])),
        ]
    )

    x86 = compiler.compile(program)
    asm = emit_program(x86)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        asm_path = tmp / "program.s"
        exe_path = tmp / "program"
        asm_path.write_text(asm, encoding="utf-8")

        subprocess.run(
            _compile_cmd(asm_path, exe_path),
            check=True,
            capture_output=True,
            text=True,
        )

        result = subprocess.run(
            _run_cmd(exe_path),
            check=True,
            capture_output=True,
            text=True,
        )

    assert result.stdout == "42\n"


@pytest.mark.skipif(
    not _X86_64_RUNNABLE,
    reason="clang x86_64 + runtime support is required for integration tests",
)
def test_integration_compile_and_run_input():
    compiler = CompilerVar()
    program = Module(
        [
            Assign([Name("x")], Call(Name("input_int"), [])),
            Assign([Name("y")], UnaryOp(USub(), Name("x"))),
            Assign([Name("z")], BinOp(Name("y"), Sub(), Constant(1))),
            Expr(Call(Name("print"), [Name("z")])),
        ]
    )

    x86 = compiler.compile(program)
    asm = emit_program(x86)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        asm_path = tmp / "program.s"
        exe_path = tmp / "program"
        asm_path.write_text(asm, encoding="utf-8")

        subprocess.run(
            _compile_cmd(asm_path, exe_path),
            check=True,
            capture_output=True,
            text=True,
        )

        result = subprocess.run(
            _run_cmd(exe_path),
            input="41\n",
            check=True,
            capture_output=True,
            text=True,
        )

    assert result.stdout == "-42\n"


@pytest.mark.skipif(
    not _X86_64_RUNNABLE,
    reason="clang x86_64 + runtime support is required for integration tests",
)
def test_integration_compile_and_run_nested_expression():
    compiler = CompilerVar()
    program = Module(
        [
            Expr(
                Call(
                    Name("print"),
                    [
                        BinOp(
                            BinOp(Constant(1), Add(), Constant(2)),
                            Add(),
                            BinOp(Constant(3), Add(), Constant(4)),
                        )
                    ],
                )
            )
        ]
    )

    x86 = compiler.compile(program)
    asm = emit_program(x86)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        asm_path = tmp / "program.s"
        exe_path = tmp / "program"
        asm_path.write_text(asm, encoding="utf-8")

        subprocess.run(
            _compile_cmd(asm_path, exe_path),
            check=True,
            capture_output=True,
            text=True,
        )

        result = subprocess.run(
            _run_cmd(exe_path),
            check=True,
            capture_output=True,
            text=True,
        )

    assert result.stdout == "10\n"
