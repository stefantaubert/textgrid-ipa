from logging import getLogger
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
from textgrid_tools.core.validation import (
    Success, validation_grid_is_valid_fails,
    validation_tier_exists_but_no_overwrite_fails,
    validation_tier_exists_fails)
from textgrid_tools.utils import update_or_add_tier


def validate_tier_names_are_different_fails(tier_name1: str, tier_name2: str) -> bool:
  if tier_name1 == tier_name2:
    logger = getLogger(__name__)
    logger.error("Tiers are not distinct!")
    return True
  return False


def validate_content_words_count_are_equal_fails(tier_words: List[Symbols], target_tier_words: List[Symbols]) -> bool:
  if len(tier_words) != len(target_tier_words):
    logger = getLogger(__name__)
    logger.error(
      f"Amount of non-pause intervals is different: {len(tier_words)} vs. {len(target_tier_words)} (target)!")
    min_len = min(len(target_tier_words), len(tier_words))
    for i in range(min_len):
      is_not_same = symbols_to_lower(target_tier_words[i]) != symbols_to_lower(tier_words[i])

      logger.info(
        f"{'===>' if is_not_same else ''} {''.join(tier_words[i])} vs. {''.join(target_tier_words[i])}")
    logger.info("...")
    return True
  return False


def map_tier_to_other_tier(grid: TextGrid, tier_name: str, tier_string_format: StringFormat, tiers_interval_format: IntervalFormat, target_tier_name: str, target_tier_string_format: StringFormat, custom_target_tier: Optional[str], overwrite_tier: bool) -> ExecutionResult:
  if validation_grid_is_valid_fails(grid):
    return False, False

  if validation_tier_exists_fails(grid, target_tier_name):
    return False, False

  if validation_tier_exists_fails(grid, tier_name):
    return False, False

  output_tier = target_tier_name
  if custom_target_tier is not None:
    output_tier = custom_target_tier

  if validation_tier_exists_but_no_overwrite_fails(grid, output_tier, overwrite_tier):
    return False, False

  if validate_tier_names_are_different_fails(tier_name, target_tier_name):
    return False, False

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

  if validate_content_words_count_are_equal_fails(tier_words, target_tier_words):
    return False

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

  return True, changed_anything
