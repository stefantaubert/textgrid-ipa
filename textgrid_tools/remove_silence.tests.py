import unittest

import numpy as np

from textgrid_tools.remove_silence import remove_silence


class UnitTests(unittest.TestCase):
  def test(self):
    remove_silence(
      file="/datasets/Recordings/40mins/raw/annotation.TextGrid",
      output="/datasets/Recordings/40mins/nosil/annotation.TextGrid",
      tier_name="sentences",
      wav_file="/datasets/Recordings/40mins/raw/audio.wav",
      wav_output_file="/datasets/Recordings/40mins/nosil/audio.wav",
    )

  def test_ipa(self):

    wav_dummy = np.ones(shape=(1000, 2), dtype=np.int)

    wav_dummy[500][0] = 0
    wav_dummy[500][1] = 0

    wav_dummy[501][0] = 0
    wav_dummy[501][1] = 0

    res = np.delete(wav_dummy, [500, 501, 0], axis=0)
    self.assertEqual((997, 2), res.shape)
    self.assertEqual(1, np.min(res))


if __name__ == '__main__':
  suite = unittest.TestLoader().loadTestsFromTestCase(UnitTests)
  unittest.TextTestRunner(verbosity=2).run(suite)
