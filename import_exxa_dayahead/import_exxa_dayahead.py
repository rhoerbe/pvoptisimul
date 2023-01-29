import json
import pandas as pd
from datetime import datetime
from pathlib import Path


basepath = Path(r"data")
INPATH = Path(basepath) / "exxa_dayahead.csv"
OUTPATH = Path(basepath) / "exxa_dayahead.json"

def main():
    df = pd.read_csv(INPATH)
    df['Timestamp_local_tz'] = df['Timestamp_local_tz'].strftime('%H:%M')
    df['datetime_utc'] = pd.to_datetime(df['Timestamp_local_tz'], format='%d.%m.%Y %H:%M', utc=True)
    df['timestamp_utc'] = (df['datetime_utc'].astype(int) / 10 ** 9).astype(int)
    df = pd.to_json(OUTPATH)
    # reporting -----------
    first_idx = df.index[0]
    last_idx = df.index[-1]

    df.loc[last_idx, 'timestamp_utc']
    start = datetime.fromtimestamp(df.loc[first_idx, 'timestamp_utc']).isoformat()
    end = datetime.fromtimestamp(df.loc[last_idx, 'timestamp_utc']).isoformat()
    count = df['timestamps_utc'].count()
    print(F"start: {start}, end: {end}; {count} samples read")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

