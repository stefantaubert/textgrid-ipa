from logging import getLogger
from typing import Optional, Set

from text_utils.pronunciation.ARPAToIPAMapper import symbol_map_arpa_to_ipa
from textgrid.textgrid import TextGrid

from textgrid_utils.globals import ExecutionResult
from textgrid_utils.helper import get_all_intervals, get_mark
from textgrid_utils.validation import InvalidGridError, NotExistingTierError


def map_arpa_to_ipa(grid: TextGrid, tier_names: Set[str], replace_unknown: bool, replace_unknown_with: Optional[str], ignore: Set[str]) -> ExecutionResult:
  assert len(tier_names) > 0

  if error := InvalidGridError.validate(grid):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  intervals = list(get_all_intervals(grid, tier_names))

  logger = getLogger(__name__)

  changed_anything = False

  for interval in intervals:
    arpa_symbol = get_mark(interval)
    ipa_symbol = symbol_map_arpa_to_ipa(
      arpa_symbol=arpa_symbol,
      ignore=ignore,
      replace_unknown=replace_unknown,
      replace_unknown_with=replace_unknown_with,
    )

    if ipa_symbol is None:
      ipa_symbol = ""

    if arpa_symbol != ipa_symbol:
      logger.debug(f"Mapped \"{arpa_symbol}\" to \"{ipa_symbol}\".")
      interval.mark = ipa_symbol
      changed_anything = True

  return None, changed_anything
