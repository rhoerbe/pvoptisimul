import json
import os
import requests
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pathlib import Path

""" Assume configuration for 3 K-boxes (meters): (1) grid (2) PV meter and (3) heat pump
    Meters 1 and 2 can be accessed in a single request ("combined devices"), meter 3 is separate
    URL schema 1+2
    https://optimierung.joulie.at/api/v3/properties/<clientid>/combined_devices/history/?start=<startepoch>&end=endepoch&resolution=5m
    URL schema 3
    https://optimierung.joulie.at/api/v3/properties/<clientid>/devices/<deviceid>/history/?start=<startepoch>&end=endepoch&resolution=5m
"""

DEBUG = True

class Config:
    def __init__(self):
        try:
            self.ACCESSTOKEN = os.environ['ACCESSTOKEN']
            self.BASE_URL = os.environ['BASE_URL']   # baseurl includes API path including the clientID
            self.DEVICEID = os.environ['DEVICEID']
            self.START_DATE = os.environ['START_DATE']
            self.END_DATE = os.environ['END_DATE']
        except KeyError:
            print("Required environment variables: ACCESSTOKEN, BASE_URL, DEVICEID, END_DATE, START_DATE", file=sys.stderr)
            sys.exit(1)
        # Define the URLs and authorize header for the Joulie API
        # The URLs are derived from the ajax requests in the Web interface
        self.url12 = self.BASE_URL + "/combined_devices/history/?start={}&end={}&resolution=5m"
        self.url3 = self.BASE_URL + "/devices/" + self.DEVICEID + "/history/?start={}&end={}&resolution=5m"
        self.headers = {
            'Authorization': self.ACCESSTOKEN
        }
        self.OUTPUTFILE = Path('data/grab_tiko.json')
        self.OUTPUTFILE.parent.mkdir(parents=False, exist_ok=True)


class Timeranges:
    def __init__(self, conf: Config):
        # Define the start and end date of the year
        self.start_dt = datetime.fromisoformat(conf.START_DATE)
        self.end_dt = datetime.fromisoformat(conf.END_DATE)
        self.start_unix = int(self.start_dt.timestamp())
        print(f"reading from env: startdate {conf.START_DATE}/{self.start_unix}")

        # Define the time range in monthly increments
        self.time_range = []
        current_start_dt = self.start_dt
        while current_start_dt < self.end_dt:
            next_start_dt = current_start_dt + relativedelta(months=+1)
            self.time_range.append((int(current_start_dt.timestamp()), int(next_start_dt.timestamp())))
            current_start_dt = next_start_dt


class ApiHandler():
    def __init__(self):
        self.merged_data = {}
        self.first_start = self.last_end = None
        self.resolution = None
        self.timestamps_utc = None

    def pull(self, conf: Config, tr: Timeranges) -> dict:
        # Send GET request and add result to merged_data
        for start, end in tr.time_range:
            (start_ms, end_ms) = (start*1000, end*1000-1)
            url12_formatted = conf.url12.format(start_ms, end_ms)
            url3_formatted = conf.url3.format(start_ms, end_ms)
            response12 = requests.get(url12_formatted, headers=conf.headers)
            if not response12.ok:
                print(f"GET {response12.url} returned HTTP {response12.status_code}")
                raise ValueError(response12.text)
            response3 = requests.get(url3_formatted, headers=conf.headers)
            if not response3.ok:
                print(f"GET {response3.url} returned HTTP {response3.status_code}")
                raise ValueError(response3.text)
            r = response12.json()['response']
            r3 = response3.json()['response']
            number_of_samples = len(r['timestamps'])
            print(f"{number_of_samples} samples in {datetime.fromtimestamp(start).isoformat()}/{start} - " +
                  f"{datetime.fromtimestamp(end).isoformat()}/{end}")
            if DEBUG:
                fp = Path('data') / datetime.fromtimestamp(start).strftime('%Y%m%d.json')
                with open(fp, 'w') as f:
                    json.dump(r, f)
                print(f"GET {url12_formatted}\n  response: start={r['start']}, end={r['end']}")
            if not self.merged_data:
                self.merged_data = r # copy initial object
                self.merged_data['values_3'] = []
                self.merged_data['values_3'] += r3['values']
                self.merged_data['missing_data3'] = []
                self.merged_data['missing_data3'] += r3['missing_data']
                self.first_start = r['start']
                self.resolution = r['resolution']
            else:
                # merged_data['timestamps'] += r['timestamps']  # useless if querying multiple months in a row
                self.merged_data['missing_data'] += r['missing_data']
                self.merged_data['values'] += r['values']
                self.merged_data['values_2_ex'] += r['values_2_ex']
                self.merged_data['values_3'] = []
                self.merged_data['values_3'] += r3['values']
                self.merged_data['missing_data3'] += r3['missing_data']
                try:
                    self.merged_data['auto_consumption'] += r['auto_consumption']
                except KeyError:
                    self.merged_data['auto_consumption'] += r['values_pvo_auto']
                self.merged_data['resolution'] = r['resolution']
            self.last_end = end
        # add timestamp series because tiko timestamps have some strange offset
        assert self.resolution == '5m'
        samples = len(self.merged_data['values'])
        # make sure that timestamp_utc column has same length as value column
        # (API may return different start/end than requested)
        self.timestamps_utc = list(range(tr.start_unix, tr.start_unix + samples*300, 300))

    def write_data(self, conf: Config):
        # Export the data as json
        with open(conf.OUTPUTFILE, 'w') as f:
            final_export = {
                "status": "ok",
                "response": {
                    'timestamps_utc': self.timestamps_utc,
                    'missing_data': self.merged_data['missing_data'],
                    'values': self.merged_data['values'],
                    'values_2': self.merged_data['values_2_ex'][:len(self.merged_data['values'])],
                    'values_2_ex': self.merged_data['values_2_ex'],
                    'values_3': self.merged_data['values_3'][:len(self.merged_data['values_3'])],
                    'missing_data3': self.merged_data['missing_data3'],
                    'auto_consumption': self.merged_data['auto_consumption'],
                    'resolution': self.resolution,
                    'start': self.first_start,
                    'end': self.last_end,
                }
            }
            json.dump(final_export, f)
            print(f"written {conf.OUTPUTFILE}")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    config = Config()
    timeranges = Timeranges(config)
    api_handler = ApiHandler()
    api_handler.pull(config, timeranges)
    api_handler.write_data(config)

