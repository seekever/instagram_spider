# -*- coding: utf-8 -*-
import hashlib
import json
import re
import requests


# 媒体信息，包括图片和视频
class Media(object):
    def __init__(self, id='', url='', name='', video=False, download_url='', multiple=False):
        self.id = id
        # 详情页
        self.url = url
        self.name = name
        self.video = video
        # 下载地址
        self.download_url = download_url
        # 是否多个资源
        self.multiple = multiple

    def __str__(self):
        return "Media: id={0}, video={1}, multiple={2}, url={3}, download_url={4}".format(
            self.id, self.video, self.multiple, self.url, self.download_url
        )


class Instagram(object):
    # 代理设置
    proxies = {"http": "http://127.0.0.1:1080", "https": "http://127.0.0.1:1080"}

    # 首页
    home_url = 'https://www.instagram.com'
    # 收藏页
    saved_url = 'https://www.instagram.com/{0}/saved/'
    # 登录页
    login_url = 'https://www.instagram.com/accounts/login/ajax/'

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
        self.session.headers[
            'User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0'

        self.medias = []

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

    def login(self):
        data = {'password': self.password, 'queryParams': '{}', 'username': self.login_id}
        self.session.headers['X-CSRFToken'] = self.csrf_token
        r = self.session.post(url=Instagram.login_url, data=data, timeout=30)
        r.encoding = 'utf-8'
        json_obj = r.json()
        if json_obj['authenticated']:
            self.user_id = json_obj['userId']

    # 主要是拿到 username
    def access_saved(self):
        r = self.session.get(Instagram.saved_url.format(self.username), timeout=30)
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
        md5 = hashlib.md5()
        md5.update(str.encode(src))
        self.x_instagram_gis = md5.hexdigest()

    def fetch_medias(self):
        album_url = 'https://www.instagram.com/{0}/?__a=1'.format(self.username)
        self.session.headers['X-Instagram-GIS'] = 'b6a16681b1f62218fead4991aeeea38b'
        r = self.session.get(url=album_url, timeout=30)
        if r.status_code == 200:
            json_obj = r.json()
            graphql = json_obj['graphql']
            user = graphql['user']
            edges = user['edge_saved_media']['edges']
            for edge in edges:
                node = edge['node']
                media = Media(id=node['id'],
                              url='https://www.instagram.com/p/{0}/?saved-by={1}'.format(node['shortcode'],
                                                                                         self.username),
                              name=node['edge_media_to_caption']['edges'][0]['node']['text'],
                              video=node['is_video'], download_url=node['display_url'],
                              multiple=(node['__typename'] == 'GraphSidecar'))
                self.medias.append(media)
                print(str(node))


if __name__ == '__main__':
    it = Instagram(login_id='goosebaobao@gmail.com', password='978507')
    it.access_home()
    it.login()
    it.access_saved()
    # it.gen_rhx_gis()
    it.fetch_medias()
    for media in it.medias:
        print(media)
