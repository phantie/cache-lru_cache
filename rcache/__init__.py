from typing import Any, Optional, Union, Callable, Tuple, Dict
from types import FunctionType
from functools import lru_cache

__all__ = ('cache', 'lru_cache')
__version__ = '0.3'

def cache(f): # TODO fix arguments
    return lru_cache(maxsize=None)(f)

def lru_cache(
        maxsize: Union[None, int, FunctionType, classmethod, staticmethod]=None, # NonNegativeInt
        generate_key: Optional[Callable[[Tuple, Dict], Any]]=None,
        keep_stat:bool=True # If False cache.misses and cache.hits becomes unavailable - optimisation
        ):
    from bmap import BoundSizedDict
    from types import FunctionType

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

        def custom_get(self, name, default):
            try:
                item = super(self.__class__, self).__getitem__(name)
            except KeyError:
                self.misses += 1
                return default
            else:
                self.hits += 1
                return item

        if maxsize is None:
            class Cache(dict):
                if keep_stat:
                    misses = hits = 0
                    get = custom_get

            cached = Cache()

        elif isinstance(maxsize, int) and maxsize >= 0:
            class Cache(BoundSizedDict):
                if keep_stat:
                    misses = hits = 0
                    get = custom_get

            cached = Cache(maxsize)
        else:
            raise ValueError('invalid argument', maxsize)

        if generate_key is None:
            def generate_key(*args, **kwargs):
                return (args, frozenset(kwargs.items()))

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