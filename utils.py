import pymysql
import re
import requests
import xlwings as xw
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
database = client["douyin"]
followers_videos_collection = database["followers_videos"]

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


def get_downloadurl(aweme_id):
    data = {
        'url': 'https://www.douyin.com/video/{}'.format(aweme_id)
    }
    response = requests.post(
        'https://www.daimadog.com/wp-content/themes/mytheme/action/dyjx.php',
        data=data)
    return response.json()['playurl']


def get_database_videos():
    mysql_data = []
    cursor.execute('select aweme_id from followers_datas')
    for data in cursor.fetchall():
        mysql_data.append(data[0])
    datas = followers_videos_collection.find({'aweme_id': {'$ne': 1}})
    mongodb_data = []
    for data in datas:
        mongodb_data.append(data['aweme_id'])
    return mysql_data, mongodb_data


def write2mongodb(user_videos_datas, mongodb_data):
    for video in user_videos_datas:
        aweme_id = video['aweme_id']
        if aweme_id in mongodb_data:
            continue
        else:
            try:
                # 如果不考虑判断视频在不在的话,可以使用更新操作
                # collection.update_one({'aweme_id': aweme_id}, {'$set': video})
                followers_videos_collection.insert(video)
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
        if data[0] in mysql_data:
            continue
        else:
            inser_sql = "insert into followers_datas values('{user}',{data})".format(
                user=username, data=str(data)[1:-1])
            # print(inser_sql)
            try:
                cursor.execute(inser_sql)
                db.commit()
            except Exception as e:
                print(e)
                db.rollback()


def datas_process(userdata):
    videos_data = []
    for item in userdata:
        if item['aweme_type'] == 4:
            aweme_id = item['aweme_id']
            desc = re.sub('[\\/:*?"<>|\n]', '', item['desc'])
            src = item['video']['play_addr']['url_list'][0]
            videos_data.append([aweme_id, desc, src])
    return videos_data


def truncateDataBase():
    # 清空mysql和mongodb数据库中follower_datas表中的数据
    cursor.execute("truncate table followers_datas")
    followers_videos_collection.remove({})


def write2txt(videos_data, user):
    with open(f'followers/{user}.txt', mode='a', encoding='utf-8') as f:
        if len(videos_data) == 0:
            return
        for video in videos_data:
            f.write(video[0] + "==" + video[1] + "==" + video[2])
            f.write('\n')


def write2excel(data, user):
    app = xw.App(visible=False, add_book=False)
    wb = app.books.open('douyin.xlsx')
    try:
        active_sheet = wb.sheets[user]
    except BaseException:
        active_sheet = wb.sheets.add(user)
    active_sheet.clear()
    active_sheet.range("A:A").api.NumberFormat = "@"
    for i in range(len(data)):
        for j in range(len(data[i])):
            active_sheet.range((i + 1, j + 1)).value = data[i][j]
    try:
        del wb.sheets['Sheet1']
    except BaseException:
        pass
    wb.save()
    wb.close()
    app.quit()


def dumptxt(file):
    temp = open(file, encoding='utf-8').readlines()
    data = list(set(temp))
    with open(file, mode='w', encoding='utf-8') as f:
        for aweme in data:
            f.write(aweme)


def log2file(filename,mode,time=False):
    import logging
    logger = logging.getLogger('get_latest')
    logger.setLevel(logging.INFO)
    filepath = filename
    hadler = logging.FileHandler(filepath, mode=mode, encoding='utf-8')
    hadler.setLevel(logging.NOTSET)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    if time:
        format = logging.Formatter("%(asctime)s - %(message)s")
    else:
        format = logging.Formatter("%(message)s")
    hadler.setFormatter(format)
    ch.setFormatter(format)
    logger.addHandler(ch)
    logger.addHandler(hadler)
    logger.info("*" * 80)
    return logger
