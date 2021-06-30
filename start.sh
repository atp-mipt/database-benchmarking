#!/usr/bin/env bash

export SA_KEY_FILE=~/.ydb/sa_name.json
export AWS_ACCESS_KEY_ID=""
export AWS_SECRET_ACCESS_KEY=""
cd ydb-python-sdk/examples/basic_example_custom

python3 __main__.py -e grpcs://ydb.serverless.yandexcloud.net:2135 -d /ru-central1/b1g78gnr21qbtqjat225/etn033rv4tlgsm6elg26 -pt results/txns-short -n 2 -id 1 -m 0
python3 __main__.py -e grpcs://ydb.serverless.yandexcloud.net:2135 -d /ru-central1/b1g78gnr21qbtqjat225/etn033rv4tlgsm6elg26 -pt results/txns-short -n 2 -id 0 -m 1
#& python3 __main__.py -e grpcs://ydb.serverless.yandexcloud.net:2135 -d /ru-central1/b1g78gnr21qbtqjat225/etn033rv4tlgsm6elg26 -n 2 -id 1 -pt results/txns-short -m 1

#python3 __main__.py -e grpcs://ydb.serverless.yandexcloud.net:2135 -d /ru-central1/b1g78gnr21qbtqjat225/etn033rv4tlgsm6elg26 | tee 1.log & python3 __main__.py -e grpcs://ydb.serverless.yandexcloud.net:2135 -d /ru-central1/b1g78gnr21qbtqjat225/etn033rv4tlgsm6elg26 | tee 2.log