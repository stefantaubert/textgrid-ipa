# textgrid-tools

[![PyPI](https://img.shields.io/pypi/v/textgrid-tools.svg)](https://pypi.python.org/pypi/textgrid-tools)
![PyPI](https://img.shields.io/pypi/pyversions/textgrid-tools.svg)
[![MIT](https://img.shields.io/github/license/stefantaubert/textgrid-ipa.svg)](https://github.com/stefantaubert/textgrid-ipa/blob/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/wheel/textgrid-tools.svg)](https://pypi.python.org/pypi/textgrid-tools/#files)
![PyPI](https://img.shields.io/pypi/implementation/textgrid-tools.svg)
[![PyPI](https://img.shields.io/github/commits-since/stefantaubert/textgrid-ipa/latest/main.svg)](https://github.com/stefantaubert/textgrid-ipa/compare/v0.0.6...main)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7477341.svg)](https://doi.org/10.5281/zenodo.7477341)

Command-line interface (CLI) to modify TextGrids and their corresponding audio files.

## Features

- grids
  - `merge`: merge grids together
  - `plot-durations`: plot durations
  - `mark-durations`: mark intervals with specific durations with a text
  - `create-dictionary`: create pronunciation dictionary out of a word and a pronunciation tier
  - `plot-stats`: plot statistics
  - `export-vocabulary`: export vocabulary out of multiple grid files
  - `export-marks`: exports marks of a tier to a file
  - `export-durations`: exports durations of grids to a file
  - `export-paths`: exports grid paths to a file
  - `export-audio-paths`: exports audio paths to a file
  - `import-paths`: import grids from paths written in a file
  - `import-audio-paths`: import audio files from paths written in a file
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
  - `join`: join adjacent intervals
  - `join-between-marks`: join intervals between marks
  - `join-by-boundary`: join intervals by boundaries of a tier
  - `join-by-duration`: join intervals by a duration
  - `join-marks`: join intervals containing specific marks
  - `join-symbols`: join intervals containing specific symbols
  - `join-template`: join intervals according to a template
  - `split`: split intervals
  - `fix-boundaries`: align boundaries of tiers according to a reference tier
  - `remove`: remove intervals
  - `plot-durations`: plot durations
  - `join-between-pauses`: join intervals between pauses (LEGACY, please use join-between-marks)
  - `replace-text`: replace text using regex pattern

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
- `pronunciation_dictionary>=0.0.5`

## Contributing

If you notice an error, please don't hesitate to open an issue.

### Development setup

```sh
# update
sudo apt update
# install Python 3.8, 3.9, 3.10 & 3.11 for ensuring that tests can be run
sudo apt install python3-pip \
  python3.8 python3.8-dev python3.8-distutils python3.8-venv \
  python3.9 python3.9-dev python3.9-distutils python3.9-venv \
  python3.10 python3.10-dev python3.10-distutils python3.10-venv \
  python3.11 python3.11-dev python3.11-distutils python3.11-venv
# install pipenv for creation of virtual environments
python3.8 -m pip install pipenv --user

# check out repo
git clone https://github.com/stefantaubert/textgrid-ipa.git
cd textgrid-ipa
# create virtual environment
python3.8 -m pipenv install --dev
```

## Running the tests

```sh
# first install the tool like in "Development setup"
# then, navigate into the directory of the repo (if not already done)
cd textgrid-ipa
# activate environment
python3.8 -m pipenv shell
# run tests
tox
```

Final lines of test result output:

```log
  py38: commands succeeded
  py39: commands succeeded
  py310: commands succeeded
  py311: commands succeeded
  congratulations :)
```

## Troubleshooting

If recordings/audio files are not in `.wav` format they need to be converted, e.g.:

```sh
sudo apt install ffmpeg -y
# e.g., mp3 to wav conversion
ffmpeg -i *.mp3 -acodec pcm_s16le -ar 22050 *.wav
```

## License

MIT License

## Acknowledgments

Funded by the Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) – Project-ID 416228727 – CRC 1410

## Citation

If you want to cite this repo, you can use this BibTeX-entry generated by GitHub (see *About => Cite this repository*).
