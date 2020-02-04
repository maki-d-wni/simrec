import os
import sys
import pathlib
import json

try:
    sys.path.append(str(pathlib.Path(os.path.dirname(__file__)) / '../../'))
    from base import Path
except ImportError:
    raise


class NWPMeta(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        with open('%s/data/nwp/nwpmeta.json' % Path.lib_dir) as f:
            for k, v in json.load(f).items():
                self[k] = v


class MSM(NWPMeta):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for k, v in self['MSM'].items():
            self[k] = v

        del self['MSM']
