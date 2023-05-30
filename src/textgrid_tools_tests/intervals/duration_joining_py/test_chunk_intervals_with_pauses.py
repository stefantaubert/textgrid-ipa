from textgrid import Interval

from textgrid_tools.intervals.duration_joining import chunk_intervals_with_pauses
from textgrid_tools_tests.helper import assert_intervals_are_equal


def test_component():
  res = list(chunk_intervals_with_pauses(
    intervals=(
      Interval(0, 1, ""),
      Interval(1, 2, "a"),
      Interval(3, 4, "b"),
      Interval(5, 6, ""),
      Interval(6, 7, ""),
      Interval(8, 9, "c"),
      Interval(9, 10, ""),
      Interval(10, 11, "d"),
      Interval(11, 12, ""),
      Interval(12, 13, "e"),
      Interval(13, 14, "f"),
      Interval(14, 15, "g"),
      Interval(15, 16, "h"),
      Interval(16, 17, ""),
    ),
    max_duration_s=4,
  ))

  assert res == [
    [Interval(0, 1, None), Interval(1, 2, "a"), Interval(3, 4, "b"), Interval(5, 6, None)],
    [Interval(6, 7, None), Interval(8, 9, "c"), Interval(9, 10, None), Interval(10, 11, "d")],
    [Interval(11, 12, None), Interval(12, 13, "e"), Interval(13, 14, "f"), Interval(14, 15, "g")],
    [Interval(15, 16, "h"), Interval(16, 17, None)]
  ]


def test_too_long_content__is_in_own_chunk():
  interval1 = Interval(0, 2, "e")
  res = list(chunk_intervals_with_pauses(
    intervals=(interval1, ),
    max_duration_s=1,
  ))

  assert len(res) == 1
  assert_intervals_are_equal(res[0], [interval1])
