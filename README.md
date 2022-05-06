# textgrid-tools

[![PyPI](https://img.shields.io/pypi/v/textgrid-tools.svg)](https://pypi.python.org/pypi/textgrid-tools)
[![PyPI](https://img.shields.io/pypi/pyversions/textgrid-tools.svg)](https://pypi.python.org/pypi/textgrid-tools)
[![MIT](https://img.shields.io/github/license/stefantaubert/textgrid-ipa.svg)](https://github.com/stefantaubert/textgrid-ipa/blob/main/LICENSE)

CLI to modify TextGrids and their corresponding audio files.

## Features

- grids
  - merge grids together
  - export vocabulary out of multiple grid files
  - plot durations
  - exports marks of a tier to a file
- grid
  - convert text files to grid files
  - synchronize grid minTime and maxTime according to the corresponding audio file
  - split a grid file on intervals into multiple grid files (incl. audio files)
  - print statistics
- tiers
  - apply mapping table to marks
  - transcribe words of tiers using a pronunciation dictionary
  - remove tiers
  - remove symbols from tiers
  - mark silence intervals
- tier
  - rename tier
  - clone tier
  - copy tier from one grid to another
  - map tier to other tiers
  - move tier to another position
  - export content of tier to a txt file
  - import content of tier from a txt file
- intervals
  - join intervals between pauses
  - join intervals by boundaries of a tier
  - join intervals by a duration
  - join intervals containing specific marks
  - join intervals containing specific symbols
  - align boundaries of tiers according to a reference tier
  - split intervals
  - remove intervals
  - plot durations

## Roadmap

- Performance improvement
- Adding more tests

## Installation

```sh
pip install textgrid-tools --user
```

## Usage

```sh
textgrid-tools-cli
```

## Dependencies

- scipy
- numpy
- tqdm
- TextGrid >= 1.5
- pandas
- matplotlib
- ordered-set >=4.1.0
- pronunciation-dictionary >=0.0.4

## Troubleshooting

If recordings/audio files are not in `.wav` format they need to be converted:

```sh
sudo apt-get install ffmpeg -y
# e.g., mp3 to wav conversion
ffmpeg -i *.mp3 -acodec pcm_s16le -ar 22050 *.wav
```

## Citation

If you want to cite this repo, you can use this BibTeX-entry:

```bibtex
@misc{tstgt22,
  author = {Taubert, Stefan},
  title = {textgrid-tools},
  year = {2022},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/stefantaubert/textgrid-ipa}}
}
```
