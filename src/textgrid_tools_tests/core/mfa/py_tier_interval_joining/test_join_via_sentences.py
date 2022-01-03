from text_utils.language import Language
from text_utils.symbol_format import SymbolFormat
from textgrid.textgrid import Interval, IntervalTier
from textgrid_tools.core.mfa.interval_format import IntervalFormat
from textgrid_tools.core.mfa.string_format import StringFormat
from textgrid_tools.core.mfa.tier_interval_joining import join_via_sentences


def test_a():
  tier = IntervalTier(name="test", minTime=0, maxTime=6)
  tier.add(0, 0.5, " ")
  tier.add(0.5, 1, "\"This")
  tier.add(1, 2, "test.\"")
  tier.add(2, 2.5, " ")
  tier.add(2.5, 3, "")
  tier.add(3, 4, "Is")
  tier.add(4, 5, "right. ")
  tier.add(5, 6, "")

  res = list(join_via_sentences(tier, StringFormat.TEXT,
             IntervalFormat.WORD, {" ", "\""}, {".", "?", "!"}))

  assert len(res) == 6
  assert res[0] == Interval(0, 0.5, " ")
  assert res[1] == Interval(0.5, 2, "\"This test.\"")
  assert res[2] == Interval(2, 2.5, " ")
  assert res[3] == Interval(2.5, 3, "")
  assert res[4] == Interval(3, 5, "Is right. ")
  assert res[5] == Interval(5, 6, "")
