import os
from argparse import ArgumentParser
from dataclasses import astuple, dataclass
from logging import Logger, getLogger
from typing import List, Tuple

import numpy as np
import pandas as pd
from numpy.core.fromnumeric import mean
from numpy.lib.function_base import median
from scipy.io.wavfile import read, write
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.utils import ms_to_samples
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


def convert_textgrid2dataset(grid: TextGrid, tier_name: str, wav: np.ndarray, sr: int, duration_s_max: float, speaker_name: str, speaker_gender: str, speaker_accent: str) -> List[Tuple[Entry, np.ndarray]]:
  logger = getLogger()
  logger.info(f"Calculating durations of tier {tier_name}...")

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
    parts = wav[start:end]

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

  durations = [x.duration for x in res]

  logger.info(f"Minimal duration of one utterance: {min(durations):.2f}s")
  logger.info(f"Maximal duration of one utterance: {max(durations):.2f}s")
  logger.info(f"Mean duration of an utterance: {mean(durations):.2f}s")
  logger.info(f"Median duration of an utterance: { median(durations):.2f}s")
  logger.info(
    f"Total duration of all utterances: {sum(durations):.0f}s ({sum(durations)/60:.2f}min)")
  logger.info(f"Count of utterances: {len(durations)}")

  return res