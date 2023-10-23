# textgrid-tools

[![PyPI](https://img.shields.io/pypi/v/textgrid-tools.svg)](https://pypi.python.org/pypi/textgrid-tools)
![PyPI](https://img.shields.io/pypi/pyversions/textgrid-tools.svg)
[![MIT](https://img.shields.io/github/license/stefantaubert/textgrid-ipa.svg)](https://github.com/stefantaubert/textgrid-ipa/blob/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/wheel/textgrid-tools.svg)](https://pypi.python.org/pypi/textgrid-tools/#files)
![PyPI](https://img.shields.io/pypi/implementation/textgrid-tools.svg)
[![PyPI](https://img.shields.io/github/commits-since/stefantaubert/textgrid-ipa/latest/main.svg)](https://github.com/stefantaubert/textgrid-ipa/compare/v0.0.8...main)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7986716.svg)](https://doi.org/10.5281/zenodo.7986716)

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
  - `replace-text`: replace text using regex pattern

## Roadmap

- Performance improvement
- Adding more tests

## Installation

```sh
pip install textgrid-tools --user
```

## Usage

```txt
usage: textgrid-tools-cli [-h] [-v] {grids,grid,tiers,tier,intervals} ...

This program provides methods to modify TextGrids (.TextGrid) and their corresponding audio files (.wav).

positional arguments:
  {grids,grid,tiers,tier,intervals}  description
    grids                            execute commands targeted at multiple grids at once
    grid                             execute commands targeted at single grids
    tiers                            execute commands targeted at multiple tiers at once
    tier                             execute commands targeted at single tiers
    intervals                        execute commands targeted at intervals of tiers

optional arguments:
  -h, --help                         show this help message and exit
  -v, --version                      show program's version number and exit
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

## Changelog

- v0.0.9 (unreleased)
  - Fixed:
    - Bugfix `grids import` error raise on file not found
- v0.0.8 (2023-05-30)
  - Fixed:
    - Bugfix `intervals remove` copying on different in/out-locations
    - Bugfix `import-paths` and `import-audio-paths` option `--symlink` is now creating symbolic links instead of hard links
  - Changed:
    - Improved logging in `import-paths` and `import-audio-paths`
    - Improved logging of durations in `grids plot-stats`
  - Added:
    - Added option to get durations from audio files on `grids export-durations`
- v0.0.7 (2023-01-12)
  - Fixed:
    - Bugfix `grids import-paths` and `grids import-audio-paths`
  - Added:
    - Added option `--ignore` to ignore custom marks in `grids export-vocabulary`
    - Added option `--mode` to `intervals replace-text` to replace text on different interval positions
    - Added returning of an exit code
  - Removed:
    - Removed `tiers mark-silence` because `grids mark-durations` should be used
    - Removed `tiers remove-symbols` because `intervals replace-text` should be used
    - Removed `intervals join-between-pauses` because `join-between-marks` should be used
- v0.0.6 (2022-12-23)
  - improved validation for pronunciation dictionary creation
  - bugfix replace text logging
  - added intervals join-template
  - support Python 3.11
  - update pylint config
  - fix description of grid/audio import
- v0.0.5 (2022-11-25)
  - `intervals remove`: added parameter `mode` to better choose which intervals should be removed
  - Added method to plot statistics for all grids together
  - `tiers transcribe`: added option `assign-mark-to-missing` to replace missing transcriptions with a custom mark
  - Bugfix: `mark-durations` empty couldn't be assigned
  - Added `--min-count` to `mark-durations`
  - Improved sorting of phonemes in durations plotting
  - Changed marks exporting format to only contain tier marks
  - Added exporting/importing of audio paths
  - Added durations exporting
  - Added exporting/importing of grid paths
  - Added replacement of marks using regex pattern
  - Added `--dry` option to most methods
  - Make split symbol on split mandatory
  - Upper-cased metavars
- v0.0.4 (2022-06-09)
  - fixed bug while saving TextGrids
  - improved robustness against file system errors
- v0.0.3 (2022-05-31)
  - fixed invalid installation format and clarified dependencies
  - adjusted textgrid serialization equal to praat output
  - added option `include-empty` on vocabulary export
  - set default chunksize to `1`
  - added missing `__init__.py` files
  - improved logging
- v0.0.2 (2022-05-06)
  - improved logging
  - improved reading/saving speed of TextGrids
  - removed n_digits argument
  - added option to define encoding of TextGrids
  - added option to insert interval between grids which should be merged together
  - removed tier copy
  - added parser for tier export
- v0.0.1 (2022-04-29)
  - initial release
