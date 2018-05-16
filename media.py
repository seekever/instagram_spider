# -*- coding: utf-8 -*-


# 媒体信息，图片或视频
class Media(object):
    def __init__(self, id, url):
        # 媒体id，保存时作为文件名
        self.id = id
        # 下载地址
        self.url = url

    def __str__(self):
        return "Media: id={}, url={}".format(self.id, self.url)
