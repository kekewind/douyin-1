# mitmdump抓包脚本
import json
import re
import pymysql
from pymongo import MongoClient
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
client = MongoClient("mongodb://localhost:27017/")
database = client["douyin"]
collection = database["favorites"]
cursor = db.cursor()
print("="*80)


def response(flow):
    # 将我的喜欢存入数据库和txt文件
    if 'https://www.douyin.com/aweme/v1/web/aweme/favorite/' in flow.request.url:
        with open('favorite.txt', 'a', encoding='utf-8') as f:
            for aweme in json.loads(flow.response.text)['aweme_list']:
                if 'play_addr' in aweme['video']:
                    aweme_id = aweme['aweme_id']
                    desc = re.sub('[\\\\/:*?"<>|\n]', '', aweme['desc'])
                    src = re.sub('watermark=1', 'watermark=0', aweme['video']['download_addr']['url_list'][-1])
                    f.write(
                        aweme_id +
                        "==" +
                        desc +
                        "==" +
                        src)
                    f.write('\n')
                # 写入mongodb
                collection.insert_one(dict(aweme))
                # 写入mysql
                aweme_id = aweme_id
                aweme_type = aweme['aweme_type']
                download_addr = src
                create_time = aweme['create_time']
                author_nickname = aweme['author']['nickname']
                author_sec_uid = aweme['author']['sec_uid']
                author_user_id = aweme['aweme_id']
                downloaded = 0
                data = [
                    aweme_id,
                    desc,
                    download_addr,
                    create_time,
                    aweme_type,
                    author_nickname,
                    author_sec_uid,
                    author_user_id,
                    downloaded]
                sql = 'insert into favorites values ({data})'.format(
                    data=str(data)[1:-1])
                print(sql)
                try:
                    cursor.execute(sql)
                    db.commit()
                except BaseException as e:
                    print(e)
                    db.rollback()

    # 将关注的人存入txt文件
    # if 'aweme/v1/user/following/list' in flow.request.url:
    #     with open('allfollowings.txt', 'a', encoding='utf-8') as f:
    #         for follower in json.loads(flow.response.text)['followings']:
    #             f.write(follower['nickname']+":"+follower['sec_uid'])
    #             f.write('\n')
    # 将关注的人存入数据库
    #     cursor = db.cursor()
    #     for follower in json.loads(flow.response.text)['followings']:
    #         nickname = follower['nickname']
    #         sec_uid = follower['sec_uid']
    #         uid = follower['uid']
    #         url = 'https://www.douyin.com/user/'+sec_uid
    #         signature = follower['signature']
    #         follower_type = 0
    #         data = [nickname,sec_uid,uid,url,signature,follower_type]
    #         sql = 'INSERT INTO followers VALUES ({data})'.format(data=str(data)[1:-1])
    #         print(sql)
    #         try:
    #             cursor.execute(sql)
    #             db.commit()
    #         except:
    #             db.rollback()
    #     cursor.close()
