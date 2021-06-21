from logging import getLogger
from pathlib import Path
from shutil import copy, rmtree
from typing import Optional

from scipy.io.wavfile import read, write
from text_utils import EngToIpaMode
from textgrid.textgrid import TextGrid
from textgrid_tools.core.main import (add_ipa_tier, add_pause_tier,
                                      add_words_tier, get_template_textgrid,
                                      log_tier_stats)


def to_dataset(base_dir: Path, recording_name: str, step: str, tier: str, duration_s_max: float, remove_silence_tier: Optional[str], output_dir: Path, output_name: str, speaker_name: str, speaker_gender: str, speaker_accent: str, overwrite_step: bool, overwrite_tier: bool):
  pass
