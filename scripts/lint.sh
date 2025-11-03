#!/usr/bin/env bash

set -e
set -x

ty check src
ruff check src
ruff format src --check