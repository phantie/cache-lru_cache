def cache(f):
    return lru_cache(maxsize=None)(f)

def lru_cache(maxsize=None): # takes NonNegativeInt, None or FunctionType
    from bmap import BoundSizedDict
    from types import FunctionType

    if maxsize == 0:
        return lambda f: f
    elif isinstance(maxsize, FunctionType):
        return cache(maxsize)

    class none: ...

    def wrap(func):
        if maxsize is None:
            cached = {}
        elif isinstance(maxsize, int) and maxsize >= 0:
            cached = BoundSizedDict(maxsize)
        else:
            raise ValueError('invalid argument', maxsize)

        def wrap(*args, **kwargs):
            key = (args, frozenset(kwargs.items()))
            value = cached.get(key, none)

            if value is none:
                calculated = func(*args, **kwargs)
                cached[key] = calculated
                return calculated
            else:
                return value

        return wrap
    return wrap