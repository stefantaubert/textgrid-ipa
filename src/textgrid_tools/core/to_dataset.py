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
from tqdm import tqdm

from textgrid_tools.utils import ms_to_samples

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


def convert_textgrid2dataset(file: str, tier_name: str, wav_file: str, duration_s_max: float, output_dir: str, output_name: str, speaker_name: str, speaker_gender: str, speaker_accent: str) -> None:
  logger = getLogger()
  grid = TextGrid()
  grid.read(file)

  logger.info(f"Calculating durations of tier {tier_name}...")

  in_tier: IntervalTier = grid.getFirst(tier_name)
  in_tier_intervals: List[Interval] = in_tier.intervals
  sampling_rate, wav = read(wav_file)

  collected_duration = 0
  collected_parts = []
  collected_texts = []
  final_parts: List[Tuple[str, np.ndarray, float]] = list()

  for interval in in_tier_intervals:
    current_duration = interval.maxTime - interval.minTime

    start = ms_to_samples(interval.minTime * 1000, sampling_rate)
    end = ms_to_samples(interval.maxTime * 1000, sampling_rate)
    part = wav[start:end]

    if collected_duration + current_duration > duration_s_max:
      part_is_bigger_than_max = len(collected_parts) == 0
      if part_is_bigger_than_max:
        logger.warning(
          f"Found to long recording intervall (longer than {duration_s_max}s): {collected_duration + current_duration}s for \"{interval.mark}\"")
        final_parts.append((interval.mark, part, current_duration))
        continue
      p = np.concatenate(collected_parts)
      text = " ".join(collected_texts)
      final_parts.append((text, p, collected_duration))
      collected_parts.clear()
      collected_texts.clear()
      collected_duration = 0

    collected_parts.append(part)
    collected_texts.append(interval.mark)
    collected_duration = collected_duration + current_duration

  logger.info("Writing outputs...")
  dest_dirpath = os.path.join(output_dir, output_name)
  audio_dirpath = os.path.join(dest_dirpath, AUDIO_FOLDER_NAME)
  os.makedirs(audio_dirpath, exist_ok=True)
  res: List[Entry] = list()
  for i, part in enumerate(tqdm(final_parts)):
    text, wav, current_duration = part
    wav_name = f"{i}.wav"
    # logger.info(f"{text}, {len(wav)}")
    res.append(Entry(
      entry_id=i,
      text=text,
      wav=wav_name,
      duration=current_duration,
      speaker=speaker_name,
      gender=speaker_gender,
      accent=speaker_accent,
    ))
    wav_filepath = os.path.join(audio_dirpath, wav_name)
    write(wav_filepath, sampling_rate, wav)
  durations = [x.duration for x in res]

  logger.info(f"Minimal duration of one utterance: {min(durations):.2f}s")
  logger.info(f"Maximal duration of one utterance: {max(durations):.2f}s")
  logger.info(f"Mean duration of an utterance: {mean(durations):.2f}s")
  logger.info(f"Median duration of an utterance: { median(durations):.2f}s")
  logger.info(f"Total duration of all utterances: {sum(durations):.0f}s ({sum(durations)/60:.2f}min)")
  logger.info(f"Count of utterances: {len(durations)}")

  data_filepath = os.path.join(dest_dirpath, OATA_CSV_NAME)
  save(res, data_filepath)
