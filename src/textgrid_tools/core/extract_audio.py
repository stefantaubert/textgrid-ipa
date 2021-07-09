import os
from argparse import ArgumentParser
from collections import OrderedDict
from dataclasses import astuple, dataclass
from logging import Logger, getLogger
from typing import List, Optional
from typing import OrderedDict as OrderedDictType
from typing import Tuple

import numpy as np
import pandas as pd
from numpy.core.fromnumeric import mean
from numpy.lib.function_base import median
from pandas.core.frame import DataFrame
from scipy.io.wavfile import read, write
from text_utils.language import Language
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.utils import (check_interval_has_content,
                                  grid_contains_tier, ms_to_samples)
from tqdm import tqdm

STRIP_SYMBOLS = ".?!,;-: "


@dataclass()
class AudioExtract():
  interval_start: float
  interval_end: float
  duration_s: float
  graphemes: str
  phonemes: str
  phones: str
  audio: np.ndarray


def extract_words_to_audio(grid: TextGrid, graphemes_tier_name: str, phonemes_tier_name: str, phones_tier_name: str, wav: np.ndarray, sr: int) -> OrderedDictType[Tuple[str, str], List[AudioExtract]]:
  logger = getLogger(__name__)
  empty_result: OrderedDictType[Tuple[str, str], List[AudioExtract]] = OrderedDict()

  if not grid_contains_tier(grid, graphemes_tier_name):
    logger.error(f"Tier {graphemes_tier_name} does not exist!")
    return empty_result

  if not grid_contains_tier(grid, phonemes_tier_name):
    logger.error(f"Tier {phonemes_tier_name} does not exist!")
    return empty_result

  if not grid_contains_tier(grid, phones_tier_name):
    logger.error(f"Tier {phones_tier_name} does not exist!")
    return empty_result

  tier_graphemes: IntervalTier = grid.getFirst(graphemes_tier_name)
  tier_phonemes: IntervalTier = grid.getFirst(phonemes_tier_name)
  tier_phones: IntervalTier = grid.getFirst(phones_tier_name)

  if len(tier_graphemes) != len(tier_phonemes) != len(tier_phones):
    logger.error(
      f"The tiers do not have the same amount of intervals {len(tier_graphemes)} ({tier_graphemes}) vs. {len(tier_phonemes)} ({tier_phonemes}) vs. {len(tier_phones)} ({tier_phones})!")
    return empty_result

  result: OrderedDictType[Tuple[str, str], List[AudioExtract]] = OrderedDict()

  for interval_graphemes, interval_phonemes, interval_phones in zip(tier_graphemes, tier_phonemes, tier_phones):

    graphemes = strip_irrelevant_symbols(interval_graphemes.mark)
    phonemes = strip_irrelevant_symbols(interval_phonemes.mark)
    phones = strip_irrelevant_symbols(interval_phones.mark)
    not_allowed_symbols = "<", ">", ":", "\"", "\\", "|", "?", "*"
    if graphemes == '':
      continue

    if contains_any_of_the_symbols(graphemes, not_allowed_symbols) or contains_any_of_the_symbols(phonemes, not_allowed_symbols) or contains_any_of_the_symbols(phones, not_allowed_symbols):
      logger.warning(
        f"Ignoring {graphemes} - {phonemes} - {phones} on interval [{interval_graphemes.minTime}, {interval_graphemes.maxTime}] due to not allowed symbols: {' '.join(not_allowed_symbols)}")
      continue

    if not (interval_graphemes.minTime == interval_phonemes.minTime == interval_phones.minTime):
      logger.error(
        f"Interval minimum of the three layers does not match at: {interval_graphemes.minTime}!")
      return empty_result

    if not (interval_graphemes.maxTime == interval_phonemes.maxTime == interval_phones.maxTime):
      logger.error(
        f"Interval maximum of the three layers does not match at: {interval_graphemes.maxTime}!")
      return empty_result

    start_samples = ms_to_samples(interval_graphemes.minTime * 1000, sr)
    end_samples = ms_to_samples(interval_graphemes.maxTime * 1000, sr)
    part = wav[start_samples:end_samples]

    extract = AudioExtract(
      interval_start=interval_graphemes.minTime,
      interval_end=interval_graphemes.maxTime,
      duration_s=interval_graphemes.maxTime - interval_graphemes.minTime,
      graphemes=graphemes,
      phonemes=phonemes,
      phones=phones,
      audio=part,
    )

    key = (extract.graphemes, extract.phonemes)

    if key not in result:
      result[key] = []
    result[key].append(extract)

  result = OrderedDict({k: result[k] for k in sorted(result.keys())})

  return result


def contains_any_of_the_symbols(text: str, symbols: List[str]):
  for s in symbols:
    if s in text:
      return True
  return False


def strip_irrelevant_symbols(symbols: str) -> str:
  res = symbols.strip(STRIP_SYMBOLS)
  return res


def get_extracts_df(extracts: List[AudioExtract]) -> DataFrame:
  res_data = []
  for i, extract in enumerate(extracts):
    res_data.append((
      i+1,
      extract.graphemes,
      extract.phonemes,
      extract.phones,
      extract.duration_s,
      extract.interval_start,
      extract.interval_end,
    ))

  res = DataFrame(
    data=res_data,
    columns=[
      "Nr",
      "Graphemes",
      "Phonemes",
      "Phones",
      "Duration (s)",
      "Interval start",
      "Interval end",
    ]
  )

  return res
