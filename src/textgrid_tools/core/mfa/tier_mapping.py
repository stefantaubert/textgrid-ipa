from typing import Iterable, List, Optional, cast

from text_utils.string_format import StringFormat
from text_utils.text import symbols_to_words
from text_utils.types import Symbols
from text_utils.utils import symbols_to_lower
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.comparison import check_tiers_are_equal
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.mfa.helper import (get_first_tier,
                                            interval_is_None_or_whitespace,
                                            merge_symbols, replace_tier,
                                            tier_exists)
from textgrid_tools.core.mfa.interval_format import IntervalFormat
from textgrid_tools.core.validation import (ExistingTierError,
                                            InvalidGridError,
                                            NotExistingTierError,
                                            ValidationError)


class NonDistinctTiersError(ValidationError):
  def __init__(self, tier_name: str) -> None:
    super().__init__()
    self.tier_name = tier_name

  @classmethod
  def validate(cls, tier_name1: str, tier_name2: str):
    if tier_name1 == tier_name2:
      return cls(tier_name1)
    return None

  @property
  def default_message(self) -> str:
    return f"Tiers \"{self.tier_name}\" are not distinct!"


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


def map_tier_to_other_tier(grid: TextGrid, tier_name: str, tier_string_format: StringFormat, tiers_interval_format: IntervalFormat, target_tier_name: str, target_tier_string_format: StringFormat, custom_target_tier: Optional[str], overwrite_tier: bool) -> ExecutionResult:
  if error := InvalidGridError.validate(grid):
    return error, False

  if error := NonDistinctTiersError.validate(tier_name, target_tier_name):
    return error, False

  if error := NotExistingTierError.validate(grid, target_tier_name):
    return error, False

  if error := NotExistingTierError.validate(grid, tier_name):
    return error, False

  output_tier = target_tier_name
  if custom_target_tier is not None:
    output_tier = custom_target_tier

  if not overwrite_tier and (error := ExistingTierError.validate(grid, output_tier)):
    return error, False

  tier = get_first_tier(grid, tier_name)
  tier_symbols = merge_symbols(tier.intervals,
                               tier_string_format, tiers_interval_format)
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

  target_tier_symbols = merge_symbols(target_tier.intervals, target_tier_string_format,
                                      tiers_interval_format)
  target_tier_words = symbols_to_words(target_tier_symbols)

  if error := UnequalIntervalAmountError.validate(tier_words, target_tier_words):
    return error, False

  res_tier = IntervalTier(
    minTime=target_tier.minTime,
    maxTime=target_tier.maxTime,
    name=output_tier,
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

  changed_anything = False
  if overwrite_tier and target_tier.name == res_tier.name:
    if not check_tiers_are_equal(target_tier, res_tier):
      replace_tier(target_tier, res_tier)
      changed_anything = True
  elif overwrite_tier and tier_exists(grid, res_tier.name):
    existing_tier = get_first_tier(grid, res_tier.name)
    if not check_tiers_are_equal(existing_tier, res_tier):
      replace_tier(existing_tier, res_tier)
      changed_anything = True
  else:
    grid.append(res_tier)
    changed_anything = True

  return None, changed_anything
