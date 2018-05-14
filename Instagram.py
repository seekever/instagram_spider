# -*- coding: utf-8 -*-
import hashlib
import json
import os
import os.path
import re
import requests

from config import LOGIN_ID, PASSWORD


# 媒体信息，包括图片和视频
class Media(object):
    def __init__(self, id='', url='', video=False, download_url='', multiple=False):
        self.id = id
        # 详情页
        self.url = url
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
    home_url = 'https://www.instagram.com/'
    # 收藏页
    saved_url = 'https://www.instagram.com/{0}/saved/'
    # 登录页
    login_url = 'https://www.instagram.com/accounts/login/ajax/'

    gis = '{{"shortcode":"{0}","first":50,"after":"{1}"}}'

    # sharedData 正则表达式，sharedData 包含 csrf token，username，媒体地址，...... 等信息
    shared_data_regex = r'<script type="text/javascript">\s*window._sharedData\s*=\s*({.*});\s*</script>'

    def __init__(self, csrf_token='', rhx_gis='', username='', user_id='', login_id='', password='',
                 root='c:\instagram'):

        self.root = root

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

        self.has_next_page = True
        self.end_cursor = ''

        # 收藏列表
        self.saved = []
        # 媒体列表
        self.medias = []

    def __str__(self):
        return 'Instagram: csrf_token={0}, rhx_gis={1}, username={2}, user_id={3}, x_instagram_gis={4}'.format(
            self.csrf_token, self.rhx_gis,
            self.username, self.user_id, self.x_instagram_gis)

    # 访问首页得到 csrf_token
    def access_home(self):
        r = self.session.get(url=Instagram.home_url, timeout=30)
        r.encoding = 'utf-8'
        html = r.text
        s = re.search(Instagram.shared_data_regex, html)
        self.shared_data = s.group(1)
        json_obj = json.loads(self.shared_data, encoding='utf8')
        self.csrf_token = json_obj['config']['csrf_token']
        self.rhx_gis = json_obj['rhx_gis']

    # 登录
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
        src = Instagram.gis.format('', '')
        data = self.rhx_gis + ":" + src
        print(data)
        md5 = hashlib.md5()
        md5.update(data.encode('utf-8'))
        print(md5.hexdigest())
        # self.x_instagram_gis = md5.hexdigest()

    # 得到收藏列表
    def fetch_saved(self):
        saved_url = 'https://www.instagram.com/{0}/?__a=1'.format(self.username)
        self.session.headers['X-Instagram-GIS'] = '588b1b8709fd1f5cb4de30b890d7a140'
        # 'b6a16681b1f62218fead4991aeeea38b'
        r = self.session.get(url=saved_url, timeout=30)
        if r.status_code == 200:
            json_obj = r.json()
            graphql = json_obj['graphql']
            user = graphql['user']
            edges = user['edge_saved_media']['edges']
            self.has_next_page = user['edge_saved_media']['has_next_page']
            self.end_cursor = user['edge_saved_media']['end_cursor']
            for edge in edges:
                node = edge['node']
                media = Media(id=node['id'],
                              url='https://www.instagram.com/p/{0}/?saved-by={1}'.format(node['shortcode'],
                                                                                         self.username),
                              video=node['is_video'], download_url=node['display_url'],
                              multiple=(node['__typename'] == 'GraphSidecar'))
                self.saved.append(media)
                # print(str(node))

    # 访问收藏详情得到媒体信息
    def get_medias(self, media):
        r = self.session.get(media.url)
        html = r.text
        s = re.search(Instagram.shared_data_regex, html)
        self.shared_data = s.group(1)
        json_obj = json.loads(self.shared_data, encoding='utf8')
        if media.multiple:
            self.medias += self.get_multi_medias(json_obj)
        else:
            self.medias += self.get_single_medias(json_obj)

    def get_single_medias(self, json_obj):
        medias = []
        url_name = None
        node = json_obj['entry_data']['PostPage'][0]['graphql']['shortcode_media']
        video = (node['__typename'] == 'GraphVideo')
        if video:
            url_name = 'video_url'
        else:
            url_name = 'display_url'
        medias.append(
            Media(id=node['id'],
                  url='https://www.instagram.com/p/{0}/?saved-by={1}'.format(node['shortcode'], self.username),
                  video=video,
                  download_url=node[url_name]))
        return medias

    def get_multi_medias(self, json_obj):
        medias = []
        nodes = json_obj['entry_data']['PostPage'][0]['graphql']['shortcode_media']['edge_sidecar_to_children']['edges']
        for node_t in nodes:
            node = node_t['node']
            video = (node['__typename'] == 'GraphVideo')
            if video:
                url_name = 'video_url'
            else:
                url_name = 'display_url'
            medias.append(
                Media(id=node['id'],
                      url='https://www.instagram.com/p/{0}/?saved-by={1}'.format(node['shortcode'], self.username),
                      video=video,
                      download_url=node[url_name]))
        return medias

    def mkdir(self):
        if not os.path.exists(self.root):
            os.mkdir(self.root)
        os.chdir(self.root)
        if not os.path.exists(self.username):
            os.mkdir(self.username)
        os.chdir(self.username)

    def download_medias(self):
        for media in self.medias:
            filename = media.id
            if media.video:
                filename += '.mp4'
            else:
                filename += '.jpg'
            if os.path.exists(filename):
                print('file already exists.pass')
            else:
                print('download file:' + filename)
                r = self.session.get(media.download_url)
                try:
                    with open(filename, "wb") as file:
                        file.write(r.content)
                except Exception as e:
                    if os.path.exists(filename):
                        os.remove(filename)


if __name__ == '__main__':
    it = Instagram(login_id=LOGIN_ID, password=PASSWORD)
    it.access_home()
    it.login()
    it.access_saved()
    # it.gen_rhx_gis()
    while it.has_next_page:
        it.fetch_saved()
    for media in it.saved:
        it.get_medias(media)
    it.mkdir()
    it.download_medias()
