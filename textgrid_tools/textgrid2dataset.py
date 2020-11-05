import os
from argparse import ArgumentParser
from dataclasses import astuple, dataclass
from logging import Logger, getLogger
from typing import List, Tuple

import numpy as np
import pandas as pd
from scipy.io.wavfile import read, write
from tqdm import tqdm

from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.utils import ms_to_samples


@dataclass
class Entry():
  entry_id: int
  text: str
  wav: str
  duration: float
  speaker: str


def save(items: List[Entry], file_path: str):
  data = [astuple(xi) for xi in items]
  dataframe = pd.DataFrame(data)
  dataframe.to_csv(file_path, header=None, index=None, sep="\t")


def init_textgrid2dataset_parser(parser: ArgumentParser):
  parser.add_argument("-f", "--file", type=str, required=True, help="TextGrid input filepath.")
  parser.add_argument("-t", "--text-tier-name", type=str, default="sentences", help="")
  parser.add_argument("-w", "--wav-file", type=str, required=True, help="")
  parser.add_argument("-d", "--duration-s-max", type=float, required=True, help="")
  parser.add_argument("-o", "--output-dir", type=str, required=True, help="")
  parser.add_argument("-n", "--output-name", type=str, required=True, help="")
  parser.add_argument("-s", "--speaker-name", type=str, required=True, help="")
  return convert_textgrid2dataset


def convert_textgrid2dataset(file: str, tier_name: str, wav_file: str, duration_s_max: float, output_dir: str, output_name: str, speaker_name: str) -> None:
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
  audio_dirpath = os.path.join(dest_dirpath, "audio")
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
    ))
    wav_filepath = os.path.join(audio_dirpath, wav_name)
    write(wav_filepath, sampling_rate, wav)
  data_filepath = os.path.join(dest_dirpath, "data.csv")
  save(res, data_filepath)
