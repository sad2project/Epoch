# coding=utf-8


def pipe(func, *args, **kwargs):
    return PipeValue(func(*args, **kwargs))


class PipeValue:
    def __init__(self, value):
        self.value = value

    def then(self, func, *args, **kwargs):
        return PipeValue(func(self.value, *args, **kwargs))

    def then_post(self, func, *args, **kwargs):
        return PipeValue(func(*args, self.value, **kwargs))

    def then_as(self, func, key, *args, **kwargs):
        kwargs[key] = self.value
        return PipeValue(func(*args, **kwargs))


def do_if(boolVal, func):
    if boolVal:
        return func
    else:
        return _passThroughFirst


def _passThroughFirst(val, *args, **kwargs):
    return val