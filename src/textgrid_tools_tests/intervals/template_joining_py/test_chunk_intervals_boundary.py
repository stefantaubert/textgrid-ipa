from ordered_set import OrderedSet
from textgrid import Interval

from textgrid_tools.intervals.template_joining import chunk_intervals_boundary


def test_component():
  intervals = [
    Interval(0, 1, "a"),    # word 1
    Interval(1, 2, ""),     # word 1
    Interval(2, 3, "c"),    # word 1
    Interval(3, 4, "a"),    # word 2
    Interval(4, 5, ""),     # word 2
    Interval(5, 6, "x"),    # word 2
    Interval(6, 7, "y"),    # word 3
    Interval(7, 8, "b"),    # word 4
    Interval(8, 9, "a"),    # word 5
    Interval(9, 10, "a"),   # word 5 -> is not merged with next two intervals
    Interval(10, 11, ""),   # word 5
    Interval(11, 12, "c"),  # word 6
    Interval(12, 13, ""),   # word 7
  ]

  boundaries = OrderedSet((
    0, 3,
    4, 6,
    7,
    8, 11,
    12,
    13,
  ))

  result = list(chunk_intervals_boundary(intervals, ["a", "", "c"], boundaries))

  assert result == [
    [intervals[0], intervals[1], intervals[2]],
    [intervals[3]],
    [intervals[4]],
    [intervals[5]],
    [intervals[6]],
    [intervals[7]],
    [intervals[8]],
    [intervals[9]],
    [intervals[10]],
    [intervals[11]],
    [intervals[12]],
  ]


def test__X__a__X__returns__X():
  intervals = [
    Interval(0, 1, "X"),
  ]

  result = list(chunk_intervals_boundary(intervals, ["a"], OrderedSet((0, 1))))

  assert result == [
    [intervals[0]],
  ]


def test__a__a__a__returns__a():
  intervals = [
    Interval(0, 1, "a"),
  ]

  result = list(chunk_intervals_boundary(intervals, ["a"], OrderedSet((0, 1))))

  assert result == [
    [intervals[0]],
  ]


def test__a_a__a__aa__returns__a_a():
  intervals = [
    Interval(0, 1, "a"),
    Interval(1, 2, "a"),
  ]

  result = list(chunk_intervals_boundary(intervals, ["a"], OrderedSet((0, 2))))

  assert result == [
    [intervals[0]],
    [intervals[1]],
  ]


def test__a_X_a__a__a_X_a__returns__a_X_a():
  intervals = [
    Interval(0, 1, "a"),
    Interval(1, 2, "X"),
    Interval(2, 3, "a"),
  ]

  result = list(chunk_intervals_boundary(intervals, ["a"], OrderedSet((0, 1, 2, 3))))

  assert result == [
    [intervals[0]],
    [intervals[1]],
    [intervals[2]],
  ]


def test__a_b__a_b__ab__returns__ab():
  intervals = [
    Interval(0, 1, "a"),  # merge
    Interval(1, 2, "b"),  # merge
  ]

  result = list(chunk_intervals_boundary(intervals, ["a", "b"], OrderedSet((0, 2))))

  assert result == [
    [intervals[0], intervals[1]],
  ]


def test__a_a_b__a_b__aab__returns__a_ab():
  intervals = [
    Interval(0, 1, "a"),
    Interval(1, 2, "a"),  # merge
    Interval(2, 3, "b"),  # merge
  ]

  result = list(chunk_intervals_boundary(intervals, ["a", "b"], OrderedSet((0, 3))))

  assert result == [
    [intervals[0]],
    [intervals[1], intervals[2]],
  ]


def test__a_a_a_b__a_b__aaab__returns__a_a_ab():
  intervals = [
    Interval(0, 1, "a"),
    Interval(1, 2, "a"),
    Interval(2, 3, "a"),  # merge
    Interval(3, 4, "b"),  # merge
  ]

  result = list(chunk_intervals_boundary(intervals, ["a", "b"], OrderedSet((0, 4))))

  assert result == [
    [intervals[0]],
    [intervals[1]],
    [intervals[2], intervals[3]],
  ]


def test__a_b_b__a_b__abb__returns__ab_b():
  intervals = [
    Interval(0, 1, "a"),  # merge
    Interval(1, 2, "b"),  # merge
    Interval(2, 3, "b"),
  ]

  result = list(chunk_intervals_boundary(intervals, ["a", "b"], OrderedSet((0, 3))))

  assert result == [
    [intervals[0], intervals[1]],
    [intervals[2]],
  ]


def test__a_b_b_b__a_b__abbb__returns__ab_b_b():
  intervals = [
    Interval(0, 1, "a"),  # merge
    Interval(1, 2, "b"),  # merge
    Interval(2, 3, "b"),
    Interval(3, 4, "b"),
  ]

  result = list(chunk_intervals_boundary(intervals, ["a", "b"], OrderedSet((0, 4))))

  assert result == [
    [intervals[0], intervals[1]],
    [intervals[2]],
    [intervals[3]],
  ]


def test__a_a_b_b__a_b__aabb__returns__a_ab_b():
  intervals = [
    Interval(0, 1, "a"),
    Interval(1, 2, "a"),  # merge
    Interval(2, 3, "b"),  # merge
    Interval(3, 4, "b"),
  ]

  result = list(chunk_intervals_boundary(intervals, ["a", "b"], OrderedSet((0, 4))))

  assert result == [
    [intervals[0]],
    [intervals[1], intervals[2]],
    [intervals[3]],
  ]


def test__a_a_b_b__a_b__returns__a_ab_b():
  intervals = [
    Interval(0, 1, "a"),
    Interval(1, 2, "a"),  # merge
    Interval(2, 3, "b"),  # merge
    Interval(3, 4, "b"),
  ]

  result = list(chunk_intervals_boundary(intervals, ["a", "b"], OrderedSet()))

  assert result == [
    [intervals[0]],
    [intervals[1], intervals[2]],
    [intervals[3]],
  ]


def test__a_a_b_b__a_b__aa_bb__returns__a_a_b_b():
  intervals = [
    Interval(0, 1, "a"),
    Interval(1, 2, "a"),  # no merge
    Interval(2, 3, "b"),  # no merge
    Interval(3, 4, "b"),
  ]

  result = list(chunk_intervals_boundary(intervals, ["a", "b"], OrderedSet((0, 2, 4))))

  assert result == [
    [intervals[0]],
    [intervals[1]],
    [intervals[2]],
    [intervals[3]],
  ]


def test__a_b_a_b_a__a_b__ababa__returns__ab_ab_a():
  intervals = [
    Interval(0, 1, "a"),  # merge 1
    Interval(1, 2, "b"),  # merge 1
    Interval(2, 3, "a"),  # merge 2
    Interval(3, 4, "b"),  # merge 2
    Interval(4, 5, "a"),
  ]

  result = list(chunk_intervals_boundary(intervals, ["a", "b"], OrderedSet((0, 5))))

  assert result == [
    [intervals[0], intervals[1]],
    [intervals[2], intervals[3]],
    [intervals[4]],
  ]


def test__a_b_a_b_a__a_b__ab_ab_a__returns__ab_ab_a():
  intervals = [
    Interval(0, 1, "a"),  # merge 1
    Interval(1, 2, "b"),  # merge 1
    Interval(2, 3, "a"),  # merge 2
    Interval(3, 4, "b"),  # merge 2
    Interval(4, 5, "a"),
  ]

  result = list(chunk_intervals_boundary(intervals, ["a", "b"], OrderedSet((0, 2, 4, 5))))

  assert result == [
    [intervals[0], intervals[1]],
    [intervals[2], intervals[3]],
    [intervals[4]],
  ]


def test__a_b_a_b_a__a_b__ab_a_b_a__returns__ab_a_b_a():
  intervals = [
    Interval(0, 1, "a"),  # merge
    Interval(1, 2, "b"),  # merge
    Interval(2, 3, "a"),  # no merge
    Interval(3, 4, "b"),  # no merge
    Interval(4, 5, "a"),
  ]

  result = list(chunk_intervals_boundary(intervals, ["a", "b"], OrderedSet((0, 2, 3, 4, 5))))

  assert result == [
    [intervals[0], intervals[1]],
    [intervals[2]],
    [intervals[3]],
    [intervals[4]],
  ]
