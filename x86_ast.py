from dataclasses import dataclass, field


@dataclass(frozen=True)
class Immediate:
    value: int

    def __str__(self):
        return f"${self.value}"


@dataclass(frozen=True)
class Reg:
    name: str

    def __str__(self):
        return f"%{self.name}"


@dataclass(frozen=True)
class Var:
    name: str

    def __str__(self):
        return f"{self.name}"


@dataclass(frozen=True)
class Label:
    name: str

    def __str__(self):
        return f"{self.name}"


@dataclass(frozen=True)
class Deref:
    """
    Represents a memory dereference: offset(%register)
    Example: -8(%rbp) means "the memory at rbp - 8"
    """

    reg: str
    offset: int

    def __str__(self):
        return f"{self.offset}(%{self.reg})"


Arg = Immediate | Reg | Var | Label | Deref


@dataclass(frozen=True, eq=False)
class Instr:
    op: str
    args: list[Arg]

    def __str__(self):
        if len(self.args) == 0:
            return f"{self.op}"
        return f"{self.op} {', '.join(map(str, self.args))}"


@dataclass
class X86Program:
    instrs: list[Instr]
    used_callee: set[str] = field(default_factory=set)

    def __str__(self):
        result = ""
        for i in self.instrs:
            match i:
                case Instr(".globl", _) | Instr("_main:", _) | Instr("main:", _):
                    result += f"{i}\n"
                case _:
                    result += f"\t{i}\n"
        return result
