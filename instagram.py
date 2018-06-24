# -*- coding: utf-8 -*-
import json
import os
import os.path
import re
import requests
import time

from constant import *
from media import Media
from user import *


class Instagram(object):

    def __init__(self, username, password, rootpath='c:\instagram'):

        self.session = requests.session()
        self.session.headers['User-Agent'] = USER_AGENT

        # 媒体保存路径
        self.rootpath = rootpath

        self.username = username
        self.password = password

        self.csrf_token = None
        self.user_id = None

        self.has_next_page = False
        self.end_cursor = None

        # 收藏列表
        self.shortcodes = []
        # 媒体列表
        self.medias = []

    def __str__(self):
        return 'Instagram: csrf_token={}, username={}, user_id={}, has_next_page={}'.format(
            self.csrf_token, self.username, self.user_id, str(self.has_next_page))

    # http 请求封装
    def http_req(self, url, data=None, headers=None, get=True):
        if get:
            req = self.session.get(url=url, data=data, headers=headers, proxies=PROXIES, timeout=TIMEOUT)
        else:
            req = self.session.post(url=url, data=data, headers=headers, proxies=PROXIES, timeout=TIMEOUT)
        req.encoding = CHARSET
        if req.status_code == 200:
            return req
        else:
            print('http fail.\r\n\turl={},\r\n\tstatus={},\r\n\ttext={}'.format(
                url, str(req.status_code), req.text))
            return None

    # 返回文本
    def http_text(self, url, data=None, headers=None, get=True):
        req = self.http_req(url, data, headers, get)
        if req:
            return req.text
        else:
            return None

    # 返回 json
    def http_json(self, url, data=None, headers=None, get=True):
        req = self.http_req(url, data, headers, get)
        if req:
            return req.json()
        else:
            return None

    # 登录
    def login(self):
        req = self.http_req(HOME_URL)
        # 从 cookies 里得到 csrf_token
        self.csrf_token = req.cookies['csrftoken']
        data = {'password': self.password, 'queryParams': '{}', 'username': self.username}
        self.session.headers['X-CSRFToken'] = self.csrf_token
        root = self.http_json(LOGIN_URL, data=data, get=False)
        if root['authenticated']:
            self.user_id = root['userId']

    # 得到收藏列表的首页
    def graphql_start(self):
        self.session.headers['X-Instagram-GIS'] = X_INSTAGRAM_GIS
        root = self.http_json(GRAPHQL_START_URL.format(self.username))
        if root is not None:
            self.extract_shortcode(root['graphql']['user'])

    # 得到收藏列表的下一页
    def graphql_next(self):
        root = self.http_json(GRAPHQL_NEXT_URL.format(QUERY_HASH, self.user_id, self.end_cursor))
        if root is not None:
            self.extract_shortcode(root['data']['user'])

    # 从 json 里解析出收藏的 shortcode，并获取是否有下页，及下页的游标
    def extract_shortcode(self, user):
        # .edge_saved_media.page_info
        page_info = user['edge_saved_media']['page_info']
        self.has_next_page = page_info['has_next_page']
        self.end_cursor = page_info['end_cursor']
        # .edge_saved_media.edges
        edges = user['edge_saved_media']['edges']
        for edge in edges:
            node = edge['node']
            self.shortcodes.append(node['shortcode'])

    # 访问收藏详情得到媒体信息
    def get_medias(self, shortcode):
        url = SHORTCODE_URL.format(shortcode, self.username)
        html = self.http_text(url)
        m = re.search(SHARED_DATA_REGEX, html)
        root = json.loads(m.group(1), encoding=CHARSET)
        if root is not None:
            shortcode_media = root['entry_data']['PostPage'][0]['graphql']['shortcode_media']
            if shortcode_media['__typename'] == 'GraphSidecar':
                self.get_multi_medias(shortcode_media)
            else:
                self.get_single_medias(shortcode_media)

    # 获取单个媒体的信息
    def get_single_medias(self, shortcode_media):
        video = (shortcode_media['__typename'] == 'GraphVideo')
        self.medias.append(Media(shortcode_media['id'], shortcode_media['video_url' if video else 'display_url']))

    # 获取多重媒体的每一个媒体
    def get_multi_medias(self, shortcode_media):
        edges = shortcode_media['edge_sidecar_to_children']['edges']
        for edge in edges:
            node = edge['node']
            video = (node['__typename'] == 'GraphVideo')
            self.medias.append(Media(node['id'], node['video_url' if video else 'display_url']))

    # 为用户创建保存媒体的目录
    def mkdir(self):
        if not os.path.exists(self.rootpath):
            os.mkdir(self.rootpath)
        os.chdir(self.rootpath)
        if not os.path.exists(self.username):
            os.mkdir(self.username)
        os.chdir(self.username)

    # 下载媒体，文件名为媒体 id
    def download_media(self, media):
        pos = media.url.rfind('.')
        filename = media.id + media.url[pos:]
        if os.path.exists(filename):
            print('file already exists. pass')
        else:
            print('download file: ' + filename)
            req = self.http_req(media.url)
            try:
                with open(filename, "wb") as file:
                    file.write(req.content)
            except:
                print('download file fail: ' + filename)
                if os.path.exists(filename):
                    os.remove(filename)


if __name__ == '__main__':
    it = Instagram(USERNAME, PASSWORD)

    print('login')
    it.login()

    page = 1
    time.sleep(1)
    print('get page: {}'.format(page))
    it.graphql_start()

    while it.has_next_page:
        it.has_next_page = False
        page += 1
        time.sleep(60 if page % 5 == 0 else 10)
        print('get page: {}'.format(page))
        it.graphql_next()

    page = 1
    for shortcode in it.shortcodes:
        page += 1
        time.sleep(3 if page % 5 == 0 else 1)
        print('get medias for: ' + shortcode)
        try:
            it.get_medias(shortcode)
        except:
            print('get media error')

    print('mkdir')
    it.mkdir()

    print('download medias')
    page = 1
    for media in it.medias:
        page += 1
        time.sleep(2 if page % 5 == 0 else 1)
        it.download_media(media)

    print('done...')
