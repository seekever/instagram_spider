# -*- coding: utf-8 -*-
import hashlib
import json
import re
import requests

# 代理设置
proxies = {"http": "http://127.0.0.1:1080", "https": "http://127.0.0.1:1080"}
# 首页
home_url = 'https://www.instagram.com'
# 收藏页
saved_url = 'https://www.instagram.com/{username}/saved/'
# sharedData 正则表达式，sharedData 包含 csrf token，username，媒体地址，...... 等信息
shared_data_regex = r'<script type="text/javascript">\s*window._sharedData\s*=\s*({.*});\s*</script>'

session = requests.session()

csrf_token = ''


# 获取 home 页内容
def access_home():
    r = session.get(url=home_url, proxies=proxies, timeout=30)
    r.encoding = 'utf-8'
    return r.text


# 解析 home 页内容得到 SCRF Token
def parse_csrf_token(html):
    global csrf_token
    s = re.search(shared_data_regex, html)
    json_obj = json.loads(s.group(1), encoding='utf8')
    csrf_token = json_obj['config']['csrf_token']


# 解析首页得到用户名
def parse_username(html):
    s = re.search(shared_data_regex, html)
    json_obj = json.loads(s.group(1), encoding='utf8')
    return json_obj['config']['viewer']['username']


# 登录
def sign_in():
    global  csrf_token
    sign_in_url = 'https://www.instagram.com/accounts/login/ajax/'
    data = {'password': 'wo2amber', 'queryParams': '{}', 'username': 'goosebaobao@gmail.com'}
    headers = {
        #'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)',
        'X-CSRFToken': csrf_token,
        #'Referer': 'https://www.instagram.com',
        #'X-Instagram-AJAX': '1',
        #'X-Requested-With': 'XMLHttpRequest'
    }

    r = session.post(url=sign_in_url, data=data, headers=headers, proxies=proxies, timeout=30)
    r.encoding = 'utf-8'
    return r.json()['authenticated']


def access_saved(username):
    r = session.get(saved_url.format(username=username), proxies=proxies, timeout=30)
    r.encoding = 'utf-8'
    return r.text


def parse_saved(html):
    global csrf_token

    s = re.search(shared_data_regex, html)
    json_obj = json.loads(s.group(1), encoding='utf8')
    csrf_token = json_obj['config']['csrf_token']

    # print(s.group(1))
    return json_obj['rhx_gis']


def access_album(page, xhx_gis):
    global  csrf_token
    print(csrf_token)
    print(xhx_gis)
    md5gis = gis(xhx_gis,  '/refuse_sea/?__a=1')
    print(md5gis)
    #md5gis = 'b6a16681b1f62218fead4991aeeea38b'
    print('gis=' + md5gis)
    album_url = 'https://www.instagram.com/refuse_sea/?__a=' + str(page)
    headers = {
        'Host': 'www.instagram.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.instagram.com/refuse_sea/saved/',
        'X-Instagram-GIS': md5gis,
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
    }
    r = session.get(url=album_url, headers=headers, proxies=proxies, timeout=30)
    r.encoding = 'utf-8'
    print('album=')
    print(r.status_code)
    print(r.text)


def parse_album(html):
    s = re.search(shared_data_regex, html)
    json_obj = json.loads(s.group(1), encoding='utf8')
    data = json_obj['entry_data']
    page = data['ProfilePage']
    # GraphQL facebook 开发的一种查询语言
    gra = page[0]['graphql']
    user = gra['user']
    edge = user['edge_saved_media']
    edges = edge['edges']
    for edge in edges:
        node = edge['node']
        # print(node['display_url'])


def gis(rhx_gis, path):
    global  csrf_token
    md5 = hashlib.md5()
    md5.update(str.encode(rhx_gis + ':' +  path))

    return md5.hexdigest()


if __name__ == '__main__':
    html = access_home()
    parse_csrf_token(html)
    if sign_in():
        html = access_home()
        username = parse_username(html)
        html = access_saved(username)
        xhx_gis = parse_saved(html)
        access_album(1, xhx_gis)
        parse_album(html)
    else:
        print('sign in fail')
