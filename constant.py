# -*- coding: utf-8 -*-


# UA
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0'

# 代理设置
PROXIES = {"http": "http://127.0.0.1:1080", "https": "http://127.0.0.1:1080"}

# 首页
HOME_URL = 'https://www.instagram.com/'
# 收藏页
SAVED_URL = 'https://www.instagram.com/{0}/saved/'
# 登录页
LOGIN_URL = 'https://www.instagram.com/accounts/login/ajax/'

# 用来从网页里提取 sharedData 的正则表达式
SHARED_DATA_REGEX = r'<script type="text/javascript">\s*window._sharedData\s*=\s*({.*});\s*</script>'

CHARSET = 'UTF-8'