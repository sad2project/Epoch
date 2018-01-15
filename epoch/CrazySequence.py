# coding=utf-8
import functools


class Sequence:
    functions = {}
    
    def __init__(self, iterable):
        self.iterable = iterable

    def filter(self, func):
        return Sequence(filter(func, self.iterable))

    def map(self, func):
        return Sequence(map(func, self.iterable))

    def reduce(self, func, identity=None):
        if identity is None:
            return functools.reduce(func, self.iterable)
        else:
            return functools.reduce(func, self.iterable, identity)
        
    def __getattr__(self, item):
        return lambda: Sequence.functions[item](self.iterable)
    

def mapper(name=None):
    def deco(func):
        nonlocal name
        if name is None:
            name = func.__name__

        @functools.wraps(func)
        def wrapper(iterable):
            return Sequence(map(func, iterable))

        Sequence.functions[name] = wrapper
        return wrapper

    return deco


def filterer(name=None):
    def deco(func):
        nonlocal name
        if name is None:
            name = func.__name__

        @functools.wraps(func)
        def wrapper(iterable):
            return Sequence(filter(func, iterable))

        Sequence.functions[name] = wrapper
        return wrapper

    return deco


def reducer(name=None, *, identity=None):

    def deco(func):
        nonlocal name
        if name is None:
            name = func.__name__

        @functools.wraps(func)
        def wrapper(iterable):
            return functools.reduce(func, iterable, identity)

        Sequence.functions[name] = wrapper
        return wrapper

    return deco


def terminator(name=None):

    def decorator(func):
        nonlocal name
        if name is None:
            name = func.__name__

        Sequence.functions[name] = func
        return func

    return decorator


if __name__ == '__main__':

    @filterer("evens")
    def isEven(x):
        return x % 2 == 0

    @mapper()
    def squared(x):
        return x ** 2

    terminator("toList")(list)

    @reducer("sum", identity=0)
    def add(x, y):
        return x + y

    theList = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    print(Sequence(theList).evens().squared().toList())
    print(Sequence(theList).evens().squared().sum())
