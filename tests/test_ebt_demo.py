from ebt import EBT, WorldState


def my_func(world): return f"Hello {world}!"
def test_ebt_01_true(): EBT(pre=WorldState(args="world"), target=my_func, post=WorldState(returns="Hello world!")).run()
def test_ebt_01_false(): EBT(pre=WorldState(args="fail"), target=my_func, post=WorldState(returns="Hello world!"), expect=False).run()
def test_ebt_02_true(): EBT(pre=WorldState(kwargs={"world": "world"}), target=my_func, post=WorldState(returns="Hello world!")).run()
def test_ebt_02_false(): EBT(pre=WorldState(kwargs={"world": "fail"}), target=my_func, post=WorldState(returns="Hello world!"), expect=False).run()


def simple_func(): return "Hello world!"
def test_simple_true(): EBT(target=simple_func, post=WorldState(returns="Hello world!")).run()
def test_simple_false(): EBT(target=simple_func, post=WorldState(returns="fail"), expect=False).run()


def add(one, two): return one + two
def test_add_true():EBT(pre=WorldState(args=(1, 2)), target=add, post=WorldState(returns=3)).run()
def test_add_false():EBT(pre=WorldState(args=(1, 2)), target=add, post=WorldState(returns="fail"), expect=False).run()