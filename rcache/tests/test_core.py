import pytest
from rcache import cache, lru_cache

def execute_times(n):
    def wrap(f, *args, **kwargs):
        for _ in range(n):
            last = f(*args, **kwargs)
        return last
        
    return wrap

def inspect_max_cache_size(size):
    def wrap(f):
        def wrap(*args, **kwargs):
            result = f(*args, **kwargs)
            assert len(f.cache) <= size
            return result
        wrap.cache = f.cache
        return wrap
    return wrap

def execute_once(f): # WITH GIVEN PARAMETERS
    executed = set()
    def wrap(*args, **kwargs):
        key = (args, frozenset(kwargs.items()))

        assert key not in executed, \
            f"you can {f.__name__}({', '.join(str(_) for _ in args)}{', ' if args and kwargs else ''}" \
            f"{', '.join(f'{k}={v!r}' for k, v in kwargs.items())}) only once"

        calculated = f(*args, **kwargs)
        executed.add(key)
        return calculated
    return wrap

def test_base():
    class A:
        @cache
        @execute_once
        def foo(self):
            return 42

        @execute_once
        def bar(self):
            return 13

    a = A()

    assert execute_times(5)(a.foo) == 42
    
    assert a.bar() == 13
    with pytest.raises(AssertionError):
        a.bar()

def test_classmethod():
    class A:
        secret = 42

        @cache
        @classmethod
        @execute_once
        def foo(cls):
            return cls.secret

    a = A()
    a.secret = 13

    assert execute_times(5)(A.foo) == 42
    assert execute_times(5)(a.foo) == 42

def test_staticmethod():
    class A:
        @cache
        @staticmethod
        @execute_once
        def foo(x):
            return 42 * x

    a = A()

    assert execute_times(3)(a.foo, 2) == 42 * 2
    assert execute_times(3)(A.foo, 2) == 42 * 2
    assert execute_times(3)(a.foo, 3) == 42 * 3
    assert execute_times(3)(A.foo, 3) == 42 * 3

def test_generate_key():
    class A:
        def __init__(self, id):
            self.id = id

        @lru_cache(generate_key = lambda self: self.id, keep_stat=True)
        @execute_once
        def foo(self):
            return 100000 * self.id

    a = A(id=3)

    assert execute_times(10)(a.foo) == 100000 * 3
    assert A.foo.cache == {3: 100000 * 3}
    assert A.foo.cache.misses == a.foo.cache.misses == 1
    assert A.foo.cache.hits == a.foo.cache.hits == 9

def test_stat_optimisation():
    class A:
        @lru_cache(keep_stat=False)
        @execute_once
        def foo(self): pass

    a = A()

    assert execute_times(5)(a.foo) is None
    assert not hasattr(a.foo.cache, 'hits')
    assert not hasattr(a.foo.cache, 'misses')

def test_lru_cache():
    @inspect_max_cache_size(2)
    @lru_cache(maxsize=2, keep_stat=True)
    @execute_once
    def foo(a, b):
        return a + b

    cache = foo.cache
    assert foo(1, 2) == 3
    assert cache.misses == 1 and cache.hits == 0
    assert foo(1, 2) == 3
    assert cache.misses == 1 and cache.hits == 1
    assert foo(2, 2) == 4
    assert foo(2, 2) == 4
    assert foo(5, 5) == 10
    with pytest.raises(AssertionError):
        foo(1, 2) # because it ran once, removed from cache, and tries to recalculate
    assert cache == {
        ((2, 2), frozenset()): 4,
        ((5, 5), frozenset()): 10,
    }

def test_wrapped():
    @lru_cache(keep_stat=True)
    def foo(a: int, b: int):
        'adds integers'
        return a + b

    assert foo.__name__ == 'foo'
    assert foo.__doc__ == 'adds integers'