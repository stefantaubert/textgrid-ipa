from textgrid.textgrid import Interval, IntervalTier

from textgrid_tools.intervals.removing import find_intervals_with_mark


def test_empty_mark_from_marks__is_removed():
  tier = IntervalTier()
  interval1 = Interval(0, 1, mark="")
  interval2 = Interval(1, 2, mark=" ")
  interval3 = Interval(2, 3, mark="")
  tier.intervals.append(interval1)
  tier.intervals.append(interval2)
  tier.intervals.append(interval3)
  result = list(find_intervals_with_mark(tier, marks={""}, include_empty=False))
  assert len(result) == 2
  assert result[0] == interval1
  assert result[1] == interval3


def test_empty_mark_from_bool__is_removed():
  tier = IntervalTier()
  interval1 = Interval(0, 1, mark="")
  interval2 = Interval(1, 2, mark="test")
  interval3 = Interval(2, 3, mark=" ")
  tier.intervals.append(interval1)
  tier.intervals.append(interval2)
  tier.intervals.append(interval3)
  result = list(find_intervals_with_mark(tier, marks={}, include_empty=True))
  assert len(result) == 2
  assert result[0] == interval1
  assert result[1] == interval3
