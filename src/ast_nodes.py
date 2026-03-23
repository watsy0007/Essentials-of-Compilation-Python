class Constant:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"Constant({self.value!r})"


class USub:
    def __repr__(self):
        return "USub()"


class Add:
    def __repr__(self):
        return "Add()"


class Sub:
    def __repr__(self):
        return "Sub()"


class UnaryOp:
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand

    def __repr__(self):
        return f"UnaryOp({self.op!r}, {self.operand!r})"


class Call:
    def __init__(self, func, args):
        self.func = func
        self.args = args

    def __repr__(self):
        return f"Call({self.func!r}, {self.args!r})"


class Name:
    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return f"Name({self.id!r})"


class BinOp:
    def __init__(self, left, op, right):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return f"BinOp({self.left!r}, {self.op!r}, {self.right!r})"


class Expr:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"Expr({self.value!r})"


class Module:
    def __init__(self, body):
        self.body = body

    def __repr__(self):
        return f"Module({self.body!r})"


class Assign:
    def __init__(self, targets, value):
        self.targets = targets
        self.value = value

    def __repr__(self):
        return f"Assign({self.targets!r}, {self.value!r})"
