#!/usr/bin/env bash

export SA_KEY_FILE=~/.ydb/sa_name.json
export AWS_ACCESS_KEY_ID="dx0_Y_XWiFkIv59RG3J7"
export AWS_SECRET_ACCESS_KEY="KVZ0FwNrzgU4jQqsD3TOdHg0UVhvU3L5jDV1HHHi"
cd ydb-python-sdk/examples/basic_example_custom

python3 __main__.py -e grpcs://ydb.serverless.yandexcloud.net:2135 -d /ru-central1/b1g78gnr21qbtqjat225/etn033rv4tlgsm6elg26 | tee 1.log & python3 __main__.py -e grpcs://ydb.serverless.yandexcloud.net:2135 -d /ru-central1/b1g78gnr21qbtqjat225/etn033rv4tlgsm6elg26 | tee 2.log