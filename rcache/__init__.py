def cache(f):
    return lru_cache(maxsize=None)(f)

def lru_cache(maxsize=None): 
    # takes NonNegativeInt, None, FunctionType, classmethod or staticmethod
    from bmap import BoundSizedDict
    from types import FunctionType

    specials = {classmethod, staticmethod, FunctionType}

    if maxsize == 0:
        return lambda f: f
    elif any(isinstance(maxsize, t) for t in specials):
        return cache(maxsize)

    class none: ...

    def wrap(func):
        wrapper = type(func)
        if wrapper in specials:
            if wrapper is FunctionType:
                wrapper = None
            else:
                func = func.__func__
        else:
            raise TypeError('unsupported descriptor', wrapper)

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

        if wrapper is not None:
            wrap = wrapper(wrap)

        return wrap
    return wrap