import json
import os
import requests
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pathlib import Path


DEBUG = False

class Config:
    def __init__(self):
        try:
            self.ACCESSTOKEN = os.environ['ACCESSTOKEN']
            self.BASE_URL = os.environ['BASE_URL']
            self.START_DATE = os.environ['START_DATE']
            self.END_DATE = os.environ['END_DATE']
        except KeyError:
            print("Required environment variables: ACCESSTOKEN, BASE_URL, END_DATE, START_DATE", file=sys.stderr)
            sys.exit(1)
        # Define the URL and authorize header for the Joulie API
        # The URL is the copy from the ajax request in the Web interface without URL parameters
        self.url = self.BASE_URL + "?start={}&end={}&resolution=5m"
        self.headers = {
            'Authorization': self.ACCESSTOKEN
        }
        self.OUTPUTFILE = Path('data/grab_tiko.json')
        self.OUTPUTFILE.parent.mkdir(parents=False, exist_ok=True)


class Timeranges:
    def __init__(self, conf: Config):
        # Define the start and end date of the year
        self.start_dt = datetime.strptime(conf.START_DATE, '%Y-%m-%d')
        self.end_dt = datetime.strptime(conf.END_DATE, '%Y-%m-%d')

        # Define the time range in unix time format
        self.start_unix = int(self.start_dt.timestamp())
        self.end_unix = int(self.end_dt.timestamp())

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
            (start_ms, end_ms) = (start*1000, end*1000)
            url_formatted = conf.url.format(start_ms, end_ms)
            response = requests.get(url_formatted, headers=conf.headers)
            if response.ok:
                r = response.json()['response']
                number_of_samples = len(r['timestamps'])
                print(f"{number_of_samples} samples in {datetime.fromtimestamp(start).isoformat()}/{start} - " +
                      f"{datetime.fromtimestamp(end).isoformat()}/{end}")
                if DEBUG:
                    fp = Path('data') / datetime.fromtimestamp(start).strftime('%Y%m%d.json')
                    with open(fp, 'w') as f:
                        json.dump(r, f)
                    print(f"GET {url_formatted}\n  response: start={r['start']}, end={r['end']}")
                if not self.merged_data:
                    self.merged_data = r # copy initial object
                    self.first_start = r['start']
                    self.resolution = r['resolution']
                else:
                    # merged_data['timestamps'] += r['timestamps']  # useless if querying multiple months in a row
                    self.merged_data['missing_data'] += r['missing_data']
                    self.merged_data['values'] += r['values']
                    self.merged_data['values_2_ex'] += r['values_2_ex']
                    try:
                        self.merged_data['auto_consumption'] += r['auto_consumption']
                    except KeyError:
                        self.merged_data['auto_consumption'] += r['values_pvo_auto']
                    self.merged_data['resolution'] = r['resolution']
            else:
                print(f"GET {response.url} returned HTTP {response.status_code}")
                raise ValueError(response.text)
            self.last_end = end
        # add timestamp series (tiko timestamps have some strange offset)
        assert self.resolution == '5m'
        samples = len(self.merged_data['values'])
        self.timestamps_utc = list(range(tr.start_unix, tr.end_unix, 300))[0:samples] # resolution 5m

    def write_data(self, conf: Config):
        # Export the data as json
        with open(conf.OUTPUTFILE, 'w') as f:
            final_export = {
                "status": "ok",
                "response": {
                    'timestamps_utc': self.timestamps_utc,
                    'missing_data': self.merged_data['missing_data'],
                    'values': self.merged_data['values'],
                    'values_2_ex': self.merged_data['values_2_ex'],
                    'auto_consumption': self.merged_data['auto_consumption'],
                    'resolution': self.resolution,
                    'start': self.first_start,
                    'end': self.last_end,
                }
            }
            json.dump(final_export, f)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    config = Config()
    timeranges = Timeranges(config)
    api_handler = ApiHandler()
    api_handler.pull(config, timeranges)
    api_handler.write_data(config)

