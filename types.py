class Timestamp:
    def __init__(self, TLP, time):
        self.time = time
        self.TLP = TLP

    def to(self, endTime):
        return Duration(self.TLP, endTime - self.time)


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
        self.new_acc_adjustment = acc_adjustment + adjustment

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
