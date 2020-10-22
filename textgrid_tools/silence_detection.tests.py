import unittest

from scipy.io.wavfile import read

from textgrid_tools.silence_detection import mask_silence


class UnitTests(unittest.TestCase):

  def test_ipa(self):
    file = "/datasets/test.wav"
    _, wav = read(file)

    res = mask_silence(wav, silence_boundary=0.30, chunk_size=int(96000 / 2))
    print(res)


if __name__ == '__main__':
  suite = unittest.TestLoader().loadTestsFromTestCase(UnitTests)
  unittest.TextTestRunner(verbosity=2).run(suite)
