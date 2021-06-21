import unittest

from scipy.io.wavfile import read

from textgrid_tools.wav2pauses import (Chunk, add_end_buffer, add_pause,
                                       add_start_buffer, mask_silence,
                                       merge_content_chunks,
                                       merge_marked_chunks,
                                       merge_same_coherent_chunks)


class UnitTests(unittest.TestCase):

  # region merge_same_coherent_chunks
  def test_merge_same_coherent_chunks__empty_list__returns_empty_list(self):
    x = []
    res = merge_same_coherent_chunks(x)
    self.assertEqual([], res)

  def test_merge_same_coherent_chunks__single_entry__returns_single_entry(self):
    x = [Chunk(size=5, is_silence=True)]
    res = merge_same_coherent_chunks(x)
    self.assertEqual([Chunk(size=5, is_silence=True)], res)

  def test_merge_same_coherent_chunks__two_silences__returns_one_silence(self):
    x = [
      Chunk(size=5, is_silence=True),
      Chunk(size=5, is_silence=True)
    ]

    res = merge_same_coherent_chunks(x)
    self.assertEqual([Chunk(size=10, is_silence=True)], res)

  def test_merge_same_coherent_chunks__two_content__returns_one_content(self):
    x = [
      Chunk(size=5, is_silence=False),
      Chunk(size=5, is_silence=False)
    ]

    res = merge_same_coherent_chunks(x)
    self.assertEqual([Chunk(size=10, is_silence=False)], res)

  def test_merge_same_coherent_chunks__two_different__returns_two_different(self):
    x = [
      Chunk(size=5, is_silence=True),
      Chunk(size=5, is_silence=False)
    ]

    res = merge_same_coherent_chunks(x)
    self.assertEqual([
      Chunk(size=5, is_silence=True),
      Chunk(size=5, is_silence=False)
    ], res)

  def test_merge_same_coherent_chunks__multiple_coherent_are_merged(self):
    x = [
       Chunk(size=5, is_silence=False),
       Chunk(size=5, is_silence=False),
       Chunk(size=5, is_silence=False),
       Chunk(size=5, is_silence=False),
       Chunk(size=5, is_silence=False),
     ]

    res = merge_same_coherent_chunks(x)
    self.assertEqual([
        Chunk(size=25, is_silence=False)
      ], res)

  def test_merge_same_coherent_chunks__multiple_coherent_with_diff_are_merged(self):
    x = [
       Chunk(size=5, is_silence=False),
       Chunk(size=5, is_silence=False),
       Chunk(size=5, is_silence=False),
       Chunk(size=5, is_silence=True),
       Chunk(size=5, is_silence=True),
       Chunk(size=5, is_silence=False),
       Chunk(size=5, is_silence=False),
     ]

    res = merge_same_coherent_chunks(x)
    self.assertEqual([
        Chunk(size=15, is_silence=False),
        Chunk(size=10, is_silence=True),
        Chunk(size=10, is_silence=False),
      ], res)
  # endregion

  # region add_end_buffer
  def test_add_end_buffer__empty_list_returns_empty_list(self):
    res = add_end_buffer([], [], 1)
    self.assertEqual([], res)

  def test_add_end_buffer__one_entry_returns_one_chunk(self):
    x = [
      Chunk(size=1, is_silence=False),
    ]
    mask = [True]

    res = add_end_buffer(x, mask, 1)

    self.assertEqual([
      Chunk(size=1, is_silence=False),
    ], res)

  def test_add_end_buffer__first_entry__adds_buffer(self):
    x = [
      Chunk(size=1, is_silence=False),
      Chunk(size=2, is_silence=False),
    ]
    mask = [True, False]

    res = add_end_buffer(x, mask, 1)

    self.assertEqual([
      Chunk(size=2, is_silence=False),
      Chunk(size=1, is_silence=False),
    ], res)

  def test_add_end_buffer__last_entry__adds_no_buffer(self):
    x = [
      Chunk(size=1, is_silence=False),
      Chunk(size=2, is_silence=False),
    ]
    mask = [False, True]

    res = add_end_buffer(x, mask, 1)

    self.assertEqual([
      Chunk(size=1, is_silence=False),
      Chunk(size=2, is_silence=False),
    ], res)

  def test_add_end_buffer__first_entry_too_much_add__adds_buffer(self):
    x = [
      Chunk(size=1, is_silence=False),
      Chunk(size=2, is_silence=False),
    ]
    mask = [True, False]

    res = add_end_buffer(x, mask, 10)

    self.assertEqual([
      Chunk(size=3, is_silence=False),
      Chunk(size=0, is_silence=False),
    ], res)

  def test_add_end_buffer__middle_entry__adds_buffer(self):
    x = [
      Chunk(size=1, is_silence=False),
      Chunk(size=2, is_silence=False),
      Chunk(size=3, is_silence=False),
    ]
    mask = [False, True, False]

    res = add_end_buffer(x, mask, 1)

    self.assertEqual([
      Chunk(size=1, is_silence=False),
      Chunk(size=3, is_silence=False),
      Chunk(size=2, is_silence=False),
    ], res)

  def test_add_end_buffer__first_entry_too_much_add__adds_buffer_and_not_subtracts_on_second_next_buffer(self):
    x = [
      Chunk(size=1, is_silence=False),
      Chunk(size=2, is_silence=False),
      Chunk(size=3, is_silence=False),
    ]
    mask = [True, False, False]

    res = add_end_buffer(x, mask, 10)

    self.assertEqual([
      Chunk(size=3, is_silence=False),
      Chunk(size=0, is_silence=False),
      Chunk(size=3, is_silence=False),
    ], res)

  def test_add_end_buffer__all_false__adds_no_buffer(self):
    x = [
      Chunk(size=1, is_silence=False),
      Chunk(size=2, is_silence=False),
      Chunk(size=3, is_silence=False),
    ]
    mask = [False, False, False]

    res = add_end_buffer(x, mask, 1)

    self.assertEqual([
      Chunk(size=1, is_silence=False),
      Chunk(size=2, is_silence=False),
      Chunk(size=3, is_silence=False),
    ], res)

  # endregion

  # region add_start_buffer

  def test_add_start_buffer__empty_list_returns_empty_list(self):
    res = add_start_buffer([], [], 1)
    self.assertEqual([], res)

  def test_add_start_buffer__one_entry_returns_one_chunk(self):
    x = [
      Chunk(size=1, is_silence=False),
    ]
    mask = [True]

    res = add_start_buffer(x, mask, 1)

    self.assertEqual([
      Chunk(size=1, is_silence=False),
    ], res)

  def test_add_start_buffer__first_entry__adds_no_buffer(self):
    x = [
      Chunk(size=1, is_silence=False),
      Chunk(size=2, is_silence=False),
    ]
    mask = [True, False]

    res = add_start_buffer(x, mask, 1)

    self.assertEqual([
      Chunk(size=1, is_silence=False),
      Chunk(size=2, is_silence=False),
    ], res)

  def test_add_start_buffer__last_entry__adds_buffer(self):
    x = [
      Chunk(size=1, is_silence=False),
      Chunk(size=2, is_silence=False),
    ]
    mask = [False, True]

    res = add_start_buffer(x, mask, 1)

    self.assertEqual([
      Chunk(size=0, is_silence=False),
      Chunk(size=3, is_silence=False),
    ], res)

  def test_add_start_buffer__last_entry_too_much_add__adds_buffer(self):
    x = [
      Chunk(size=1, is_silence=False),
      Chunk(size=2, is_silence=False),
    ]
    mask = [False, True]

    res = add_start_buffer(x, mask, 10)

    self.assertEqual([
      Chunk(size=0, is_silence=False),
      Chunk(size=3, is_silence=False),
    ], res)

  def test_add_start_buffer__middle_entry__adds_buffer(self):
    x = [
      Chunk(size=1, is_silence=False),
      Chunk(size=2, is_silence=False),
      Chunk(size=3, is_silence=False),
    ]
    mask = [False, True, False]

    res = add_start_buffer(x, mask, 1)

    self.assertEqual([
      Chunk(size=0, is_silence=False),
      Chunk(size=3, is_silence=False),
      Chunk(size=3, is_silence=False),
    ], res)

  def test_add_start_buffer__last_entry_too_much_add__adds_buffer_and_not_subtracts_on_second_previous_buffer(self):
    x = [
      Chunk(size=1, is_silence=False),
      Chunk(size=2, is_silence=False),
      Chunk(size=3, is_silence=False),
    ]
    mask = [False, False, True]

    res = add_start_buffer(x, mask, 10)

    self.assertEqual([
      Chunk(size=1, is_silence=False),
      Chunk(size=0, is_silence=False),
      Chunk(size=5, is_silence=False),
    ], res)

  def test_add_start_buffer__all_false__adds_no_buffer(self):
    x = [
      Chunk(size=1, is_silence=False),
      Chunk(size=2, is_silence=False),
      Chunk(size=3, is_silence=False),
    ]
    mask = [False, False, False]

    res = add_start_buffer(x, mask, 1)

    self.assertEqual([
      Chunk(size=1, is_silence=False),
      Chunk(size=2, is_silence=False),
      Chunk(size=3, is_silence=False),
    ], res)

  # endregion

  # region merge_marked_chunks

  def test_merge_marked_chunks__empty_list_returns_empty_list(self):
    res = merge_marked_chunks([], [])
    self.assertEqual([], res)

  def test_merge_marked_chunks__one_entry_returns_one_chunk(self):
    x = [
      Chunk(size=1, is_silence=False),
    ]
    mask = [True]

    res = merge_marked_chunks(x, mask)

    self.assertEqual([
      Chunk(size=1, is_silence=False),
    ], res)

  def test_merge_marked_chunks__first_true_second_false_returns_merged_second_entry(self):
    x = [
      Chunk(size=1, is_silence=False),
      Chunk(size=2, is_silence=False),
    ]
    mask = [True, False]

    res = merge_marked_chunks(x, mask)

    self.assertEqual([
      Chunk(size=3, is_silence=False)
    ], res)

  def test_merge_marked_chunks__first_false_second_true_returns_merged_first_entry(self):
    x = [
      Chunk(size=1, is_silence=False),
      Chunk(size=2, is_silence=False),
    ]
    mask = [False, True]

    res = merge_marked_chunks(x, mask)

    self.assertEqual([
      Chunk(size=3, is_silence=False)
    ], res)

  def test_merge_marked_chunks__first_and_last_false_second_true_returns_merged_last_entry(self):
    x = [
      Chunk(size=1, is_silence=False),
      Chunk(size=2, is_silence=False),
      Chunk(size=3, is_silence=False),
    ]
    mask = [False, True, False]

    res = merge_marked_chunks(x, mask)

    self.assertEqual([
      Chunk(size=1, is_silence=False),
      Chunk(size=5, is_silence=False)
    ], res)

  def test_merge_marked_chunks__first_and_last_true_second_false_returns_merged_entry(self):
    x = [
      Chunk(size=1, is_silence=False),
      Chunk(size=2, is_silence=False),
      Chunk(size=3, is_silence=False),
    ]
    mask = [True, False, True]

    res = merge_marked_chunks(x, mask)

    self.assertEqual([
      Chunk(size=6, is_silence=False)
    ], res)
# endregion


if __name__ == '__main__':
  suite = unittest.TestLoader().loadTestsFromTestCase(UnitTests)
  unittest.TextTestRunner(verbosity=2).run(suite)
