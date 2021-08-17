import pymysql
import re
import xlwings as xw
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
database = client["douyin"]
collection = database["followers_videos"]
app = xw.App(visible=False, add_book=False)
wb = app.books.add()
host = 'localhost'
port = 3306
database = 'douyin'
user = 'root'
password = '123456'
db = pymysql.connect(
    host=host,
    port=port,
    db=database,
    user=user,
    password=password)
cursor = db.cursor()


def get_database_videos():
    mysql_data = []
    cursor.execute('select aweme_id from followers_datas')
    for data in cursor.fetchall():
        mysql_data.append(data[0])
    datas = collection.find({'aweme_id': {'$ne': 1}})
    mongodb_data = []
    for data in datas:
        mongodb_data.append(data['aweme_id'])
    return mysql_data, mongodb_data


def write2mongodb(user_videos_datas, mongodb_data):
    for video in user_videos_datas:
        aweme_id = video['aweme_id']
        if aweme_id in mongodb_data:
            pass
        else:
            try:
                # 如果不考虑判断视频在不在的话,可以使用更新操作
                # collection.update_one({'aweme_id': aweme_id}, {'$set': video})
                collection.insert(video)
            except BaseException:
                print("插入mongodb数据库失败")


def mysql_connect():
    sql = f'drop table if exists followers_datas'
    cursor.execute(sql)
    create_table = f"""CREATE TABLE followers_datas (
                    author varchar(50) comment '作者',
                    aweme_id varchar(25),
                    vid varchar(100),
                    description varchar(255),
                    src varchar(255),
                    primary key (aweme_id))"""
    cursor.execute(create_table)
    return db, cursor


def write2mysql(datas, username, db, cursor, mysql_data):
    for data in datas:
        if datas[0] in mysql_data:
            pass
        else:
            inser_sql = "insert into followers_datas values('{user}',{data})".format(
                user=username, data=str(data)[1:-1])
            try:
                cursor.execute(inser_sql)
                db.commit()
            except Exception as e:
                db.rollback()


def datas_process(userdata):
    small_data = []
    for item in userdata:
        if item['aweme_type'] == 4:
            aweme_id = item['aweme_id']
            vid = item['video']['vid']
            temp_src = item['video']['download_addr']['url_list'][0]
            src = re.sub('&watermark=1', '&watermark=0', temp_src, re.S)
            desc = re.sub('[\\/:*?"<>|\n]', '', item['desc'])
            small_data.append([aweme_id, vid, desc, src])
    return small_data


def write2txt(datas, user):
    with open(f'followers/{user}.txt', mode='w', encoding='utf-8') as f:
        for video in datas:
            f.write(video[0] + "==" + video[1] + "==" + video[2])
            f.write('\n')


def write2excel(data, user):
    try:
        active_sheet = wb.sheets.add(user)
    except BaseException:
        active_sheet = wb.sheets[user]
    active_sheet.range("A:A").api.NumberFormat = "@"
    for i in range(len(data)):
        for j in range(len(data[i])):
            active_sheet.range((i + 1, j + 1)).value = data[i][j]


def dumptxt(file):
    temp = open(file,encoding='utf-8').readlines()
    data = list(set(temp))
    with open(file,mode='w',encoding='utf-8') as f:
        for aweme in data:
            f.write(aweme)