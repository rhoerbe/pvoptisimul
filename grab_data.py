import json
import os
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta


ACCESSTOKEN = os.environ['ACCESSTOKEN']
BASE_URL = os.environ['BASE_URL']
# Define the URL and authorize header for the Joulie API
# The URL is the copy from the ajax request in the Web interface without URL parameters
url = BASE_URL + "?start={}&end={}&resolution=5m"
headers = {
    'Authorization': ACCESSTOKEN
}

# Define the start and end date of the year
start_dt = datetime(2022, 1, 1)
end_dt = datetime(2022, 12, 31)

# Define the time range in unix time format
start_unix = int(start_dt.timestamp())
end_unix = int(end_dt.timestamp())

# Define the time range in monthly increments
time_range = []
current_start_dt = start_dt
while current_start_dt < end_dt:
    next_start_dt = current_start_dt + relativedelta(months=+1)
    time_range.append((int(current_start_dt.timestamp()), int(next_start_dt.timestamp())))
    current_start_dt = next_start_dt

# Initialize an empty list to store the data
merged_data = {}
first_start = last_end = None


# Send GET request and add result to merged_data
for start, end in time_range:
    response = requests.get(url.format(start, end), headers=headers)
    if response.ok:
        r = response.json()['response']
        number_of_samples = len(r['timestamps'])
        print(f"{number_of_samples} samples in {datetime.fromtimestamp(start).isoformat()} - {datetime.fromtimestamp(end).isoformat()}")
        if not merged_data:
            merged_data = r # copy initial object
            first_start = r['start']
            resolution = r['resolution']
        else:
            # merged_data['timestamps'] += r['timestamps']  # useless if querying multiple months in a row
            merged_data['missing_data'] += r['missing_data']
            merged_data['values'] += r['values']
            merged_data['values_2_ex'] += r['values_2_ex']
            try:
                merged_data['auto_consumption'] += r['auto_consumption']
            except KeyError:
                merged_data['auto_consumption'] += r['values_pvo_auto']
            merged_data['resolution'] = r['resolution']
    else:
        print(f"GET {response.url} returned HTTP {response.status_code}")
        raise ValueError(response.text)
    last_end = end
# add timestamp series (joulie timestamps are pretty useless)
assert resolution == '5m'
samples = len(merged_data['values'])
timestamps_utc = list(range(start_unix, end_unix, 300))[0:samples] # resolution 5m

# Export the data as json
with open('data/grab.json', 'w') as f:
    final_export = {
        "status": "ok",
        "response": {
            'timestamps_utc': timestamps_utc,
            'missing_data': merged_data['missing_data'],
            'values': merged_data['values'],
            'values_2_ex': merged_data['values_2_ex'],
            'auto_consumption': merged_data['auto_consumption'],
            'resolution': resolution,
            'start': first_start,
            'end': last_end,
        }
    }
    json.dump(final_export, f)
