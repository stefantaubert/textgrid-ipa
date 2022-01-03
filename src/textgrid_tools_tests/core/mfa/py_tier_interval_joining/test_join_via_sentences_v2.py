from text_utils.language import Language
from text_utils.symbol_format import SymbolFormat
from textgrid.textgrid import Interval, IntervalTier
from textgrid_tools.core.mfa.interval_format import IntervalFormat
from textgrid_tools.core.mfa.string_format import StringFormat
from textgrid_tools.core.mfa.tier_interval_joining import (
    join_via_sentences, join_via_sentences_v2)


def test_a():
  tier = IntervalTier(name="test", minTime=0, maxTime=6)
  tier.add(0, 1, "\"This")
  tier.add(1, 2, "test.\"")
  tier.add(2, 2.5, " ")
  tier.add(2.5, 3, None)
  tier.add(3, 4, "Is")
  tier.add(4, 5, "right. ")
  tier.add(5, 6, None)

  res = list(join_via_sentences_v2(tier, StringFormat.TEXT,
             IntervalFormat.WORD, {" ", "\""}, {".", "?", "!"}))

  assert len(res) == 5
  assert res[0] == Interval(0, 2, "\"This test.\"")
  assert res[1] == Interval(2, 2.5, " ")
  assert res[2] == Interval(2.5, 3, "")
  assert res[3] == Interval(3, 5, "Is right. ")
  assert res[4] == Interval(5, 6, "")
