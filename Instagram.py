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

    def __init__(self, csrf_token='', rhx_gis='', username='', user_id='', login_id=None, password=None):
        self.csrf_token = csrf_token
        self.rhx_gis = rhx_gis
        self.username = username
        self.user_id = user_id
        self.shared_data = None

        # 登录信息
        self.login_id = login_id
        self.password = password

        self.session = requests.session()
        self.session.proxies = Instagram.proxies

    def __str__(self):
        return 'Instagram: csrf_token={0}, rhx_gis={1}, username={2}, user_id={3}'.format(self.csrf_token, self.rhx_gis,
                                                                                          self.username, self.user_id)

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


if __name__ == '__main__':
    it = Instagram(login_id='goosebaobao@gmail.com', password='978507')
    it.access_home()
    print(it)
    it.sign_in()
    print(it)
