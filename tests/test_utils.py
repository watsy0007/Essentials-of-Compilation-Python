from utils import add64, generate_name, label_name, mul64, neg64, sub64


def test_add64():
    assert add64(1, 2) == 3
    assert add64(-1, -1) == -2
    assert add64(2**63 - 1, 1) == -(2**63)


def test_sub64():
    assert sub64(2, 1) == 1
    assert sub64(-1, -2) == 1


def test_mul64():
    assert mul64(2, 3) == 6
    assert mul64(-2, 3) == -6


def test_neg64():
    assert neg64(1) == -1
    assert neg64(-1) == 1


def test_generate_name():
    assert generate_name("temp") == "temp_0"
    assert generate_name("temp") == "temp_1"
    assert generate_name("var") == "var_0"
    assert generate_name("temp") == "temp_2"
    assert generate_name("var") == "var_1"


def test_label_name():
    assert label_name("start") in ("_start", "start")
