from logging import getLogger
from typing import Set

from pronunciation_dict_parser import PronunciationDict
from sentence2pronunciation import (LookupCache, sentence2pronunciation_cached,
                                    sentences2pronunciations_from_cache_mp)
from text_utils.string_format import (StringFormat,
                                      convert_symbols_to_symbols_string)
from textgrid.textgrid import TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.helper import (get_all_intervals,
                                        get_mark_symbols_intervals)
from textgrid_tools.core.validation import (InvalidGridError,
                                            InvalidStringFormatIntervalError,
                                            NotExistingTierError)


def transcribe_text(grid: TextGrid, tier_names: Set[str], tiers_string_format: StringFormat, pronunciation_dictionary: PronunciationDict) -> ExecutionResult:
  """
  chunksize: amount of intervals at once
  """
  assert len(tier_names) > 0

  if error := InvalidGridError.validate(grid):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  intervals = list(get_all_intervals(grid, tier_names))

  if error := InvalidStringFormatIntervalError.validate_intervals(intervals, tiers_string_format):
    return error, False

  intervals_symbols = list(get_mark_symbols_intervals(intervals, tiers_string_format))
  all_symbols = set(intervals_symbols)
  all_symbols.remove(tuple())
  logger = getLogger(__name__)
  logger.debug("Transcibing...")
  intervals_symbols_arpa = sentences2pronunciations_from_cache_mp(
    cache=convert_pronunciation_dict_to_cache(pronunciation_dictionary),
    sentences=all_symbols,
    chunksize=len(all_symbols),
    consider_annotation=False,  # was decided in dictionary creation
    annotation_split_symbol=None,
    ignore_case=True,
    n_jobs=1,
  )

  changed_anything = False

  for interval, interval_symbols in zip(intervals, intervals_symbols):
    #if len(intervals_symbols) == 0: ...
    if interval_symbols == tuple():
      mark = ""
    else:
      assert interval_symbols in intervals_symbols_arpa
      arpa_transcription = intervals_symbols_arpa[interval_symbols]
      mark = convert_symbols_to_symbols_string(arpa_transcription)
    if interval.mark != mark:
      logger.debug(f"Transcribed \"{interval.mark}\" to \"{mark}\".")
      interval.mark = mark
      changed_anything = True

  return None, changed_anything


def convert_pronunciation_dict_to_cache(pronunciation_dictionary: PronunciationDict) -> LookupCache:
  cache: LookupCache = dict(
    (tuple(word), pronunciation[0])
    for word, pronunciation in pronunciation_dictionary.items()
  )
  return cache


# def transcribe_words_to_arpa_on_phoneme_level(grid: TextGrid, words_tier: str, phoneme_tier: str, new_tier: str, ignore_case: bool, pronunciation_dictionary: PronunciationDict, overwrite_tier: bool, trim_symbols: Set[Symbol]):
#   logger = getLogger(__name__)
#   word_tier = get_first_tier(grid, words_tier)
#   phoneme_tier = get_first_tier(grid, phoneme_tier)
#   original_text = tier_to_text(word_tier)
#   symbols = text_to_symbols(
#     lang=Language.ENG,
#     text=original_text,
#     text_format=SymbolFormat.GRAPHEMES,
#   )

#   cache = {
#     tuple(word): pronunciation[0]
#     for word, pronunciation in pronunciation_dictionary.items()
#   }

#   symbols_arpa = sentences2pronunciations_from_cache_mp(
#     cache=cache,
#     sentences={symbols},
#     chunksize=1,
#     consider_annotation=False,
#     annotation_split_symbol=None,
#     ignore_case=ignore_case,
#     n_jobs=1,
#   )[symbols]

#   words_arpa_with_punctuation = symbols_to_words(symbols_arpa)
#   # print(words_arpa_with_punctuation)
#   replace_str = re.escape(''.join(trim_symbols))
#   pattern = re.compile(rf"[{replace_str}]+")
#   # remove words consisting only of punctuation since these were annotated as silence
#   words_arpa_with_punctuation = [word for word in words_arpa_with_punctuation if len(
#     re.sub(pattern, "", ''.join(word))) > 0]
#   symbols_arpa = words_to_symbols(words_arpa_with_punctuation)

#   ignore_merge_symbols = {" "}

#   final_arpa_symbols = symbols_arpa

#   final_arpa_symbols = merge_right(
#     symbols=final_arpa_symbols,
#     ignore_merge_symbols=ignore_merge_symbols,
#     merge_symbols=trim_symbols,
#     insert_symbol=" ",
#   )

#   final_arpa_symbols = merge_left(
#     symbols=final_arpa_symbols,
#     ignore_merge_symbols=ignore_merge_symbols,
#     merge_symbols=trim_symbols,
#     insert_symbol=" ",
#   )

#   final_arpa_symbols = [symbol for symbol in final_arpa_symbols if symbol != " "]

#   reference_tier_intervals: List[Interval] = phoneme_tier.intervals
#   new_tier = IntervalTier(
#     minTime=phoneme_tier.minTime,
#     maxTime=phoneme_tier.maxTime,
#     name=new_tier,
#   )

#   for interval in reference_tier_intervals:
#     new_arpa_symbol = ""

#     if not interval_is_None_or_whitespace(interval):
#       new_arpa_symbol = final_arpa_symbols.pop(0)
#       logger.debug(f"Assigned \"{new_arpa_symbol}\" to \"{interval.mark}\".")

#     new_arpa_interval = Interval(
#       minTime=interval.minTime,
#       maxTime=interval.maxTime,
#       mark=new_arpa_symbol,
#     )

#     new_tier.addInterval(new_arpa_interval)

#   if overwrite_tier:
#     update_or_add_tier(grid, new_tier)
#   else:
#     grid.append(new_tier)


# def transcribe_words_to_arpa(grid: TextGrid, original_text_tier_name: str, tier_name: str, consider_annotations: bool, ignore_case: bool, cache: LookupCache, overwrite_existing_tier: bool):
#   logger = getLogger(__name__)

#   original_text_tier: IntervalTier = grid.getFirst(original_text_tier_name)
#   if original_text_tier is None:
#     raise Exception("Original text-tier not found!")

#   if grid.getFirst(tier_name) is not None and not overwrite_existing_tier:
#     raise Exception("ARPA tier already exists!")

#   original_text = tier_to_text(original_text_tier)

#   symbols = text_to_symbols(
#     lang=Language.ENG,
#     text=original_text,
#     text_format=SymbolFormat.GRAPHEMES,
#   )

#   symbols_arpa = sentences2pronunciations_from_cache_mp(
#     cache=cache,
#     sentences={symbols},
#     annotation_split_symbol="/",
#     chunksize=1,
#     consider_annotation=consider_annotations,
#     ignore_case=ignore_case,
#     n_jobs=1,
#   )[symbols]

#   words_arpa_with_punctuation = symbols_to_words(symbols_arpa)

#   original_text_tier_intervals: List[Interval] = original_text_tier.intervals

#   new_arpa_tier = IntervalTier(
#     minTime=original_text_tier.minTime,
#     maxTime=original_text_tier.maxTime,
#     name=tier_name,
#   )

#   for interval in original_text_tier_intervals:
#     new_arpa = ""

#     if not interval_is_empty(interval):
#       interval_contains_space = " " in interval.mark
#       if interval_contains_space:
#         logger.error(
#           f"Invalid interval mark: \"{interval.mark}\" on [{interval.minTime}, {interval.maxTime}]!")
#         # raise Exception()
#       new_arpa_tuple = words_arpa_with_punctuation.pop(0)
#       # if new_arpa_tuple == (SIL,):
#       #  logger.info(f"Skip {interval.mark} as it is only sil.")
#       #  continue
#       new_arpa = " ".join(new_arpa_tuple)
#       logger.debug(f"Assigned \"{new_arpa}\" to \"{interval.mark}\".")

#     new_arpa_interval = Interval(
#       minTime=interval.minTime,
#       maxTime=interval.maxTime,
#       mark=new_arpa,
#     )

#     new_arpa_tier.addInterval(new_arpa_interval)

#   if overwrite_existing_tier:
#     update_or_add_tier(grid, new_arpa_tier)
#   else:
#     grid.append(new_arpa_tier)
