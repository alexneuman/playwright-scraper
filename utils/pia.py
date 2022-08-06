
from random import random, choice
from time import sleep

import os

regions = os.popen('piactl get regions').read().split('\n')[:-1]

def change_region(region=None, random=False, prefix=None):
    if random:
        region = choice(regions)
    if prefix:
        regions_prefix = [r for r in regions if r.startswith(prefix)] or None
        if regions_prefix is None:
            raise ValueError(f'No region found with prefix: {prefix}')
        region = choice(regions_prefix)
    
    os.system(f'piactl set region {region}')