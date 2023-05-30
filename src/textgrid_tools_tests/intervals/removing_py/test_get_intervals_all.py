from textgrid.textgrid import Interval, IntervalTier

from textgrid_tools.intervals.removing import get_intervals_all


def test_component():
  tier = IntervalTier()
  tier.intervals = [
    Interval(0, 1, mark="X"),
    Interval(1, 2, mark=""),
    Interval(2, 3, mark="Y"),
    Interval(3, 4, mark="X"),
    Interval(4, 5, mark=""),
    Interval(5, 6, mark="X"),
    Interval(6, 7, mark="Y"),
    Interval(7, 8, mark="X"),
    Interval(8, 9, mark=""),
  ]

  result = list(get_intervals_all(tier, marks={"", "X"}))

  assert len(result) == 7
  assert result[0] == Interval(0, 1, mark="X")
  assert result[1] == Interval(1, 2, mark="")
  assert result[2] == Interval(3, 4, mark="X")
  assert result[3] == Interval(4, 5, mark="")
  assert result[4] == Interval(5, 6, mark="X")
  assert result[5] == Interval(7, 8, mark="X")
  assert result[6] == Interval(8, 9, mark="")
