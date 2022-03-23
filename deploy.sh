#!/bin/bash

prog_name="textgrid-tools"
cli_path=src/cli.py

mkdir -p ./dist

pipenv run cxfreeze \
  -O \
  --compress \
  --target-dir=dist \
  --bin-includes="libffi.so" \
  --target-name=cli \
  $cli_path

cd dist
zip $prog_name-linux.zip ./ -r
cd ..
echo "zipped."