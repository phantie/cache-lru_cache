from typing import Union
from types import FunctionType
from functools import wraps

__all__ = ('lru_cache', 'cache')
__version__ = '0.4'

def cache(f):
    return lru_cache()(f)

def lru_cache(
        maxsize: Union[None, "NonNegativeInt", FunctionType, classmethod, staticmethod]=None,
        generate_key = lambda *args, **kwargs: (args, frozenset(kwargs.items())),
        keep_stat: bool = False # If False cache.misses and cache.hits becomes unavailable - optimisation
        ):

    from bmap import BoundSizedDict

    specials = {classmethod, staticmethod, FunctionType}

    if maxsize == 0:
        return lambda f: f
    elif any(isinstance(maxsize, t) for t in specials):
        return cache(maxsize)

    def wrap(func):
        nonlocal generate_key
        
        none = object()

        wrapper = type(func)
        if wrapper in specials:
            if wrapper is FunctionType:
                wrapper = None
            else:
                func = func.__func__
        else:
            raise TypeError('unsupported descriptor', wrapper)

        try:
            class Cache(
                dict if maxsize is None else 
                BoundSizedDict if isinstance(maxsize, int) and maxsize >= 0 else 
                None):

                def remove(self, key):
                    try:
                        del self[key]
                    except KeyError:
                        pass

                if keep_stat:
                    misses = hits = 0
                        
                    def get(self, name, default):
                        try:
                            item = super(self.__class__, self).__getitem__(name)
                        except KeyError:
                            self.misses += 1
                            return default
                        else:
                            self.hits += 1
                            return item
        except TypeError:
            raise TypeError('Invalid argument', maxsize)

        cached = Cache({} if maxsize is None else maxsize)

        @wraps(func)
        def wrap(*args, **kwargs):
            key = generate_key(*args, **kwargs)
            value = cached.get(key, none)

            if value is none:
                calculated = func(*args, **kwargs)
                cached[key] = calculated
                return calculated
            else:
                return value

        wrap.cache = cached

        if wrapper is not None:
            wrap = wrapper(wrap)

        return wrap
    return wrap