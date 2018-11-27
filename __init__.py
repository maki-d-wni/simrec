import os
import re
import glob
import pygrib
import numpy as np
from flask import Flask, render_template, request
from .db import MSMDB
from .recommend import read_similar_date, extract_similar_date, make_tmp_filename, make_similar_date_histogram

WEB_PATH = '/home/maki-d/PycharmProjects/SimRec/web'


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/', methods=["GET", "POST"])
    def search():
        if request.method == 'POST':
            date = request.form['date']
            p = re.compile('\d+')
            ms = p.findall(date)
            date = ''.join(ms)

            params = {}
            level = {}
            for layer in ['surface', 'upper']:
                param = request.form.getlist('check_%s' % layer)
                param = [p.split('_') for p in param]

                params[layer] = np.unique([p[0] for p in param])
                level[layer] = np.unique([p[1] for p in param])

            bt = '03'
            vt = '00'

            if int(vt) <= 15:
                vt_dir = 'vt0015'
            elif (15 < int(vt)) and (int(vt) <= 33):
                vt_dir = 'vt1633'
            else:
                vt_dir = None

            cutoff = 5
            tmp_file = make_tmp_filename(cutoff, params, level, 'pkl')
            tmp_file = '%s/tmp/similar_date/%s/%s' % (WEB_PATH, date, tmp_file)

            save_path = '%s/templates/similar_date/%s.html' % (WEB_PATH, date)
            if os.path.exists(tmp_file):
                hist = read_similar_date(tmp_file)
                make_similar_date_histogram(hist, save_path)

                sd_path = '/similar_date/%s.html' % date
                return render_template(
                    'home.html',
                    params=MSMDB.params,
                    level=MSMDB.level,
                    sd_path=sd_path
                )
            else:
                os.makedirs('%s/tmp/similar_date/%s' % (WEB_PATH, date), exist_ok=True)

                hist = {}
                for layer in ['surface', 'upper']:
                    f = glob.glob(
                        '/home/ai-corner/part1/MSM/%s/bt%s/%s/%s*' % (layer, bt, vt_dir, date)
                    )[0]

                    grbs = pygrib.open(f)

                    hist_layer = extract_similar_date(
                        cutoff=5,
                        grbs=grbs,
                        ft=12,
                        collection=layer,
                        params=params[layer],
                        level=level[layer],
                        save_path=tmp_file
                    )

                    for key in hist_layer:
                        hist[key] = hist_layer[key]

                make_similar_date_histogram(hist, save_path)

                sd_path = 'similar_date/%s.html' % date
                return render_template(
                    'home.html',
                    params=MSMDB.params,
                    level=MSMDB.level,
                    sd_path=sd_path,
                )
        else:
            return render_template(
                'home.html',
                params=MSMDB.params,
                level=MSMDB.level
            )

    return app
