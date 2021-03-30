#!/bin/bash

python3 -m grpc_tools.protoc -Iproto --python_out proto --mypy_out proto --grpc_python_out proto proto/*.proto
python3 -m lib2to3 -wn proto --output-dir proto

