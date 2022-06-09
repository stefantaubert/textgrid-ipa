# textgrid-tools

[![PyPI](https://img.shields.io/pypi/v/textgrid-tools.svg)](https://pypi.python.org/pypi/textgrid-tools)
![PyPI](https://img.shields.io/pypi/pyversions/textgrid-tools.svg)
[![MIT](https://img.shields.io/github/license/stefantaubert/textgrid-ipa.svg)](https://github.com/stefantaubert/textgrid-ipa/blob/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/wheel/textgrid-tools.svg)](https://pypi.python.org/pypi/textgrid-tools/#files)
![PyPI](https://img.shields.io/pypi/implementation/textgrid-tools.svg)
[![PyPI](https://img.shields.io/github/commits-since/stefantaubert/textgrid-ipa/latest/main.svg)](https://github.com/stefantaubert/textgrid-ipa/compare/v0.0.4...main)

Command-line interface (CLI) to modify TextGrids and their corresponding audio files.

## Features

- grids
  - `merge`: merge grids together
  - `export-vocabulary`: export vocabulary out of multiple grid files
  - `plot-durations`: plot durations
  - `export-marks`: exports marks of a tier to a file
- grid
  - `create`: convert text files to grid files
  - `sync`: synchronize grid minTime and maxTime according to the corresponding audio file
  - `split`: split a grid file on intervals into multiple grid files (incl. audio files)
  - `print-stats`: print statistics
- tiers
  - `apply-mapping`: apply mapping table to marks
  - `transcribe`: transcribe words of tiers using a pronunciation dictionary
  - `remove`: remove tiers
  - `remove-symbols`: remove symbols from tiers
  - `mark-silence`: mark silence intervals
- tier
  - `rename`: rename tier
  - `clone`: clone tier
  - `map`: map tier to other tiers
  - `move`: move tier to another position
  - `export`: export content of tier to a txt file
  - `import`: import content of tier from a txt file
- intervals
  - `join-between-pauses`: join intervals between pauses
  - `join-by-boundary`: join intervals by boundaries of a tier
  - `join-by-duration`: join intervals by a duration
  - `join-marks`: join intervals containing specific marks
  - `join-symbols`: join intervals containing specific symbols
  - `fix-boundaries`: align boundaries of tiers according to a reference tier
  - `split`: split intervals
  - `remove`: remove intervals
  - `plot-durations`: plot durations

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

- `numpy>=1.18.5`
- `scipy>=1.8.0`
- `tqdm>=4.63.0`
- `TextGrid>=1.5`
- `pandas>=1.4.0`
- `ordered_set>=4.1.0`
- `matplotlib>=3.5.0`
- `pronunciation_dictionary>=0.0.4`

## Troubleshooting

If recordings/audio files are not in `.wav` format they need to be converted:

```sh
sudo apt-get install ffmpeg -y
# e.g., mp3 to wav conversion
ffmpeg -i *.mp3 -acodec pcm_s16le -ar 22050 *.wav
```

## License

MIT License

## Acknowledgments

Funded by the Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) – Project-ID 416228727 – CRC 1410

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
