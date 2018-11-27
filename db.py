import pymongo
import pickle
import numpy as np
import pandas as pd
from collections import OrderedDict


class NwpDB(object):
    client = pymongo.MongoClient()

    def __init__(self, name=None, collections=None):
        self.db = self.client[name]
        self.collections = {}
        for c in collections:
            self.collections[c] = self.db[c]

    def register_one_document(self, document, collection):
        self.collections[collection].insert_one(document)

    def register_documents(self, documents, collection):
        self.collections[collection].insert_many(documents)


class MSMDBBase(NwpDB):
    name = 'MSM'
    collection_names = ['surface', 'upper']
    params = {}
    level = {}
    base_time = {}
    validity_time = {}
    for c in collection_names:
        if c == 'surface':
            params[c] = [
                'Pressure reduced to MSL',
                'u-component of wind',
                'v-component of wind',
                'Temperature',
                'Relative humidity',
                'Low cloud cover',
                'Medium cloud cover',
                'High cloud cover',
                'Total cloud cover',
                'Total precipitation'
            ]
            level[c] = ['surface']
            base_time[c] = ['%02d' % t for t in range(0, 24, 3)]
            validity_time[c] = ['%02d' % t for t in range(39)]

        else:
            params[c] = ['Geopotential height',
                         'Relative humidity',
                         'Temperature',
                         'Vertical velocity [pressure]',
                         'u-component of wind',
                         'v-component of wind']
            level[c] = [
                300,
                400,
                500,
                600,
                700,
                800,
                850,
                900,
                925,
                950,
                975,
                1000
            ]
            base_time[c] = ['%02d' % t for t in range(3, 24, 6)]
            validity_time[c] = ['%02d' % t for t in range(0, 39, 3)]

    def __init__(self):
        super(MSMDBBase, self).__init__(
            name=self.name, collections=self.collection_names
        )


class MSMDB(MSMDBBase):
    def read_documents(self, query, collection='surface'):
        docs = self.db[collection].find(query)

        return docs

    def read_values(self, collection, params, level):
        x_all = []
        for p in params:
            for l in level:
                docs = self.db[collection].find(
                    {'$and': [
                        {'parameter': p},
                        {'level': l}]}
                )

                x_one = []
                for doc in docs:
                    x_one.append(pickle.loads(doc['values']))

                x_all.append(x_one)

        x_all = np.array(x_all)

        return x_all

    def read_date(self):
        docs = self.db['surface'].find(
            {'$and': [
                {'parameter': MSMDB.params['surface'][0]},
                {'base time': '03'},
                {'validity time': '00'}
            ]},
            {'_id': 0, 'date': 1}
        )

        date = pd.DataFrame(list(docs))['date']

        return date.values


def make_msm_docs(params, level, bt, vt, body_path):
    values = {}
    for p in params:
        for l in level:
            if str(l) == 'surface':
                name = p
            else:
                name = '%s_%s' % (p, l)

            path = '%s/%s.pkl' % (body_path, name)
            values['%s_%s' % (p, l)] = pickle.load(open(path, 'rb'))
            print(name)

    docs = [
        OrderedDict({
            'parameter': p,
            'level': l,
            'base time': btime,
            'validity time': vtime,
            'date': i,
            'values': pickle.dumps(v)
        })
        for p in params
        for l in level
        for btime in bt
        for vtime in vt
        for i, v in zip(values['%s_%s' % (p, l)].index, values['%s_%s' % (p, l)].values)
    ]

    return docs


def main():
    import glob
    import pygrib

    layer = "upper"
    if layer == 'surface':
        params = [
            'Pressure reduced to MSL',
            'u-component of wind',
            'v-component of wind',
            'Temperature',
            'Relative humidity',
            'Low cloud cover',
            'Medium cloud cover',
            'High cloud cover',
            'Total cloud cover',
            'Total precipitation'
        ]

        level = ['surface']
        bt = ['03']
        vt = ['00']
        c_names = ['surface']

    else:
        params = ['Geopotential height',
                  'Relative humidity',
                  'Temperature',
                  'Vertical velocity [pressure]',
                  'u-component of wind',
                  'v-component of wind']
        level = [
            300,
            400,
            500,
            600,
            700,
            800,
            850,
            900,
            925,
            950,
            975,
            1000
        ]
        bt = ['03']
        vt = ['00']
        c_names = ['upper']

    msm = MSMDB()
    date = msm.read_date()

    '''
    # kokokara
    cnt = 0
    for p in params:
        docs = (
            make_msm_docs(
                params=[p],
                level=level,
                bt=bt,
                vt=vt,
                body_path='/home/maki-d/PycharmProjects/SimRec/database/FT0',
            )
        )

        msm.register_documents(docs, collection=c_names[0])
        cnt += len(level)
        print('%s/%s' % (cnt, len(params) * len(level)))
    # kokomade main
    '''

    search_date = '20170210'
    ft = 12
    f = glob.glob('/home/ai-corner/part1/MSM/%s/bt03/vt0015/%s*' % (layer, search_date))[0]

    import time
    s = time.time()

    n = 2
    x_all = []
    for n_p, p in enumerate(params[4:6]):
        docs = msm.db[c_names[0]].find(
            {'$and': [
                {'parameter': p},
                {'level': level[0]}]},
            {'_id': 0, 'values': 1}
        )

        x_one = []

        for i, doc in enumerate(docs):
            x_one.append(pickle.loads(doc['values']))

        x_all.append(x_one)

    x_all = np.array(x_all)
    print(x_all.shape)
    print(time.time() - s)

    grbs = pygrib.open(f)
    for i, p in enumerate(params[4:6]):
        print(p)
        grb = grbs.select(forecastTime=ft, parameterName=p)[0]
        x = grb.values.reshape(1, -1)
        diff = np.sqrt((x_all[i] - x) ** 2).sum(axis=1)
        args = np.argsort(diff)
        print(date[args][:100])

    print('all :', time.time() - s)


if __name__ == '__main__':
    main()
