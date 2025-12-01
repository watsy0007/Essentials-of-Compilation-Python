import ast
import sys
import os
import pytest

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from type_check_l_var import TypeCheckLvar
from type_check_l_if import TypeCheckLif

def test_l_var():
    tc = TypeCheckLvar()
    
    # Test 1 + 2
    expr = ast.BinOp(ast.Constant(1), ast.Add(), ast.Constant(2))
    assert tc.type_check_exp(expr, {}) == int
    
    # Test -1
    expr = ast.UnaryOp(ast.USub(), ast.Constant(1))
    assert tc.type_check_exp(expr, {}) == int

def test_l_if():
    tc = TypeCheckLif()
    
    # Test True
    expr = ast.Constant(True)
    assert tc.type_check_exp(expr, {}) == bool
    
    # Test 1 + 2
    expr = ast.BinOp(ast.Constant(1), ast.Add(), ast.Constant(2))
    assert tc.type_check_exp(expr, {}) == int
    
    # Test not True
    expr = ast.UnaryOp(ast.Not(), ast.Constant(True))
    assert tc.type_check_exp(expr, {}) == bool
    
    # Test 1 == 1
    expr = ast.Compare(ast.Constant(1), [ast.Eq()], [ast.Constant(1)])
    assert tc.type_check_exp(expr, {}) == bool

    # Test IfExp(True, 1, 2)
    expr = ast.IfExp(ast.Constant(True), ast.Constant(1), ast.Constant(2))
    assert tc.type_check_exp(expr, {}) == int
