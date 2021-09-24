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


# 更新文件写入新的视频
def update_user_videos(user, videos):
    with open(f'followers/{user}.txt', mode='w', encoding='utf-8') as f:
        for video in videos:
            f.write(video)
            f.write('\n')


def download_new_videos(user, number, logger, os, sys):
    path = 'F:/douyin/' + user
    videos = open(f'followers/{user}.txt',
                  encoding='utf-8').readlines()[:number]
    for video in videos:
        aweme_id, desc, src = video.rstrip().split("==")
        filename = aweme_id + "_" + desc
        savepath = path + "/" + filename + ".mp4"
        try:
            response = requests.get(
                url=src,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Android 5.1.1; Mobile; rv:68.0) Gecko/68.0 Firefox/68.0',
                },
                timeout=10).content
        except Exception as e:
            logger[0].info(e)
        else:
            with open(savepath, 'wb') as f:
                f.write(response)
                logger[0].info(video[0:19] + "\t下载完成")
            if os.path.getsize(savepath) < 2:
                logger[0].info(video[0:19] + "\t下载出错，文件大小不正常，建议检查下程序")
                os.remove(savepath)
                sys.exit(0)
            logger[1].info(user + " " + video[0:19] + "\t下载完成")


def download_photos_aweme(photos_aweme):
    pass


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


def write2mysql(datas, username, mysql_data):
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
    photo_aweme_num = 0
    for item in userdata:
        if item['aweme_type'] == 4:
            aweme_id = item['aweme_id']
            desc = re.sub('[\\/:*?"<>|\n]', '', item['desc'])
            src = re.sub('watermark=1', 'watermark=0', item['video']['download_addr']['url_list'][1])
            videos_data.append([aweme_id, desc, src])
        elif item['aweme_type'] == 2:
            photo_aweme_num += 1
    return videos_data, photo_aweme_num


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


def log2file(name, filename, ch=False, mode='a', time=False):
    import logging
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    filepath = f'{filename}.log'
    hadler = logging.FileHandler(filepath, mode=mode, encoding='utf-8')
    hadler.setLevel(logging.NOTSET)
    if time:
        format = logging.Formatter("%(asctime)s - %(message)s")
    else:
        format = logging.Formatter("%(message)s")
    hadler.setFormatter(format)
    if ch:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(format)
        logger.addHandler(ch)
    logger.addHandler(hadler)
    return logger
