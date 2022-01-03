from text_utils.language import Language
from text_utils.symbol_format import SymbolFormat
from textgrid.textgrid import IntervalTier
from textgrid_tools.core.mfa.string_format import StringFormat
from textgrid_tools.core.mfa.tier_interval_joining import join_via_sentences


def test_a():
  tier = IntervalTier(name="test", minTime=0, maxTime=10)
  tier.add(0, 1, "This")
  tier.add(1, 2, "test.")
  tier.add(2,3, "")
  tier.add(3,4, "Is")
  tier.add(4,5, "right.")
  
  res = list(join_via_sentences(tier, StringFormat.TEXT, SymbolFormat.GRAPHEMES, Language.ENG))
  