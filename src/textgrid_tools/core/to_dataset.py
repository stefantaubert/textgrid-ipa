import os
from argparse import ArgumentParser
from dataclasses import astuple, dataclass
from logging import Logger, getLogger
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from numpy.core.fromnumeric import mean
from numpy.lib.function_base import median
from scipy.io.wavfile import read, write
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.utils import (check_interval_has_content,
                                  grid_contains_tier, ms_to_samples)
from tqdm import tqdm

OATA_CSV_NAME = "data.csv"
AUDIO_FOLDER_NAME = "audio"


@dataclass
class Entry():
  entry_id: int
  text: str
  wav: str
  duration: float
  speaker: str
  gender: str
  accent: str


def save(items: List[Entry], file_path: str):
  data = [astuple(xi) for xi in items]
  dataframe = pd.DataFrame(data)
  dataframe.to_csv(file_path, header=None, index=None, sep="\t")


def convert_textgrid2dataset(grid: TextGrid, tier_name: str, wav: np.ndarray, sr: int, duration_s_max: float, speaker_name: str, speaker_gender: str, speaker_accent: str, ignore_empty_marks: bool) -> List[Tuple[Entry, np.ndarray]]:
  logger = getLogger()
  logger.info(f"Calculating durations of tier {tier_name}...")

  in_wav = wav
  if ignore_empty_marks:
    new_wav = remove_empty_marks(
      grid=grid,
      tier_name=tier_name,
      in_wav=wav,
      sr=sr,
    )
    in_wav = new_wav

  in_tier: IntervalTier = grid.getFirst(tier_name)
  in_tier_intervals: List[Interval] = in_tier.intervals

  collected_duration = 0
  collected_parts = []
  collected_texts = []
  final_parts: List[Tuple[str, np.ndarray, float]] = list()

  for interval in in_tier_intervals:
    current_duration = interval.maxTime - interval.minTime

    start = ms_to_samples(interval.minTime * 1000, sr)
    end = ms_to_samples(interval.maxTime * 1000, sr)
    parts = in_wav[start:end]

    if collected_duration + current_duration > duration_s_max:
      part_is_bigger_than_max = len(collected_parts) == 0
      if part_is_bigger_than_max:
        logger.warning(
          f"Found too long recording interval (longer than {duration_s_max}s): {collected_duration + current_duration}s for \"{interval.mark}\"!")
        final_parts.append((interval.mark, parts, current_duration))
        continue
      p = np.concatenate(collected_parts)
      text = " ".join(collected_texts)
      final_parts.append((text, p, collected_duration))
      collected_parts.clear()
      collected_texts.clear()
      collected_duration = 0

    collected_parts.append(parts)
    collected_texts.append(interval.mark)
    collected_duration = collected_duration + current_duration

  res: List[Tuple[Entry, np.ndarray]] = []
  for i, parts in enumerate(final_parts):
    text, out_wav, current_duration = parts
    wav_name = f"{i}.wav"
    # logger.info(f"{text}, {len(wav)}")
    res.append((Entry(
      entry_id=i,
      text=text,
      wav=wav_name,
      duration=current_duration,
      speaker=speaker_name,
      gender=speaker_gender,
      accent=speaker_accent,
    ), out_wav))

  durations = [x.duration for x, _ in res]

  logger.info(f"Minimal duration of one utterance: {min(durations):.2f}s")
  logger.info(f"Maximal duration of one utterance: {max(durations):.2f}s")
  logger.info(f"Mean duration of an utterance: {mean(durations):.2f}s")
  logger.info(f"Median duration of an utterance: { median(durations):.2f}s")
  logger.info(
    f"Total duration of all utterances: {sum(durations):.0f}s ({sum(durations)/60:.2f}min)")
  logger.info(f"Count of utterances: {len(durations)}")

  return res


def remove_empty_marks(grid: TextGrid, tier_name: str, in_wav: np.ndarray, sr: int) -> np.ndarray:
  logger = getLogger(__name__)
  assert grid_contains_tier(grid, tier_name)
  in_tier: IntervalTier = grid.getFirst(tier_name)
  in_tier_intervals: List[Interval] = in_tier.intervals
  in_tier_intervals_reversed = in_tier_intervals[::-1]

  new_intervals: List[Interval] = list()
  remove_samples = list()
  for interval in tqdm(in_tier_intervals_reversed):
    has_content = check_interval_has_content(interval)
    if has_content:
      new_intervals.append(interval)
    else:
      remove = get_remove_samples(interval.minTime, interval.maxTime, sr)
      remove_samples.extend(remove)
      #in_wav = remove_from_wav(in_wav, interval.minTime, interval.maxTime, sr)

  logger.info("Deleting pauses from wav...")
  logger.info(in_wav.shape)
  logger.info(len(remove_samples))
  out_wav = np.delete(in_wav, remove_samples, axis=0)
  logger.info("Done.")
  logger.info(out_wav.shape)

  new_intervals = new_intervals[::-1]
  word_durations: List[Tuple[str, float]] = list()

  for interval in new_intervals:
    duration = interval.maxTime - interval.minTime
    word_durations.append((interval.mark, duration))

  min_time = 0
  max_time = 0

  word_tier = IntervalTier(
    name=tier_name,
    minTime=min_time,
    maxTime=max_time,
  )

  for _, word_duration in enumerate(word_durations):
    word, duration = word_duration
    max_time = min_time + duration
    word_interval = Interval(
      minTime=min_time,
      maxTime=max_time,
      mark=word,
    )
    word_tier.addInterval(word_interval)
    min_time = max_time

  word_tier.maxTime = max_time

  # for i, t in enumerate(grid.tiers):
  #   if t.name == tier_name:
  #     grid.tiers.pop(i)
  #     break

  grid.tiers.clear()
  grid.minTime = word_tier.minTime
  grid.maxTime = word_tier.maxTime
  grid.append(word_tier)

  return out_wav


def get_remove_samples(start_s: float, end_s: float, sr: int) -> List[int]:
  start_ms = start_s * 1000
  end_ms = end_s * 1000
  start_samples = ms_to_samples(start_ms, sr)
  sample_count_to_remove = ms_to_samples(end_ms - start_ms, sr)
  result = list(range(start_samples, start_samples + sample_count_to_remove))
  return result


# def remove_from_wav(wav: np.ndarray, start_s: float, end_s: float, sr: int) -> np.ndarray:
#   start_samples = ms_to_samples(start_s, sr)
#   sample_count_to_remove = ms_to_samples(end_s - start_s, sr)
#   return remove_from_array(wav, start_samples, sample_count_to_remove)


# def remove_from_array(wav: np.ndarray, start_s: int, count: int) -> np.ndarray:
#   wav = np.delete(wav, list(range(start_s, start_s + count)), axis=0)
#   return wav
