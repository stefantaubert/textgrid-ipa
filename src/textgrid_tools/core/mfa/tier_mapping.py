from typing import Iterable, List, Optional, cast

from text_utils.string_format import StringFormat
from text_utils.text import symbols_to_words
from text_utils.types import Symbols
from text_utils.utils import symbols_to_lower
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.intervals.joining.common import merge_intervals
from textgrid_tools.core.mfa.helper import (add_or_update_tier, get_first_tier,
                                            interval_is_None_or_whitespace)
from textgrid_tools.core.mfa.interval_format import IntervalFormat
from textgrid_tools.core.validation import (ExistingTierError,
                                            InvalidGridError, NonDistinctTiersError,
                                            NotExistingTierError,
                                            ValidationError)

class UnequalIntervalAmountError(ValidationError):
  def __init__(self, tier_words: List[Symbols], target_tier_words: List[Symbols]) -> None:
    super().__init__()
    self.tier_words = tier_words
    self.target_tier_words = target_tier_words

  @classmethod
  def validate(cls, tier_words: List[Symbols], target_tier_words: List[Symbols]):
    if len(tier_words) != len(target_tier_words):
      return cls(tier_words, target_tier_words)
    return None

  @property
  def default_message(self) -> str:
    msg = f"Amount of non-pause intervals is different: {len(self.tier_words)} vs. {len(self.target_tier_words)} (target)!\n\n"
    min_len = min(len(self.target_tier_words), len(self.tier_words))
    for i in range(min_len):
      is_not_same = symbols_to_lower(
        self.target_tier_words[i]) != symbols_to_lower(self.tier_words[i])

      msg += f"{'===>' if is_not_same else ''} {''.join(self.tier_words[i])} vs. {''.join(self.target_tier_words[i])}\n"
    msg += "..."
    return msg


def map_tier_to_other_tier(grid: TextGrid, tier_name: str, tier_string_format: StringFormat, tiers_interval_format: IntervalFormat, target_tier_name: str, target_tier_string_format: StringFormat, custom_target_tier_name: Optional[str], overwrite_tier: bool) -> ExecutionResult:
  if error := InvalidGridError.validate(grid):
    return error, False

  if error := NonDistinctTiersError.validate(tier_name, target_tier_name):
    return error, False

  if error := NotExistingTierError.validate(grid, target_tier_name):
    return error, False

  if error := NotExistingTierError.validate(grid, tier_name):
    return error, False

  output_tier_name = target_tier_name
  if custom_target_tier_name is not None:
    if not overwrite_tier and (error := ExistingTierError.validate(grid, custom_target_tier_name)):
      return error, False
    output_tier_name = custom_target_tier_name

  tier = get_first_tier(grid, tier_name)
  tier_symbols = merge_intervals(tier.intervals, tier_string_format, tiers_interval_format)
  target_tier = get_first_tier(grid, target_tier_name)

  tier_words = symbols_to_words(tier_symbols)
  for word in tier_words:
    # due to whitespace collapsing there should not be any empty words
    assert len(word) > 0

  # if original was text then: remove words with silence annotations, that have no corresponding interval
  # old_count = len(words)
  # words = [word for word in words if alignment_dict[''.join(word).upper()][0] != (SIL,)]
  # ignored_count = old_count - len(words)
  # if ignored_count > 0:
  #   logger.info(f"Ignored {ignored_count} \"{SIL}\" annotations.")

  target_tier_symbols = merge_intervals(
    target_tier.intervals, target_tier_string_format, tiers_interval_format)
  target_tier_words = symbols_to_words(target_tier_symbols)

  if error := UnequalIntervalAmountError.validate(tier_words, target_tier_words):
    return error, False

  res_tier = IntervalTier(
    minTime=target_tier.minTime,
    maxTime=target_tier.maxTime,
    name=output_tier_name,
  )

  for target_interval in cast(Iterable[Interval], target_tier.intervals):
    new_word = target_interval.mark
    if not interval_is_None_or_whitespace(target_interval):
      new_word_symbols = tier_words.pop(0)
      new_word = target_tier_string_format.convert_symbols_to_string(new_word_symbols)

    new_interval = Interval(
      minTime=target_interval.minTime,
      maxTime=target_interval.maxTime,
      mark=new_word,
    )
    res_tier.addInterval(new_interval)

  changed_anything = add_or_update_tier(grid, target_tier, res_tier, overwrite_tier)

  return None, changed_anything
