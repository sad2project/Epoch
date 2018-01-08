from datetime import datetime


class Time:
    separator_characters = ['.', ';', ':']

    def __init__(self, hour, minute):
        self.hour = hour
        self.minute = minute

    @classmethod
    def from_user_time(cls, user_time, cutoff_config):
        if user_time.startswith('+') or user_time.startswith('-'):
            return cls(*_parse_relative_time(user_time))
        else:
            return cls(*_parse_absolute_time(user_time, cutoff_config))

    @classmethod
    def now(cls):
        return cls(*_now())


def _parse_relative_time(user_time):
    minute_adjustment = int(user_time)
    now_hour, now_minute = _now()
    adjusted_minute = now_minute + minute_adjustment
    if adjusted_minute < 0:
        return now_hour - 1, adjusted_minute + 60
    if adjusted_minute > 60:
        return now_hour + 1, adjusted_minute - 60
    else:
        return now_hour, adjusted_minute


def _now():
    now = datetime.now().time()
    return now.hour, now.minute


def _parse_absolute_time(user_time, cutoff_config):
    for separator in Time.separator_characters:
        if separator in user_time:
            return _parse_absolute_time_with_separator(
                    user_time,
                    separator,
                    cutoff_config)
    else:
        raise ValueError("""User time stamp was improperly formatted.
        enter help --time for help with the time formatting""")


def _parse_absolute_time_with_separator(user_time, separator, is_afternoon):
    hour_str, rest = user_time.split(separator)
    int_hour = int(hour_str)
    if rest.isnumeric():
        return _parse_no_ampm(int_hour, int(rest), is_afternoon)
    else:
        return _parse_with_ampm(int_hour, int(rest[:2]), rest[2:].trim())


def _parse_no_ampm(hour, minute, is_afternoon):
    if hour < 12 and is_afternoon(hour):
        return hour + 12, minute
    if 0 <= hour < 24:
        return hour, minute
    raise ValueError("Invalid hour amount. The hour must be between 0 (inclusively) and 24 (exclusively)")


def _parse_with_ampm(hour, minute, ampm):
    _verify_ampm(ampm)
    return hour + _adjustment_for_pm(ampm), minute


def _verify_ampm(ampm):
    AMPM = ampm.upper()
    if len(AMPM) > 2:
        raise TypeError()
    if not AMPM.startswith('A') and not AMPM.startswith('P'):
        raise TypeError()
    if len(AMPM) == 2 and 'M' not in AMPM:
        raise TypeError()


def _adjustment_for_pm(ampm):
    return 12 \
        if 'P' in ampm.upper()\
        else 0


undefined = object()


class TLP:
    def __init__(self,
                 tlp_code,
                 description,
                 customer=undefined,
                 product=undefined,
                 code=undefined,
                 slg=undefined,
                 dlg=undefined,
                 prj=undefined):
        self.tlp_code = tlp_code
        self.description = description
        self.customer = customer
        self.product = product
        self.code = code
        self.slg = slg
        self.dlg = dlg
        self.prj = prj

    def __eq__(self, other):
        return (self.tlp_code, self.customer, self.product, self.code,
                self.slg, self.dlg, self.prj) == \
               (other.tlp_code, other.customer, other.product, other.code,
                other.slg, other.dlg, other.prj)

    def __add__(self, other):
        if self != other:
            raise ValueError("Cannot add/combine two TLGs that have the same " +
                             "set of values (excluding description)")
        return TLP(
                self.tlp_code,
                self.description + "; " + other.description,
                self.customer,
                self.product,
                self.code,
                self.slg,
                self.dlg,
                self.prj)


class Timestamp:
    def __init__(self, TLP, time):
        self.time = time
        self.TLP = TLP

    def to(self, end_time):
        return Duration(self.TLP, end_time - self.time)


class Duration:
    def __init__(self, TLP, duration):
        self.duration = duration
        self.TLP = TLP

    def has_same_TLP_as(self, other):
        return self == other

    def __add__(self, other):
        return Duration(self.TLP + other.TLP, self.duration + other.duration)

    def __eq__(self, other):
        return self.TLP == other.TLP

    def __hash__(self):
        return hash(self.TLP)

    def and_accumulated_adjustment(self, adjustment):
        return DurationWithAdjustment(self.TLP, self.duration, adjustment)

    def with_no_accumulated_adjustment(self):
        return DurationWithAdjustment(self.TLP, self.duration, 0)


class DurationWithAdjustment:
    def __init__(self, TLP, duration, acc_adjustment):
        self.TLP = TLP
        self.duration = duration
        self.acc_adjustment = acc_adjustment
        self.adjustment = None

    @property
    def adjusted_duration(self):
        if self.adjustment is None:
            self.adjustment = _best_adjustment(
                    self.duration,
                    self.acc_adjustment)
        return self.duration + self.adjustment

    @property
    def new_acc_adjustment(self):
        if self.adjustment is None:
            self.adjustment = _best_adjustment(
                    self.duration,
                    self.acc_adjustment)
        return self.acc_adjustment + self.adjustment

    def do_best_adjustment(self):
        return self

    def force_round_up(self):
        adjustment_up, _ = _adjustments_to_nearest_15(self.duration)
        return AdjustedDuration(
                self.TLP,
                self.duration,
                adjustment_up,
                self.acc_adjustment)

    def force_round_down(self):
        _, adjustment_down = _adjustments_to_nearest_15(self.duration)
        return AdjustedDuration(
                self.TLP,
                self.duration,
                adjustment_down,
                self.acc_adjustment)

    @property
    def _comparison_key(self):
        return self.new_acc_adjustment, self.adjusted_duration

    def __gt__(self, other):
        return self._comparison_key > other._comparison_key

    def __lt__(self, other):
        return self._comparison_key < other._comparison_key


class AdjustedDuration:
    def __init__(self, TLP, old_duration, adjustment, acc_adjustment):
        self.TLP = TLP
        self.duration = old_duration
        self.adjusted_duration = old_duration + adjustment
        self.adjustment = adjustment
        self.acc_adjustment = acc_adjustment
        self.new_acc_adjustment = acc_adjustment + adjustment

    def force_round_up(self):
        return AdjustedDuration(
                self.TLP,
                self.duration,
                self.adjustment + 15,
                self.acc_adjustment)

    def force_round_down(self):
        return AdjustedDuration(
                self.TLP,
                self.duration,
                self.adjustment - 15,
                self.acc_adjustment)

    @property
    def _comparison_key(self):
        return self.new_acc_adjustment, self.adjusted_duration

    def __gt__(self, other):
        return self._comparison_key > other._comparison_key

    def __lt__(self, other):
        return self._comparison_key < other._comparison_key


def _best_adjustment(num_to_round, acc_adjustment):
    adjustment_up, adjustment_down = _adjustments_to_nearest_15(num_to_round)
    new_adj_up = acc_adjustment + adjustment_up
    new_adj_down = acc_adjustment + adjustment_down
    if abs(new_adj_up) < abs(new_adj_down):
        return adjustment_up
    else:
        return adjustment_down


def _adjustments_to_nearest_15(num_to_round):
    adjustment_up = _distance_up_to_the_nearest_15(num_to_round)
    adjustment_down = adjustment_up - 15
    return adjustment_up, adjustment_down


def _distance_up_to_the_nearest_15(num_to_round):
    nearest_over = 0
    while nearest_over < num_to_round:
        nearest_over += 15
    return nearest_over - num_to_round
