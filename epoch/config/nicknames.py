from Epoch.option import DictOption


class Nickname:
    def __init__(self, name, tlp, **kwargs):
        self.name = name
        self.tlp = tlp
        optional = DictOption(kwargs)
        self.customer = optional["customer"]
        self.description = optional["description"]
        self.product = optional["product"]
        self.code = optional["code"]
        self.slg = optional["slg"]
        self.dlg = optional["dlg"]
        self.prj = optional["prj"]


day = "day"
break_ = "break"
lunch = "lunch"

builtin_nicknames = {day: Nickname(day, 0), break_: Nickname(break_, -1), lunch: Nickname(lunch, -2)}
