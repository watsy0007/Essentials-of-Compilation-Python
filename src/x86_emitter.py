from x86_ast import Callq, Deref, Immediate, Instr, Jump, Reg, Retq


def emit_arg(arg):
    if isinstance(arg, Immediate):
        return f"${arg.value}"
    if isinstance(arg, Reg):
        return f"%{arg.name}"
    if isinstance(arg, Deref):
        return f"{arg.offset}(%{arg.reg})"
    raise ValueError(f"unsupported x86 argument: {arg!r}")


def emit_instr(instr):
    if isinstance(instr, Instr):
        if len(instr.args) == 1:
            return f"    {instr.op} {emit_arg(instr.args[0])}"
        if len(instr.args) == 2:
            return (
                f"    {instr.op} {emit_arg(instr.args[0])}, {emit_arg(instr.args[1])}"
            )
        raise ValueError(f"unsupported instruction arity: {instr!r}")
    if isinstance(instr, Callq):
        return f"    callq {instr.label}"
    if isinstance(instr, Retq):
        return "    retq"
    if isinstance(instr, Jump):
        return f"    jmp {instr.label}"
    raise ValueError(f"unsupported instruction: {instr!r}")


def emit_program(program):
    lines = [f".globl {program.main_label}", f"{program.main_label}:"]
    lines.extend(emit_instr(instr) for instr in program.body)
    return "\n".join(lines) + "\n"
