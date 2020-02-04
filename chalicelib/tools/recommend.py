import os
import sys
import pathlib
import numpy as np
import pandas as pd
import boto3

import plotly.offline as offline
import plotly.graph_objs as go

try:
    sys.path.append(str(pathlib.Path(os.path.dirname(__file__)) / '../'))
    from data.nwp.msm import MSM
except ImportError:
    raise

BUCKET = 'simrec'
s3 = boto3.client('s3')

'''
TABLE = 'simrec'
ddb = boto3.client('dynamodb')

base = ddb.query(
    TableName=TABLE,
    IndexName='base_time-valid_time-index',
    ExpressionAttributeNames={
        '#name0': 'base_time',
        '#name1': 'valid_time',
        '#name2': 'parameter',
        # '#name2': 'level'
    },
    ExpressionAttributeValues={
        ':value0': {'S': '00'},
        ':value1': {'S': '00'},
        ':value2': {'S': 'High cloud cover'},
        # ':value2': {'S': 'surface'}
    },
    KeyConditionExpression='#name0 = :value0 AND #name1 = :value1',
    FilterExpression='#name2 = :value2'
)

print(base['Items'])
for item in base['Items']:
    if item['date']['S'] == '2015-01-02':
        import pickle

        val = item['value']['B']
        print(val)
        val = pickle.loads(val)
        print(val)

        break


class Recommender(object):
    def __init__(self, surface_params, upper_params, bt=0, ft=12, cutoff=5):
        self.surface_params = surface_params
        self.upper_params = upper_params
        self.bt = bt
        self.ft = ft
        self.cutoff = cutoff

    def search(self):
        sim = calc_similarity()

    def calc_similarity(self):
        cnd = {}

        for param in self.surface_params:
            pass

        for param in self.upper_params:
            pass

        for collection in collections:
            s = collection.split(sep='_')
            param = s[0]
            level = s[1]
            bt = s[2]

            if level == 'surface':
                layer = 'surface'
            else:
                layer = 'upper'

            if int(ft) <= 15:
                vt_dir = 'vt0015'
            elif (15 < int(ft)) and (int(ft) <= 33):
                vt_dir = 'vt1633'
            else:
                vt_dir = None

            docs = MSM.db[collection].find()
            docs = pd.DataFrame(list(docs))
            date = docs['date'].values

            path = '/home/ai-corner/part1/MSM/%s/%s/%s/%s_%s0000.000' % (layer, bt, vt_dir, search_date, bt[2:])
            files = glob.glob('%s/%s*' % (path, search_date))

            if param == 'Total precipitation':
                if int(ft) == 15 or int(ft) == 33:
                    forecast_time = int(ft) - 1
                else:
                    forecast_time = int(ft)
            else:
                forecast_time = int(ft)

            grb = get_grb(
                layer=layer, files=files, forecast_time=forecast_time, param=param, level=level
            )
            x = grb.values.reshape(1, -1)

            base = np.zeros((len(docs), MSM.shape[layer][0] * MSM.shape[layer][1]))

            for i, v in enumerate(docs['values']):
                base[i] = pickle.loads(v)

            diff = np.sqrt((base - x) ** 2).sum(axis=1)
            args = np.argsort(diff)
            cnd[collection] = date[args]
        return cnd


def extract_similar_date(cutoff, search_date, sf_params, up_params, save_path):
    cnd = msm_similarity(search_date, ft, collections)
    hist = {}

    for key in cnd:
        s = key.split(sep='_')
        if s[1] == 'surface':
            hist[s[0]] = cnd[key][:cutoff]
        else:
            hist['%s_%s' % (s[0], s[1])] = cnd[key][:cutoff]

    pattern = re.compile(r'(\d{4})(\d{2})(\d{2})')
    for key in hist:
        hist[key] = ['/'.join(pattern.findall(d)[0]) for d in hist[key]]

    pickle.dump(
        hist, open(save_path, 'wb')
    )

    return hist


def calc_similarity(search_date, sf_params, up_params, bt, ft, ):
    cnd = {}
    for param in sf_params:
        pass

    for collection in collections:
        s = collection.split(sep='_')
        param = s[0]
        level = s[1]
        bt = s[2]

        if level == 'surface':
            layer = 'surface'
        else:
            layer = 'upper'

        if int(ft) <= 15:
            vt_dir = 'vt0015'
        elif (15 < int(ft)) and (int(ft) <= 33):
            vt_dir = 'vt1633'
        else:
            vt_dir = None

        docs = MSM.db[collection].find()
        docs = pd.DataFrame(list(docs))
        date = docs['date'].values

        path = '/home/ai-corner/part1/MSM/%s/%s/%s/%s_%s0000.000' % (layer, bt, vt_dir, search_date, bt[2:])
        files = glob.glob('%s/%s*' % (path, search_date))

        if param == 'Total precipitation':
            if int(ft) == 15 or int(ft) == 33:
                forecast_time = int(ft) - 1
            else:
                forecast_time = int(ft)
        else:
            forecast_time = int(ft)

        grb = get_grb(
            layer=layer, files=files, forecast_time=forecast_time, param=param, level=level
        )
        x = grb.values.reshape(1, -1)

        base = np.zeros((len(docs), MSM.shape[layer][0] * MSM.shape[layer][1]))

        for i, v in enumerate(docs['values']):
            base[i] = pickle.loads(v)

        diff = np.sqrt((base - x) ** 2).sum(axis=1)
        args = np.argsort(diff)
        cnd[collection] = date[args]
    return cnd
'''


def make_recommend_filename(cutoff, selected_sf_params, selected_up_params, bt, ft, exts):
    tmp_file = ''

    msm = MSM()
    sf_table = pd.DataFrame(index=['surface'], columns=msm['surface']['parameter'])
    up_table = pd.DataFrame(index=msm['upper']['level'], columns=msm['upper']['parameter'])

    for p in selected_sf_params:
        p = p.split('_')
        idx = p[1]
        col = p[0]
        sf_table.loc[idx, col] = 1

    for p in selected_up_params:
        p = p.split('_')
        idx = int(p[1])
        col = p[0]
        up_table.loc[idx, col] = 1

    sf_table = sf_table.fillna(0)
    up_table = up_table.fillna(0)

    for idx in sf_table.index:
        cha = ''
        for bi in sf_table.loc[idx]:
            cha += str(bi)
        tmp_file += str(int(cha, 2)) + 's_'

    for idx in up_table.index:
        cha = ''
        for bi in up_table.loc[idx]:
            cha += str(int(bi))
        tmp_file += str(int(cha, 2)) + 'u%s_' % str(idx)[:2]

    tmp_file = '%sbt%02d_vt%02d_cut%s.%s' % (tmp_file, bt, ft, cutoff, exts)

    return tmp_file


def make_similar_date_histogram(hist, dlim, save_file):
    c = count_date(hist)
    rm_date = c.columns[dlim:]
    for k, v in hist.items():
        for d in rm_date:
            try:
                hist[k].remove(d)
            except ValueError:
                pass

    score_cnd_date = {k: 1 for i, k in enumerate(c.columns[:dlim])}
    print(score_cnd_date)
    print()
    p = {k: 100 for k in hist}
    for k, v in hist.items():
        for d in score_cnd_date:
            if d in v:
                p[k] -= score_cnd_date[d]
    args = np.argsort(list(p.values()))[::-1]
    keys = np.array(list(p.keys()))[args]
    print(p)
    print()
    hist = {key: hist[key] for key in keys}
    print(hist)

    data = [
        go.Histogram(
            histfunc='count',
            x=v,
            name=k,
        )
        for k, v in list(hist.items())
    ]

    layout = go.Layout(barmode='stack')
    offline.plot(
        dict(data=data, layout=layout),
        filename=save_file,
        auto_open=False
    )

    save_name = save_file.split('/')[-1]
    s3.upload_file(
        Filename=save_file,
        Bucket=BUCKET,
        Key='similar_date/hist/%s' % save_name,
        ExtraArgs={
            'ContentType': 'text/html',
            'ACL': 'public-read'
        }
    )


def count_date(hist):
    date_all = []
    for k in hist:
        date_all += hist[k]
    date_all = np.array(date_all)

    count = {}

    for d in np.unique(date_all):
        count[d] = [len(date_all[date_all == d])]
    count = pd.DataFrame(count)
    count.sort_values(0, axis=1, ascending=False, inplace=True)

    return count


def main():
    sf_params = ['Pressure reduced to MSL', 'Pressure', 'u-component of wind', 'v-component of wind', 'Temperature',
                 'Relative humidity', 'Low cloud cover', 'Medium cloud cover', 'High cloud cover', 'Total cloud cover',
                 'Total precipitation', 'Downward short-wave radiation flux']
    up_params = ['u-component of wind_850', 'Temperature_850', 'u-component of wind_700', 'Temperature_700',
                 'u-component of wind_500', 'Temperature_500']

    bt = 0
    ft = 12
    cutoff = 5

    # R = Recommender(sf_params, up_params, bt, ft, cutoff)


if __name__ == '__main__':
    main()
