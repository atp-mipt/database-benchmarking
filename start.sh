#!/usr/bin/env bash

export SA_KEY_FILE=~/.ydb/sa_name.json
cd ydb-python-sdk/examples/basic_example_custom
python3 __main__.py -e grpcs://ydb.serverless.yandexcloud.net:2135 -d /ru-central1/b1g78gnr21qbtqjat225/etn033rv4tlgsm6elg26
