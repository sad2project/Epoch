# coding=utf-8

from epoch.repo import *


class MockAdjustmentsRepo(AdjustmentsRepository):
    def __init__(self):
        self.storage: MutableMapping[TLP, TLPDuration] = {}

    def retrieve_all(self) -> Iterable[TLPDuration]:
        return self.storage.values()

    def retrieve(self, tlp: TLP) -> TLPDuration:
        return self.storage[tlp]

    def remove(self, tlp: Union[TLP, TLPDuration]) -> None:
        if isinstance(tlp, TLPDuration):
            tlp = tlp.tlp
        del self.storage[tlp]

    def set(self, tlp_dur: TLPDuration) -> None:
        self.storage[tlp_dur.tlp] = tlp_dur

    def set_all(self, durs: Iterable[TLPDuration]) -> None:
        for tlp_dur in durs:
            self.set(tlp_dur)


class MockTimeLineRepo(TimeLineRepository):
    def __init__(self):
        self.storage: MutableMapping[Time, TLPLine] = {}

    def add_line(self, tlp_line: TLPLine) -> None:
        self.storage[tlp_line.time] = tlp_line

    def retrieve_lines(self) -> Iterable[TLPLine]:
        return sorted(self.storage.values())

    def remove_line_by_time(self, time: Time) -> None:
        del self.storage[time]

    def update_line_tlp(self, tlp_line: TLPLine) -> None:
        self.storage[tlp_line.time] = tlp_line