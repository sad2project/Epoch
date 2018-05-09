from abc import ABC, abstractmethod
from typing import Iterable, Union, MutableMapping

from epoch.time import Time
from epoch.time_tracking import TLP, TLPDuration, TLPLine


class AdjustmentsRepository(ABC):
    @abstractmethod
    def retrieve_all(self) -> Iterable[TLPDuration]:
        pass

    @abstractmethod
    def retrieve(self, tlp: TLP) -> TLPDuration:
        pass

    @abstractmethod
    def remove(self, tlp: Union[TLP, TLPDuration]) -> None:
        pass

    @abstractmethod
    def set(self, tlp_dur: TLPDuration) -> None:
        pass

    @abstractmethod
    def set_all(self, durs: Iterable[TLPDuration]) -> None:
        pass


class TimeLineRepository(ABC):
    @abstractmethod
    def add_line(self, tlp_line: TLPLine) -> None:
        pass

    @abstractmethod
    def retrieve_lines(self) -> Iterable[TLPLine]:
        pass

    @abstractmethod
    def remove_line_by_time(self, time: Time) -> None:
        pass

    @abstractmethod
    def update_line_tlp(self, tlp_line: TLPLine) -> None:
        pass


class CachedAdjustmentsRepository(AdjustmentsRepository):
    def __init__(self, wrapped: AdjustmentsRepository):
        self.wrapped: AdjustmentsRepository = wrapped
        self.cache: MutableMapping[TLP, TLPDuration] = {}
        self.invalidate()

    def invalidate(self):
        del self.cache
        self.cache = {}
        for tlp_dur in self.wrapped.retrieve_all():
            self.cache[tlp_dur.tlp] = tlp_dur

    def retrieve_all(self) -> Iterable[TLPDuration]:
        return self.cache.values()

    def retrieve(self, tlp: TLP) -> TLPDuration:
        return self.cache[tlp]

    def remove(self, tlp: Union[TLP, TLPDuration]) -> None:
        if isinstance(tlp, TLPDuration):
            tlp = tlp.tlp
        del self.cache[tlp]
        self.wrapped.remove(tlp)

    def set(self, tlp_dur: TLPDuration) -> None:
        self.cache[tlp_dur.tlp] = tlp_dur
        self.wrapped.set(tlp_dur)

    def set_all(self, durs: Iterable[TLPDuration]) -> None:
        for tlp_dur in durs:
            self.cache[tlp_dur.tlp] = tlp_dur
        self.wrapped.set_all(durs)

    def __getattr__(self, item):
        return getattr(self.wrapped, item)