from dataclasses import dataclass, field


VALID_REGISTERS = {
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


@dataclass(frozen=True)
class Immediate:
    value: int


@dataclass(frozen=True)
class Reg:
    name: str

    def __post_init__(self):
        if self.name not in VALID_REGISTERS:
            raise ValueError(f"invalid register: {self.name}")


@dataclass(frozen=True)
class Deref:
    reg: str
    offset: int

    def __post_init__(self):
        if self.reg not in VALID_REGISTERS:
            raise ValueError(f"invalid register in deref: {self.reg}")


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Instr:
    op: str
    args: list


@dataclass(frozen=True)
class Callq:
    label: str
    arity: int


@dataclass(frozen=True)
class Retq:
    pass


@dataclass(frozen=True)
class Jump:
    label: str


@dataclass
class X86Program:
    body: list
    stack_space: int = 0
    main_label: str = "_main"
    homes: dict[str, Deref] = field(default_factory=dict)
