# 关于

下载 instagram 上收藏的图片/视频

# 准备

在 user.py 里设置 4 个常量，如下

```
USERNAME = 'username'
PASSWORD = 'password'
QUERY_HASH = 'xxx'
X_INSTAGRAM_GIS = 'xxx'
```

`username` 和 `password` 用来登录 instagram

`query_hash` 是调用 `https://www.instagram.com/graphql/query/` 的参数，`x_instagram_gis` 是调用 `https://www.instagram.com/username/?__a=1` 时在 `header` 里的参数，这 2 个参数请自行抓包获取

默认会将下载的图片或视频保存在 `c:\instagram`，可以自己修改目录

# 使用

```
python instagram
```

# 其他

instagram 对于客户端访问有频次的限制，若调用太频繁会返回 `429` 错误，程序会在两次访问之间休眠几秒来避免其触发

程序使用代理服务器访问 instagram，代理服务器配置见 `constant.PROXIES`

# 后续计划

* 生成全局缩略图：该缩略图为一个本地的 html 文件，显示所有的图片和视频
* 程序自动生成 `query_hash` 和 `x_instagram_gis`：暂时没有头绪
* 突破访问频次的限制：初步判断，定时向 instagram 发送 `ping` 和 `logging_client_event` 请求可以解除频次限制
* 文件名优化：文件名包括图片/视频的发布者信息