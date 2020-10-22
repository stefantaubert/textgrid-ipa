import unittest

from scipy.io.wavfile import read

from textgrid_tools.convert import add_ipa_tier, add_pause_tier, add_words_tier
from textgrid.textgrid import TextGrid


class UnitTests(unittest.TestCase):

  def test_ipa(self):

    grid = TextGrid()
    # grid.read("/datasets/sentences.TextGrid")
    grid.read("/datasets/sven_prototype.TextGrid")

    file = "/datasets/test.wav"
    sampling_rate, wav = read(file)
    grid = add_pause_tier(
      # grid=None,
      grid=grid,
      wav=wav,
      sr=sampling_rate,
      out_tier_name="pause:gen",
      chunk_size_ms=50,
      silence_boundary=0.25,
      min_silence_duration_ms=1000,
    )

    add_words_tier(
      grid=grid,
      in_tier_name="sentences",
      out_tier_name="words:gen",
    )

    add_ipa_tier(
      grid=grid,
      in_tier_name="words:gen",
      out_tier_name="ipa:gen",
    )

    grid.write("/datasets/sentences_out.TextGrid")

    self.assertEqual("IPA-standard", grid.tiers[-1].name)


if __name__ == '__main__':
  suite = unittest.TestLoader().loadTestsFromTestCase(UnitTests)
  unittest.TextTestRunner(verbosity=2).run(suite)
