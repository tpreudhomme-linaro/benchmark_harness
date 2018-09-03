#!/usr/bin/env bash
set -x

SCRIPT_PATH=$(dirname $(realpath -s $0))

apt install -y python3 python3-pip git build-essential linux-perf unzip lhasa

if [ "$1" == "--erp" ]; then
	apt install -y linux-reference-perf
fi

echo '2' | tee  /proc/sys/kernel/perf_event_paranoid

pip3 install -r "${SCRIPT_PATH}/../requirements.txt"
