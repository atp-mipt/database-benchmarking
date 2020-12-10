from io import StringIO
import clj

with open("txns", "r") as txns_file:
    objs = clj.loads(txns_file.read())
    for obj in objs:
        print(obj)