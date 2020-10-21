from dataclasses import dataclass
from math import ceil, inf, log10
from typing import List, Tuple

import numpy as np
from scipy.io.wavfile import read, write
from tqdm import tqdm
from tqdm.std import trange

FLOAT32_64_MIN_WAV = -1.0
INT16_MIN = np.iinfo(np.int16).min  # -32768 = -(2**15)
INT32_MIN = np.iinfo(np.int32).min  # -2147483648 = -(2**31)


def get_dBFS(wav: np.ndarray, max_value: float) -> float:
  value = np.sqrt(np.mean((wav / max_value)**2))
  if value == 0:
    return -inf

  result = 20 * log10(value)
  return result


def get_duration_s(samples: int, sampling_rate: int) -> float:
  duration = samples / sampling_rate
  return duration


def ms_to_samples(ms, sampling_rate):
  res = int(ms * sampling_rate / 1000)
  return res


@dataclass
class Chunk:
  size: int
  is_silence: bool


def mask_silence(wav: np.ndarray, silence_boundary: float, chunk_size: int) -> List[Chunk]:
  assert chunk_size > 0
  if chunk_size > len(wav):
    chunk_size = len(wav)

  trim = 0
  max_value = -1 * get_min_value(wav.dtype)
  len_first_channel = wav.shape[0]
  its = len(wav) / chunk_size
  its = ceil(its)
  res: List[Chunk] = list()

  dBFSs: List[float] = list()
  for _ in trange(its):
    dBFS = get_dBFS(wav[trim:trim + chunk_size], max_value)
    dBFSs.append(dBFS)
    trim += chunk_size

  print(dBFSs)
  print(min(dBFSs))
  print(max(dBFSs))
  diff = abs(abs(min(dBFSs)) - abs(max(dBFSs)))
  threshold = diff * silence_boundary
  silence_threshold = min(dBFSs) + threshold

  trim = 0
  for dBFS in tqdm(dBFSs):
    is_silence = dBFS < silence_threshold
    chunk_len = len(wav[trim:trim + chunk_size])
    chunk = Chunk(
      size=chunk_len,
      is_silence=is_silence
    )
    res.append(chunk)

    trim += chunk_size

  return res


def get_min_value(dtype):
  if dtype == np.int16:
    return INT16_MIN

  if dtype == np.int32:
    return INT32_MIN

  if dtype == np.float32 or dtype == np.float64:
    return FLOAT32_64_MIN_WAV

  assert False


if __name__ == "__main__":
  file = "/datasets/test.wav"
  sampling_rate, wav = read(file)

  res = mask_silence(wav, silence_threshold=-20, chunk_size=int(96000 / 2))
  print(res)
