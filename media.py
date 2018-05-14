# -*- coding: utf-8 -*-


# 媒体信息，可以是图片或视频
class Media(object):
    def __init__(self, id='', shortcode='', download_url='', multiple=False):
        self.id = id
        # 短码，可拼接详情页地址
        self.shortcode = shortcode
        # 下载地址
        self.download_url = download_url
        # 是否多个资源
        self.multiple = multiple

    def __str__(self):
        return "Media: id={0},  multiple={1}, shortcode={2}, download_url={3}".format(
            self.id, self.multiple, self.shortcode, self.download_url
        )
