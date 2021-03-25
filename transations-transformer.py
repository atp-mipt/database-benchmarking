import clj

with open("txns", "r") as txns_file:
    transactions = clj.loads(txns_file.read())
    for transaction in transactions:
        for command in transaction['value']:
            pass
