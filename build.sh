#!/bin/bash

cargo \
  build \
    --profile release-wasi \
	--target wasm32-wasi
