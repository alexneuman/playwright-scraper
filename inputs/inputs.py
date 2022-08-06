
import csv
import os
from collections import namedtuple
from random import shuffle
from time import sleep

from utils.url_helpers import get_google_url

PREV_OUTPUT_DUPE_COL = 'starting_url'

def set_inputs(inputs: str | list[str] | list[dict] | list[list[str]] = 'inputs.csv', url_col: str = 'url'):
    rows = []
    if isinstance(inputs, str) and inputs.endswith('.csv'):
        with open('inputs.csv', 'r') as f:
            cols = ','.join(next(f).strip().split(','))
            ROW = namedtuple('row', cols)
            reader = csv.reader(f)
            for row in reader:
                starting_url = row[0]
                if 'search' in starting_url or '/posts/' in starting_url or '/jobs/' in starting_url or 'linkedin' not in starting_url:
                    continue
                rows.append(ROW(starting_url=starting_url, google_url=row[1]))
        shuffle(rows)
    else:
        # rows = [get_google_url(i, domain='linkedin/in/') for i in ('conservative podcast', 'libertarian podcast', 'free market podcast', 'politics podcast', 'local government podcast')]
        if isinstance(inputs, list) and any(isinstance(i, list) for i in inputs):
            ROW = namedtuple('row', url_col)
            rows = []
            for i in inputs:
                if isinstance(i, list):
                    for j in i:
                        rows.append(ROW(j))
                else:
                    rows.append(ROW(i))
        
        elif isinstance(inputs, list) and all(isinstance(i, str) for i in inputs): # if inputs is a list of strings, set default key to 'url'
            ROW = namedtuple('row', url_col)
            rows = [ROW(i) for i in inputs]
        elif isinstance(inputs, list) and all(i.get(url_col) for i in inputs): # if inputs is a list of dicts, set default key to 'starting_url'
            ROW = namedtuple('row', inputs[0].keys())
            rows = [ROW(*i.values()) for i in inputs]
        elif isinstance(inputs, str):
            ROW = namedtuple('row', url_col)
            rows = [ROW(inputs)]
    return rows

    
    

previous_urls = set()
try:
    with open('results.csv', 'r') as f:
        reader= csv.DictReader(f)
        for row in reader:
            previous_urls.add(row[PREV_OUTPUT_DUPE_COL])

except:
    print('Prev output not found...')
    sleep(1.5)
    print('Starting without deduping...')
    sleep(1.5)
