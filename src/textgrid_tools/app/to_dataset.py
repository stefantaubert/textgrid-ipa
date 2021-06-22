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
