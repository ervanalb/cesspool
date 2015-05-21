#!/bin/bash -e

export SHMOOZE_SETTINGS=$PWD/settings.json
export PYTHONPATH=$PWD

trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

python -m shmooze.wsgi &
python -m cesspool.pool

