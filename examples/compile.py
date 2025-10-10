import os
import uuid
from sys import platform

from lark import Lark

from compiler import Compiler
from interp_lvar import InterpLvar
from parser import ToyTransformer, grammar


def main():
    la = Lark(grammar, parser="lalr", transformer=ToyTransformer())
    code = """
x = 42 + -10
y = x
a = 10
print(y - a)
"""
    print(code)
    result = la.parse(code)
    print("ast:\n", repr(result))
    result = InterpLvar().pe(result)
    print("after patial evaluator:\n", repr(result))
    cc = Compiler()
    passes = [
        cc.remove_complex_operands,
        cc.select_instructions,
        cc.assign_homes,
        cc.patch_instructions,
        cc.prelude_and_conclusion,
    ]
    for pass_ in passes:
        result = pass_(result)
        print(f"after {pass_.__name__} pass:")
        print(result)

    file_name = str(uuid.uuid4())[:8]
    with open(f"{file_name}.s", "w") as f:
        f.write(str(result))

    arch = "-arch x86_64" if platform == "darwin" else ""
    os.system(f"gcc {arch} -c runtime.c -o runtime.o")
    # print(os.system("nm runtime.o"))
    os.system(f"as {arch} {file_name}.s -o {file_name}.o")
    # print(os.system(f"nm {file_name}.o"))
    os.system(f"gcc {arch} runtime.o {file_name}.o -o {file_name}")
    print(f"execute {file_name}\n")
    os.system(f"./{file_name}")
    os.system(f"rm {file_name}.s {file_name}.o {file_name} runtime.o")


if __name__ == "__main__":
    main()
