# -*- coding: utf-8 -*-
import hashlib
import json
import re
import requests


class Instagram(object):
    # 代理设置
    proxies = {"http": "http://127.0.0.1:1080", "https": "http://127.0.0.1:1080"}

    # 首页
    home_url = 'https://www.instagram.com'
    # 收藏页
    saved_url = 'https://www.instagram.com/{username}/saved/'
    # 登录页
    sign_in_url = 'https://www.instagram.com/accounts/login/ajax/'

    # sharedData 正则表达式，sharedData 包含 csrf token，username，媒体地址，...... 等信息
    shared_data_regex = r'<script type="text/javascript">\s*window._sharedData\s*=\s*({.*});\s*</script>'

    def __init__(self, csrf_token='', rhx_gis='', username='', user_id='', login_id='', password=''):
        self.csrf_token = csrf_token
        self.rhx_gis = rhx_gis
        self.username = username
        self.user_id = user_id
        self.shared_data = ''
        self.x_instagram_gis = ''

        # 登录信息
        self.login_id = login_id
        self.password = password

        self.session = requests.session()
        self.session.proxies = Instagram.proxies
        self.session.headers['User-Agent']='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0'

    def __str__(self):
        return 'Instagram: csrf_token={0}, rhx_gis={1}, username={2}, user_id={3}, x_instagram_gis={4}'.format(
            self.csrf_token, self.rhx_gis,
            self.username, self.user_id, self.x_instagram_gis)

    def access_home(self):
        r = self.session.get(url=Instagram.home_url, timeout=30)
        r.encoding = 'utf-8'
        html = r.text
        s = re.search(Instagram.shared_data_regex, html)
        self.shared_data = s.group(1)
        json_obj = json.loads(self.shared_data, encoding='utf8')
        self.csrf_token = json_obj['config']['csrf_token']
        self.rhx_gis = json_obj['rhx_gis']

    def sign_in(self):
        data = {'password': self.password, 'queryParams': '{}', 'username': self.login_id}
        self.session.headers['X-CSRFToken'] = self.csrf_token
        r = self.session.post(url=Instagram.sign_in_url, data=data, timeout=30)
        r.encoding = 'utf-8'
        json_obj = r.json()
        if json_obj['authenticated']:
            self.user_id = json_obj['userId']

    def access_saved(self):
        r = self.session.get(Instagram.saved_url.format(username=self.username), timeout=30)
        r.encoding = 'utf-8'
        html = r.text
        s = re.search(Instagram.shared_data_regex, html)
        json_obj = json.loads(s.group(1), encoding='utf8')
        config = json_obj['config']
        self.csrf_token = config['csrf_token']
        self.username = config['viewer']['username']
        self.rhx_gis = json_obj['rhx_gis']

    def gen_rhx_gis(self):
        src = '{0}:/{1}/:{2}'.format(self.rhx_gis, self.username, '')
        print(src)
        md5 = hashlib.md5()
        md5.update(str.encode(src))
        self.x_instagram_gis = md5.hexdigest()

    def get_data(self):
        album_url = 'https://www.instagram.com/{0}/?__a=1'.format(self.username)
        self.session.headers['X-Instagram-GIS'] = 'b6a16681b1f62218fead4991aeeea38b'
        r = self.session.get(url=album_url, timeout=30)
        print(r.status_code)


if __name__ == '__main__':
    it = Instagram(login_id='goosebaobao@gmail.com', password='978507')
    it.access_home()
    print(it)
    it.sign_in()
    print(it)
    it.access_saved()
    print(it)
    print(it.gen_rhx_gis())
    print(it)
    it.get_data()
