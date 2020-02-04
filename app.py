from chalice import Chalice, Response
import os
import sys
import re
import pickle
import datetime
import boto3
import numpy as np

try:
    sys.path.append('./chalicelib')
    from tools.recommend import make_similar_date_histogram, make_recommend_filename, count_date
    from data.catalog import WNI_DATA_CATALOG
    from ui.layout import get_base, get_query_result
except ImportError:
    raise

app = Chalice(app_name='simrec')
app.debug = True

BUCKET = 'simrec'
s3 = boto3.client('s3')


@app.route('/', methods=['GET', 'POST'], content_types=['application/x-www-form-urlencoded', 'application/json'])
def search():
    request = app.current_request
    if request.method == 'POST':
        # forecast_time = request.form['ft']
        # print(request.json_body)

        # bt = request.form['bt']
        # vt = '00'

        body = request.raw_body.decode()
        body = body.split('&')

        body_dict = {}
        for item in body:
            item = item.split('=')
            key = item[0]
            val = item[1].replace('+', ' ')
            val = val.replace('%5B', '[')
            val = val.replace('%5D', ']')

            if key in body_dict.keys():
                body_dict[key].append(val)
            else:
                body_dict[key] = [val]

        date = body_dict['date'][0]
        date = re.sub(r'\D', '-', date)

        bt = body_dict['bt'][0]
        ft = body_dict['ft'][0]

        sf_params = body_dict['check_surface']
        up_params = body_dict['check_upper']

        cutoff = 5
        tmp_name = make_recommend_filename(cutoff, sf_params, up_params, int(bt), int(ft), 'pkl')
        os.makedirs('/tmp/similar_date/cnd/%s' % date, exist_ok=True)
        tmp_file = '/tmp/similar_date/cnd/%s/%s' % (date, tmp_name)

        if os.path.exists(tmp_file):
            hist = pickle.load(open(tmp_file, 'rb'))
        else:
            # tmp
            hist = {}
            params = {'surface': sf_params, 'upper': up_params}
            for layer in ['surface', 'upper']:
                for param in params[layer]:
                    key = 'msm/pca/x/anl/%s_bt%s_vt%03d.pkl' % (param, bt, int(ft))

                    obj = s3.get_object(Bucket=BUCKET, Key=key)
                    try:
                        vals = pickle.loads(obj['Body'].read())
                    except EOFError:
                        vals = None

                    x = vals.loc[date].values

                    diff = np.sqrt((vals.values - x) ** 2).sum(axis=1)
                    args = np.argsort(diff)

                    cnd_date = vals.index[args]
                    cnd_date = [d.replace('-', '/') for d in cnd_date]

                    hist['%s' % param] = cnd_date[:cutoff]
                    # print(hist)

            pickle.dump(
                hist, open(tmp_file, 'wb')
            )

        dlim = 10
        os.makedirs('/tmp/similar_date/hist', exist_ok=True)
        make_similar_date_histogram(hist, dlim, save_file='/tmp/similar_date/hist/%s.html' % date)
        similar_date_url = 'https://simrec.s3-ap-northeast-1.amazonaws.com/similar_date/hist/%s.html' % date

        c = count_date(hist)
        date_list = c.columns

        if abs(3 - int(bt)) < abs(15 - int(bt)):
            wxct_bt = '03'
        else:
            wxct_bt = '15'

        # wxct
        prefix_wxct = 'http://chip-intra.wni.co.jp/ieec/pub/Pub_htdocs/TV/wxct'
        cnd_date_url = {
            d.replace('/', '-'): '%s/%s.%s.jpg' % (prefix_wxct, ''.join(d.split(sep='/')), wxct_bt)
            for d in date_list
        }

        '''
        os.makedirs('/tmp/wxct', exist_ok=True)
        for key in cnd_date_url:
            save_file = '/tmp/wxct/%s.%s.jpg' % (''.join(key.split(sep='-')), wxct_bt)
            os.system('wget -nc %s -P %s' % (cnd_date_url[key], save_file))
        '''

        # rd srp
        rdsrp_urls = [
            'http://er3.wni.co.jp/amoeba/datas/hind_RD/rd_srp.cgi?p=00&ap=&sdate=%s&edate=%s&usr='
            % (d, str((datetime.datetime.strptime(d, '%Y/%m/%d') + datetime.timedelta(days=1)).date()))
            for d in date_list
        ]

        html = get_query_result(
            nwp='MSM',
            similar_date_url=similar_date_url,
            cnd_date_url=cnd_date_url,
            rdsrp_url=rdsrp_urls
        )

        return Response(
            html,
            status_code=200,
            headers={'Content-Type': 'text/html'}
        )
    elif request.method == 'GET':
        html = get_base(nwp='MSM')
        return Response(
            html,
            status_code=200,
            headers={'Content-Type': 'text/html'}
        )


'''
@app.schedule('cron(* * * * ? *)')
def download_msm_bt00():
    tagid_surface = '400220000'
    url = WNI_DATA_CATALOG[tagid_surface]['url']

    date = datetime.datetime.now(pytz.timezone('UTC'))
    year = date.year
    month = date.month
    day = date.day

    url = '%s/%04d/%02d/%02d/%04d%02d%02d_000000.000' % (url, year, month, day, year, month, day)

    os.makedirs('/tmp/%s' % tagid_surface, exist_ok=True)
    os.system('wget %s -P /tmp/%s' % (url, tagid_surface))

    s3.upload_file(
        Filename='/tmp/%04d%02d%02d_000000.000',
        Bucket=BUCKET,
        Key='tmp/%04d%02d%02d_000000.000'
    )
'''

'''
        date = request.form['date']
        if re.match(r'\d{4}\D\d{2}\D\d{2}', date):
            boo = True
        elif re.match(r'\d+', date) and len(date) == 8:
            boo = True
        else:
            boo = False

        if boo:
            p = re.compile(r'\d+')
            ms = p.findall(date)
            date = ''.join(ms)

            save_path = '%s/templates/similar_date/%s.html' % (WEB_PATH, date)

            pres_msm_img = get_msm_image(
                date=date,
                forecast_time=int(forecast_time),
                param=['Pressure reduced to MSL'],
                level=['surface'],
                bt=bt)

            collections = []
            for layer in ['surface', 'upper']:
                collections += request.form.getlist('check_%s' % layer)

            collections = ['%s_bt%s_vt%s' % (c, bt, vt) for c in collections]

            cutoff = 5
            tmp_file = make_tmp_filename(cutoff, collections, forecast_time, 'pkl')
            tmp_file = '%s/tmp/similar_date/%s/%s' % (WEB_PATH, date, tmp_file)

            if os.path.exists(tmp_file):
                hist = read_similar_date(tmp_file)
            else:
                os.makedirs('%s/tmp/similar_date/%s' % (WEB_PATH, date), exist_ok=True)
                hist = extract_similar_date(
                    cutoff=5,
                    search_date=date,
                    ft=forecast_time,
                    collections=collections,
                    save_path=tmp_file
                )

                for key in hist:
                    hist[key] = hist[key]

            # make date candidate image path
            count = count_date(hist)
            date_list = list(count.keys())
            count_list = list(count.values())
            args = np.argsort(count_list)[::-1]
            date_list = np.array(date_list)[args][:8]

            rdsrp_urls = [
                'http://er3.wni.co.jp/amoeba/datas/hind_RD/rd_srp.cgi?p=00&ap=&sdate=%s&edate=%s&usr='
                % (d, str((datetime.datetime.strptime(d, '%Y/%m/%d') + datetime.timedelta(days=1)).date()))
                for d in date_list
            ]

            if os.path.exists('/home/ai-corner/part1/WXCT/%s.%s.jpg' % (date, '15')):
                img_bt = '15'
            else:
                img_bt = '03'

            cnd_date_img_path = {
                d: '/home/ai-corner/part1/WXCT/%s.%s.jpg' % (''.join(d.split(sep='/')), img_bt)
                for d in date_list
            }

            make_similar_date_histogram(hist, save_path)

            sd_path = '/similar_date/%s.html' % date
            html = render_template(
                'home.html',
                ft=forecast_time,
                params=params,
                level=level,
                sd_path=sd_path,
                search_date=date,
                pres_msm_img=pres_msm_img,
                cnd_date_img_path=cnd_date_img_path,
                rdsrp_urls=rdsrp_urls,
            )
        else:
            html = render_template(
                'home.html',
                params=params,
                level=level,
            )
        '''

# The view function above will return {"hello": "world"}
# whenever you make an HTTP GET request to '/'.
#
# Here are a few more examples:
#
# @app.route('/hello/{name}')
# def hello_name(name):
#    # '/hello/james' -> {"hello": "james"}
#    return {'hello': name}
#
# @app.route('/users', methods=['POST'])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We'll echo the json body back to the user in a 'user' key.
#     return {'user': user_as_json}
#
# See the README documentation for more examples.
#
