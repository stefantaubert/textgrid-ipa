from text_utils import StringFormat
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_utils.interval_format import IntervalFormat
from textgrid_utils.intervals.sentence_joining import \
    join_intervals_on_sentences


def test_component__word():
  grid = TextGrid(None, 0, 6)
  tier = IntervalTier(name="test", minTime=grid.minTime, maxTime=grid.maxTime)
  tier.add(0, 0.5, "")
  tier.add(0.5, 1, "\"This")
  tier.add(1, 2, "test.\"")
  tier.add(2, 2.5, "")
  tier.add(2.5, 3, "")
  tier.add(3, 3.5, "Is")
  tier.add(3.5, 3.6, "")
  tier.add(3.6, 5, "right.")
  tier.add(5, 6, "")
  grid.append(tier)

  error, changed_anything = join_intervals_on_sentences(
    grid, {"test"}, StringFormat.TEXT,
      IntervalFormat.WORD, {"\""}, {".", "?", "!"})

  assert error is None
  assert changed_anything
  assert len(tier) == 6
  assert tier[0] == Interval(0, 0.5, "")
  assert tier[1] == Interval(0.5, 2, "\"This test.\"")
  assert tier[2] == Interval(2, 2.5, "")
  assert tier[3] == Interval(2.5, 3, "")
  assert tier[4] == Interval(3, 5, "Is right.")
  assert tier[5] == Interval(5, 6, "")


def test_component__words():
  grid = TextGrid(None, 0, 6)
  tier = IntervalTier(name="test", minTime=grid.minTime, maxTime=grid.maxTime)
  tier.add(0, 0.5, " ")
  tier.add(0.5, 1, "\"This test")
  tier.add(1, 2, "is right.\"")
  tier.add(2, 2.5, " ")
  tier.add(2.5, 3, "")
  tier.add(3, 3.5, "Is also ")
  tier.add(3.5, 3.6, "")
  tier.add(3.6, 5, "right. ")
  tier.add(5, 6, "")
  grid.append(tier)

  error, changed_anything = join_intervals_on_sentences(
    grid, {"test"}, StringFormat.TEXT,
      IntervalFormat.WORDS, {" ", "\""}, {".", "?", "!"})

  assert error is None
  assert changed_anything
  assert len(tier) == 6
  assert tier[0] == Interval(0, 0.5, "")
  assert tier[1] == Interval(0.5, 2, "\"This test.\"")
  assert tier[2] == Interval(2, 2.5, " ")
  assert tier[3] == Interval(2.5, 3, "")
  assert tier[4] == Interval(3, 5, "Is also  right. ")
  assert tier[5] == Interval(5, 6, "")
