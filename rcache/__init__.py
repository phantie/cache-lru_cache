from typing import Any, Optional, Union, Callable, Tuple, Dict
from types import FunctionType
from functools import lru_cache

__all__ = ('lru_cache', 'cache')
__version__ = '0.3.2'

def cache(f):
    return lru_cache()(f)

def lru_cache(
        maxsize: Union[None, int, FunctionType, classmethod, staticmethod]=None, # NonNegativeInt
        generate_key: Optional[Callable[[Tuple, Dict], Any]]=None,
        keep_stat:bool=False # If False cache.misses and cache.hits becomes unavailable - optimisation
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

        class Cache(dict if maxsize is None else 
                    BoundSizedDict if isinstance(maxsize, int) and maxsize >= 0 else 
                    None):

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

        cached = Cache({} if maxsize is None else maxsize)

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

        wrap.__name__ = func.__name__

        wrap.cache = cached

        if wrapper is not None:
            wrap = wrapper(wrap)

        return wrap
    return wrap