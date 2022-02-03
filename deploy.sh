#!/bin/bash

deactivate
python3.8 -m pipenv run cxfreeze \
  -O \
  --compress \
  --target-dir=dist \
  --bin-includes="libffi.so" \
  --target-name="textgrid-tools" \
  src/cli.py

echo "compiled."
# copy to local apps folder
mkdir -p /home/mi/apps/textgrid-tools
cp dist/* -r /home/mi/apps/textgrid-tools
echo "deployed."

if [ $1 ]
then
  cd dist
  zip textgrid-tools-linux.zip ./ -r
  cd ..
  echo "zipped."
fi
