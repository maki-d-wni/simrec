import os
import sys
import pathlib
from jinja2 import Environment, FileSystemLoader

try:
    sys.path.append(str(pathlib.Path(os.path.dirname(__file__)) / '../'))
    from base import Path
    from data.nwp.msm import MSM
except ImportError:
    raise

_templates_dir = '%s/ui/templates' % Path.lib_dir
env = Environment(loader=FileSystemLoader(str(_templates_dir)))
msm = MSM()


def get_base(nwp):
    template = env.get_template('home.html')

    if nwp == 'MSM':
        params = {}
        level = {}
        for key in msm:
            params[key] = msm[key]['parameter']
            level[key] = msm[key]['level']
    else:
        params = None
        level = None

    html = template.render(
        {
            'params': params,
            'level': level
        }
    )

    return html


def get_query_result(nwp, similar_date_url, cnd_date_url, rdsrp_url):
    template = env.get_template('home.html')

    if nwp == 'MSM':
        params = {}
        level = {}
        for key in msm:
            params[key] = msm[key]['parameter']
            level[key] = msm[key]['level']
    else:
        params = None
        level = None

    html = template.render(
        {
            'params': params,
            'level': level,
            'similar_date_url': similar_date_url,
            'cnd_date_img_urls': cnd_date_url,
            'rdsrp_urls': rdsrp_url
        }
    )

    return html
