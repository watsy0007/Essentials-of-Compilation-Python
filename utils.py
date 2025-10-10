from ast import Add, Assign, BinOp, Call, Constant, Expr, Module, Name, Sub, UnaryOp, USub
from sys import platform


def node_repr(node, func):
    node.__repr__ = func


def node_str(node, func):
    node.__str__ = func


node_repr(Constant, lambda self: f"Constant({self.value})")
node_repr(Sub, lambda self: "Sub()")
node_repr(Add, lambda self: "Add()")
node_repr(USub, lambda self: "USub()")
node_repr(UnaryOp, lambda self: f"UnaryOp({repr(self.op)}, {repr(self.operand)})")
node_repr(BinOp, lambda self: f"BinOp({repr(self.left)}, {repr(self.op)}, {repr(self.right)})")
node_repr(Assign, lambda self: f"Assign({repr(self.targets)}, {repr(self.value)})")
node_repr(Name, lambda self: f"Name({repr(self.id)})")
node_repr(Call, lambda self: f"Call({repr(self.func)}, {repr(self.args)})")
node_repr(Expr, lambda self: f"Expr({repr(self.value)})")
node_repr(Module, lambda self: f"Module({repr(self.body)})")

node_str(Constant, lambda self: str(self.value))
node_str(Sub, lambda self: "-")
node_str(Add, lambda self: "+")
node_str(USub, lambda self: "-")
node_str(UnaryOp, lambda self: f"{str(self.op)}{str(self.operand)}")
node_str(BinOp, lambda self: f"{str(self.left)} {str(self.op)} {str(self.right)}")
node_str(Assign, lambda self: f"{', '.join([str(t) for t in self.targets])} = {str(self.value)}")
node_str(Name, lambda self: self.id)
node_str(Call, lambda self: f"{str(self.func)}({', '.join([str(a) for a in self.args])})")
node_str(Expr, lambda self: f"{str(self.value)}")
node_str(Module, lambda self: "\n".join([str(s) for s in self.body]))

# signed 64-bit arithmetic

min_int64 = -(1 << 63)

max_int64 = (1 << 63) - 1

mask_64 = (1 << 64) - 1

offset_64 = 1 << 63


def to_unsigned(x):
    return x & mask_64


def to_signed(x):
    return ((x + offset_64) & mask_64) - offset_64


def add64(x, y):
    return to_signed(x + y)


def sub64(x, y):
    return to_signed(x - y)


def mul64(x, y):
    return to_signed(x * y)


def neg64(x):
    return to_signed(-x)


def input_int() -> int:
    # entering illegal characters may cause exception,
    # but we won't worry about that
    x = int(input())
    # clamp to 64 bit signed number, emulating behavior of C's scanf
    x = min(max_int64, max(min_int64, x))
    return x


name_ids = {}


def generate_name(name):
    global name_ids
    ls = name.split("_")
    name = ls[0]
    new_id = name_ids.setdefault(name, 0)
    name_ids[name] = new_id + 1
    return name + "_" + str(new_id)


def label_name(name):
    if platform == "darwin":
        return "_" + name
    return name
