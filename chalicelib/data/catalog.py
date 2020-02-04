import os
import sys
import pathlib
import json

try:
    sys.path.append(str(pathlib.Path(os.path.dirname(__file__)) / '../'))
    from base import Path
except ImportError:
    raise

with open('%s/data/wni_data_catalog.json' % Path.lib_dir) as f:
    WNI_DATA_CATALOG = json.load(f)

_prefix_nwp_url = 'http://stock1.wni.co.jp/stock_hdd'
_prefix_nwp_tagid = '400220'
_prefix_nwp_16digits = '0000911000220'

for tagid in WNI_DATA_CATALOG.keys():
    _id = tagid[-3:]
    WNI_DATA_CATALOG[tagid]['url'] = '%s/%s%s/%s%s' % (
        _prefix_nwp_url, _prefix_nwp_tagid, _id, _prefix_nwp_16digits, _id
    )
