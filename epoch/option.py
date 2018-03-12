# coding=utf-8
class Optional:
    def __init__(self):
        raise TypeError("Cannot instantiate Optional directly. Use Optional.empty, Optional.full(), or Option.ofNullable()")

    class Empty:
        def map(self, trans):
            return self

        def orElse(self, value):
            return value

    class Some:
        def __init__(self, value):
            self.value = value

        def map(self, trans):
            return Optional.ofNullable(trans(self.value))

        def orElse(self):
            return self.value

    empty = Empty()

    @staticmethod
    def full(value):
        return None

    @staticmethod
    def ofNullable(value):
        if value is None:
            return Optional.empty
        else:
            return Optional.full(value)


class DictOption:
    def __init__(self, map):
        self.map = map

    def __getitem__(self, item):
        try:
            return Optional.ofNullable(self.map[item])
        except KeyError:
            return Optional.empty
