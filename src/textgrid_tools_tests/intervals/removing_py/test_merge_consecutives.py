from ordered_set import OrderedSet

from textgrid_tools.intervals.removing import merge_consecutives


def test_component():
  times = OrderedSet([
    (0, 2.001),  # merge
    (2.001, 4),  # merge
    (4.1, 4.5),  # single
    (4.6, 4.71),  # merge
    (4.71, 4.72),  # merge
    (4.72, 4.8),  # merge
    (5, 5.1),  # single
    (5.15, 6),  # merge
    (6, 100.123),  # merge
  ])
  result = merge_consecutives(times)
  assert result == OrderedSet([
    (0, 4),
    (4.1, 4.5),
    (4.6, 4.8),
    (5, 5.1),
    (5.15, 100.123),
  ])


def test_one_entry__is_returned():
  times = OrderedSet([
    (0, 2.001),
  ])
  result = merge_consecutives(times)
  assert result == OrderedSet([
    (0, 2.001),
  ])


def test_two_entries_no_merge__nothing_is_merged():
  times = OrderedSet([
    (0, 2.001),
    (4, 6.001),
  ])
  result = merge_consecutives(times)
  assert result == OrderedSet([
      (0, 2.001),
      (4, 6.001),
  ])


def test_no_entry__nothing_is_returned():
  times = OrderedSet()
  result = merge_consecutives(times)
  assert result == OrderedSet()
