import json
import pandas as pd
import pytz
from datetime import datetime
from pathlib import Path


basepath = Path(r"data")
INPATH = Path(basepath) / "timeseries.json"
OUTPATH = Path(basepath) / "timeseries.xlsx"

def main():
    with open(INPATH) as fh:
        api_result = json.load(fh)
        start_epoc = api_result['response']['start'] / 1000
        timestamp_offset = int(api_result['response']['timestamps'][0])
        subset = make_subset_with_pretty_names(api_result)
        df = pd.DataFrame.from_dict(subset)
        df = compute_timestamp(df, start_epoc, timestamp_offset)
        df = round_and_scale_kWh(df)
        aggregate_and_write_excel(df)
        # reporting -----------
        start = datetime.fromtimestamp(start_epoc).isoformat()
        end = datetime.fromtimestamp(api_result['response']['end'] / 1000).isoformat()
        resolution = api_result['response']['resolution']
        count = df['timestamp_utc'].count()
        missing = df['missing_data'].count()
        print(F"start: {start}, end: {end}")
        print(F"resolution: {resolution}")
        print(F"{count} samples read, {count-missing} missing values.")


def make_subset_with_pretty_names(api_result: dict) -> dict:
    subset = dict()
    subset['timestamp_utc'] = api_result['response']['timestamps']
    subset['missing_data'] = api_result['response']['missing_data']
    subset['PV_Produktion'] = api_result['response']['values']
    subset['Netzbezug'] = api_result['response']['values_2_ex']
    try:
        subset['Eigenverbrauch'] = api_result['response']['values_pvo_auto']
    except KeyError:
        subset['Eigenverbrauch'] = api_result['response']['auto_consumption']
    return subset


def compute_timestamp(df: pd.DataFrame, start: int, timestamp_offset: int) -> pd.DataFrame:
    df['timestamp_utc'].astype(int)
    df.loc[:, 'timestamp_utc'] -= timestamp_offset  # deduct joulie counter offset
    df.loc[:, 'timestamp_utc'] *= 300  # set interval steps to 5 min
    df.loc[:, 'timestamp_utc'] += start # compute unix_epoc
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], unit='s')
    return df


def round_and_scale_kWh(df):
    df['Netzbezug'] = df['Netzbezug'].round()
    df['Netzbezug'] /= 1000
    df['PV_Produktion'] = df['PV_Produktion'].round()
    df['PV_Produktion'] /= 1000
    df['Eigenverbrauch'] = df['Eigenverbrauch'].round()
    df['Eigenverbrauch'] /= 1000
    return df


def aggregate_and_write_excel(df):
    df = df.set_index('timestamp_utc').resample('15T').sum()   # Aggregate to 15-minute intervals
    df['time'] = df.index.strftime('%H:%M')
    df['year_loc'] = (df.index + pd.DateOffset(hours=1)).strftime('%Y')   # fix time zone
    df['month_loc'] = (df.index + pd.DateOffset(hours=1)).strftime('%m').astype(int)   # fix time zone
    lookup_dict = {1:'W', 2:'W', 3:'W', 4:'Ü',5:'Ü', 6:'S',7:'S', 8:'S',9:'Ü', 10:'Ü', 11: 'W', 12: 'W'}
    df['season'] = df['month_loc'].map(lookup_dict)
    df.to_excel(OUTPATH, index=True)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

