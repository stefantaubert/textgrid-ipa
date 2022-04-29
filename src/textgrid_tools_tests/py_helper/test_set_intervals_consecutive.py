from textgrid import Interval

from textgrid_tools.helper import set_intervals_consecutive


def test_empty__is_allowed():
  set_intervals_consecutive([], 1, 2)


def test_one_interval__times_are_changed():
  inp = Interval(4, 5, "")

  set_intervals_consecutive([inp], 1, 2)

  assert inp.minTime == 1
  assert inp.maxTime == 2


def test_two_intervals__times_are_changed():
  inp1 = Interval(4, 5, "")
  inp2 = Interval(4, 5, "")

  set_intervals_consecutive([inp1, inp2], 1, 2)

  assert inp1.minTime == 1.0
  assert inp1.maxTime == 1.5

  assert inp2.minTime == 1.5
  assert inp2.maxTime == 2.0


def test_three_intervals__times_are_changed():
  inp1 = Interval(4, 5, "")
  inp2 = Interval(4, 5, "")
  inp3 = Interval(4, 5, "")

  set_intervals_consecutive([inp1, inp2, inp3], 1, 2)

  assert inp1.minTime == 1
  assert inp1.maxTime == 1 + 1 / 3

  assert inp2.minTime == 1 + 1 / 3
  assert inp2.maxTime == 1 + 2 / 3

  assert inp3.minTime == 1 + 2 / 3
  assert inp3.maxTime == 2
