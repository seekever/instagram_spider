# 数据库所在目录，相对于主目录的相对路径
db_path = "database"
# 数据库文件名
db_file = "instragram.db"
# 建表，该表保存的是已下载媒体的 shortcode，后续下载时会跳过已下载的媒体
db_create_table = 'create table shortcode (code varchar(64) primary key)'
