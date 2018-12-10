import os
import re
import glob
import pickle
import pygrib
import numpy as np
import plotly.offline as offline
import plotly.graph_objs as go

from .db import MSMDB

MSM = MSMDB()


def msm_similarity(grbs, ft, collection, params, level):
    base = MSM.read_values(
        collection=collection,
        params=params,
        level=level
    )

    date = MSM.read_date()

    cnd = {}
    for i, p in enumerate(params):
        grb = grbs.select(forecastTime=int(ft), parameterName=p)[0]
        x = grb.values.reshape(1, -1)

        diff = np.sqrt((base[i] - x) ** 2).sum(axis=1)
        args = np.argsort(diff)
        cnd[p] = date[args]

    return cnd


def extract_similar_date(cutoff, grbs, ft, collection, params, level,
                         save_path):
    cnd = msm_similarity(grbs, ft, collection, params, level)

    hist = {}

    if collection == 'surface':
        for p in params:
            hist[p] = cnd[p][:cutoff]
    else:
        for p in params:
            for l in level:
                hist['%s_%s' % (p, l)] = cnd[p][:cutoff]

    pattern = re.compile('(\d{4})(\d{2})(\d{2})')
    for key in hist:
        hist[key] = ['/'.join(pattern.findall(d)[0]) for d in hist[key]]

    pickle.dump(
        hist, open(save_path, 'wb')
    )

    return hist


def read_similar_date(path):
    hist = pickle.load(open(path, 'rb'))
    return hist


def make_similar_date_histogram(hist, save_path):
    data = [
        go.Histogram(
            histfunc='count',
            x=hist[k],
            name=k
        )
        for k in hist
    ]

    layout = go.Layout(barmode='stack')

    offline.plot(
        dict(data=data, layout=layout),
        filename=save_path,
        auto_open=False
    )


def make_tmp_filename(cutoff, params, level, exts):
    tmp_file = '%s' % cutoff
    for key in params:
        for p in params[key]:
            tmp_file += p[0]

    for key in level:
        for l in level[key]:
            tmp_file += str(l)[:2]

    tmp_file = '%s.%s' % (tmp_file, exts)
    print(tmp_file)

    return tmp_file


def main():
    from SimRec import WEB_PATH

    date = '20170210'
    ft = 12

    params = MSMDB.params
    level = MSMDB.level

    bt = '03'
    vt = '00'



    run = False
    if run:
        if int(vt) <= 15:
            vt_dir = 'vt0015'
        elif (15 < int(vt)) and (int(vt) <= 33):
            vt_dir = 'vt1633'
        else:
            vt_dir = None

        cutoff = 5
        tmp_file = make_tmp_filename(cutoff, params, level, 'pkl')
        tmp_file = WEB_PATH + '/tmp/similar_date/%s/%s' % (date, tmp_file)

        if os.path.exists(tmp_file):
            hist = read_similar_date(tmp_file)
            save_path = WEB_PATH + '/templates/similar_date/%s.html' % date
            make_similar_date_histogram(hist, save_path)

        else:
            os.makedirs(WEB_PATH + '/tmp/similar_date/%s' % date, exist_ok=True)

            hist = {}
            for layer in ['surface', 'upper']:
                params = MSMDB.params[layer][:1]
                level = MSMDB.level[layer][:2]

                f = glob.glob(
                    '/home/ai-corner/part1/MSM/%s/bt%s/%s/%s*' % (layer, bt, vt_dir, date)
                )[0]

                grbs = pygrib.open(f)

                hist_layer = extract_similar_date(
                    cutoff=5,
                    grbs=grbs,
                    ft=ft,
                    collection=layer,
                    params=params,
                    level=level,
                    save_path=tmp_file
                )

                for key in hist_layer:
                    hist[key] = hist_layer[key]
            print(hist)

            save_path = WEB_PATH + '/templates/similar_date/%s.html' % date
            make_similar_date_histogram(hist, save_path)


if __name__ == '__main__':
    main()
