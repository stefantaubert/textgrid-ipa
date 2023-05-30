from textgrid import Interval

from textgrid_tools.helper import check_intervals_are_consecutive


def test_empty__returns_true():
  assert check_intervals_are_consecutive([])


def test_one_interval__returns_true():
  inp = Interval(4, 5, "")

  assert check_intervals_are_consecutive([inp])


def test_two_intervals_1_2_2_3__returns_true():
  inp1 = Interval(1, 2, "")
  inp2 = Interval(2, 3, "")

  assert check_intervals_are_consecutive([inp1, inp2])


def test_two_intervals_1_2_3_4__returns_false():
  inp1 = Interval(1, 2, "")
  inp2 = Interval(3, 4, "")

  assert not check_intervals_are_consecutive([inp1, inp2])


def test_three_intervals_1_2_2_3_3_4__returns_true():
  inp1 = Interval(1, 2, "")
  inp2 = Interval(2, 3, "")
  inp3 = Interval(3, 4, "")

  assert check_intervals_are_consecutive([inp1, inp2, inp3])


def test_three_intervals_1_2_3_4_5_6__returns_true():
  inp1 = Interval(1, 2, "")
  inp2 = Interval(3, 4, "")
  inp3 = Interval(5, 6, "")

  assert not check_intervals_are_consecutive([inp1, inp2, inp3])
