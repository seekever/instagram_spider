# -*- coding: utf-8 -*-
import hashlib
import json
import os
import os.path
import re
import requests

from constant import *
from media import Media
from user import LOGIN_ID, PASSWORD


class Instagram(object):
    # gis = '{{"shortcode":"{0}","first":50,"after":"{1}"}}'

    def __init__(self, csrf_token='', rhx_gis='', username='', user_id='', login_id='', password='',
                 rootpath='c:\instagram'):

        self.rootpath = rootpath

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
        self.session.proxies = PROXIES
        self.session.headers['User-Agent'] = USER_AGENT

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
        r = self.session.get(url=HOME_URL, timeout=30)
        r.encoding = CHARSET
        html = r.text
        s = re.search(SHARED_DATA_REGEX, html)
        self.shared_data = s.group(1)
        json_obj = json.loads(self.shared_data, encoding='utf8')
        self.csrf_token = json_obj['config']['csrf_token']
        self.rhx_gis = json_obj['rhx_gis']

    # 登录
    def login(self):
        data = {'password': self.password, 'queryParams': '{}', 'username': self.login_id}
        self.session.headers['X-CSRFToken'] = self.csrf_token
        r = self.session.post(url=LOGIN_URL, data=data, timeout=30)
        r.encoding = CHARSET
        json_obj = r.json()
        if json_obj['authenticated']:
            self.user_id = json_obj['userId']

    # 主要是拿到 username
    def access_saved(self):
        r = self.session.get(SAVED_URL.format(self.username), timeout=30)
        r.encoding = CHARSET
        html = r.text
        s = re.search(SHARED_DATA_REGEX, html)
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
        md5.update(data.encode(CHARSET))
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
                              shortcode=node['shortcode'],
                              download_url=node['display_url'],
                              multiple=(node['__typename'] == 'GraphSidecar'))
                self.saved.append(media)
                # print(str(node))

    # 访问收藏详情得到媒体信息
    def get_medias(self, media):
        r = self.session.get(media.url)
        html = r.text
        s = re.search(SHARED_DATA_REGEX, html)
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
                  shortcode=node['shortcode'],
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
                      shortcode=node['shortcode'],
                      download_url=node[url_name]))
        return medias

    def mkdir(self):
        if not os.path.exists(self.rootpath):
            os.mkdir(self.rootpath)
        os.chdir(self.rootpath)
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
    print(it)
    # it.login()
    # it.access_saved()
    # # it.gen_rhx_gis()
    # while it.has_next_page:
    #     it.fetch_saved()
    # for media in it.saved:
    #     it.get_medias(media)
    # it.mkdir()
    # it.download_medias()
