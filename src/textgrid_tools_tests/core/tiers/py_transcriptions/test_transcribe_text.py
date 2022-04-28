from ordered_set import OrderedSet
from text_utils import StringFormat
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.tiers.transcription import transcribe_text


def test_component__success():
  grid = TextGrid(None, 0, 1)
  tier = IntervalTier("test", 0, 1)
  grid.tiers.append(tier)
  interval = Interval(0, 1, "this IS /a/ test.")
  tier.intervals.append(interval)
  pronunciation_dict = {
    "THIS": OrderedSet((tuple("this"),)),
    "IS": OrderedSet((tuple("is"),)),
    "/A/": OrderedSet((tuple("a"),)),
    "TEST.": OrderedSet((tuple("test."),)),
  }

  error, changed_anything = transcribe_text(grid, {"test"}, StringFormat.TEXT, pronunciation_dict)

  assert error is None
  assert changed_anything
  assert len(grid) == 1
  assert grid[0] == tier
  assert interval.mark == "t h i s  i s  a  t e s t ."


def test_component__missing_pronunciations__returns_error():
  grid = TextGrid(None, 0, 1)
  tier = IntervalTier("test", 0, 1)
  grid.tiers.append(tier)
  interval = Interval(0, 1, "this is a test.")
  tier.intervals.append(interval)
  pronunciation_dict = {}

  error, changed_anything = transcribe_text(grid, {"test"}, StringFormat.TEXT, pronunciation_dict)

  assert error is not None
  assert not changed_anything
  assert len(grid) == 1
  assert grid[0] == tier
  assert interval.mark == "this is a test."
