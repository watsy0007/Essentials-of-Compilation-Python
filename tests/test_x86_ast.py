import pytest

from x86_ast import Deref, Immediate, Reg, VALID_REGISTERS


def test_valid_registers_include_required_x86_names():
    expected = {
        "rsp",
        "rbp",
        "rax",
        "rbx",
        "rcx",
        "rdx",
        "rsi",
        "rdi",
        "r8",
        "r9",
        "r10",
        "r11",
        "r12",
        "r13",
        "r14",
        "r15",
    }
    assert VALID_REGISTERS == expected


def test_immediate_stores_integer_value():
    imm = Immediate(42)
    assert imm.value == 42


def test_reg_accepts_valid_name():
    reg = Reg("rax")
    assert reg.name == "rax"


def test_reg_rejects_invalid_name():
    with pytest.raises(ValueError, match="invalid register"):
        Reg("eax")


def test_deref_accepts_valid_register_and_offset():
    location = Deref("rbp", -16)
    assert location.reg == "rbp"
    assert location.offset == -16


def test_deref_rejects_invalid_register():
    with pytest.raises(ValueError, match="invalid register in deref"):
        Deref("esp", 8)
