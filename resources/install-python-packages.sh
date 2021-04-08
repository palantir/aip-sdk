#!/usr/bin/env bash

set -e

python3 -m pip install detectron2 -f \
  https://dl.fbaipublicfiles.com/detectron2/wheels/cu102/torch1.5/index.html

# the following commands are needed so we get the official torch installation, instead of the one
# that comes pre-built into the Nvidia images. Detectron2 doesn't work with an unofficial torch
# installation unfortunately.
# the install command was picked up from https://pytorch.org/get-started/previous-versions/
python3 -m pip uninstall -y pytorch torchvision
python3 -m pip install torch==1.5.1 torchvision==0.6.1

# 0.1.5 is the latest version but it has some import issue that the FAIR
# people are aware of in this issue: https://github.com/facebookresearch/iopath/issues/5
# in the meantime, using the older version
python3 -m pip uninstall -y iopath
python3 -m pip install -U iopath==0.1.4

python3 -m pip install grpcio==1.33.2
python3 -m pip install grpcio-tools==1.33.2
python3 -m pip install protobuf==3.14.0
python3 -m pip install mypy-protobuf
