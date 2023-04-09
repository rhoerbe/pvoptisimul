import json
import pandas as pd
from datetime import datetime
from pathlib import Path


basepath = Path(r"data")
INPATH_TIKO = Path(basepath) / "grab_tiko.json"
OUTPATH = Path(basepath) / "timeseries.xlsx"

def main():
    with open(INPATH_TIKO) as fh:
        tiko_result = json.load(fh)
        start_epoc = tiko_result['response']['start'] / 1000
        subset = make_subset_with_pretty_names(tiko_result)
        df = pd.DataFrame.from_dict(subset)
        df = compute_timestamp(df, start_epoc, tiko_result)
        df = round_and_scale_kWh(df)
        aggregate_enhance_and_write_excel(df)
        # reporting -----------
        start = datetime.fromtimestamp(start_epoc).isoformat()
        end = datetime.fromtimestamp(tiko_result['response']['end']).isoformat()
        resolution = tiko_result['response']['resolution']
        count = df['timestamps_utc'].count()
        missing = df['missing_data'].count()
        print(F"start: {start}, end: {end}")
        print(F"resolution: {resolution}")
        print(F"{count} samples read, {count-missing} missing values.")


def make_subset_with_pretty_names(api_result: dict) -> dict:
    subset = dict()
    try:
        subset['timestamps_utc'] = api_result['response']['timestamps_utc']
    except KeyError:
        pass
    subset['missing_data'] = api_result['response']['missing_data']
    subset['PV_Produktion'] = api_result['response']['values']
    subset['Netzbezug'] = api_result['response']['values_2_ex']
    try:
        subset['Eigenverbrauch'] = api_result['response']['values_pvo_auto']
    except KeyError:
        subset['Eigenverbrauch'] = api_result['response']['auto_consumption']
    return subset


def compute_timestamp(df: pd.DataFrame, start: int, api_result: dict) -> pd.DataFrame:
    if 'timestamps_utc' in df.columns:
        # timestamps already set by extract_tiko_data.py
        pass
    else:
        # timestamps as returned by the API with weird counter offset -> correct it
        df['timestamps_utc'] = api_result['response']['timestamps']
        timestamp_offset = int(api_result['response']['timestamps'][0])
        df['timestamps_utc'].astype(int)
        df.loc[:, 'timestamps_utc'] -= timestamp_offset  # deduct joulie counter offset
        df.loc[:, 'timestamps_utc'] *= 300  # set interval steps to 5 min
        df.loc[:, 'timestamps_utc'] += start  # compute unix_epoc
    df['timestamps_utc'] = pd.to_datetime(df['timestamps_utc'], unit='s')
    return df


def round_and_scale_kWh(df) -> pd.DataFrame:
    #df['Netzbezug'] /= 1000
    #df['PV_Produktion'] /= 1000
    #df['Eigenverbrauch'] /= 1000
    return df


def aggregate_enhance_and_write_excel(df):
    df = df.set_index('timestamps_utc')
    df = df.drop('missing_data', axis=1)
    #df = df.resample('15T').sum()   # Aggregate to 15-minute intervals
    #df['Diff_Prod_Bezug'] = df['PV_Produktion'] - df['Netzbezug']
    # to make data comparable between months, the time zone is considered, but daylight saving time is ignored
    df['time_loc'] = (df.index  + pd.DateOffset(hours=1)).strftime('%H:%M')
    df['year_loc'] = (df.index + pd.DateOffset(hours=1)).strftime('%Y')
    df['month_loc'] = (df.index + pd.DateOffset(hours=1)).strftime('%m').astype(int)
    df['day_loc'] = (df.index + pd.DateOffset(hours=1)).strftime('%d').astype(int)
    df['hour_loc'] = (df.index + pd.DateOffset(hours=1)).strftime('%H')
    df['min_loc'] = (df.index + pd.DateOffset(hours=1)).strftime('%M')
    #lookup_dict = {1:'W', 2:'W', 3:'W', 4:'Ü', 5:'S', 6:'S', 7:'S', 8:'S', 9:'Ü', 10:'Ü', 11: 'W', 12: 'W'}
    #df['season'] = df['month_loc'].map(lookup_dict)
    #df['Eigennutzung'] = df['Eigenverbrauch'] / df['PV_Produktion']
    df.to_excel(OUTPATH, index=True)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

