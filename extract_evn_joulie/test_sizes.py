import json
from pathlib import Path


basepath = Path(r"data")
INPATH_TIKO = Path(basepath) / "grab_tiko.json"

j = None
with open(INPATH_TIKO) as f:
    j = json.load(f)

try:
    for key in j['response']:
        if type(j['response'][key]) == list:
            print(key + ' ' + str(len((j['response'][key]))))
except KeyError:
    for key in j:
        if type(j[key]) == list:
            print(key + ' ' + str(len((j[key]))))

