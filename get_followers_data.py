# 获取正在关注的人的所有上传视频
# https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids=7006608594028334347
from utils import *
logger = log2file('get_followers_data.log','w')


def get_one_page_videos_data(sec_uid, signature, max_cursor):
    url = f'https://www.iesdouyin.com/web/api/v2/aweme/post/?sec_uid={sec_uid}&count=21&max_cursor={max_cursor}&aid=1128&_signature={signature}&dytk='
    headers = {
        'accept': 'application/json',
        'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
    }
    response = requests.request("GET", url, headers=headers)
    return response.json()


def get_one_page_info(sec_uid, max_cursor):
    page_video_data = []
    signature = requests.get('http://localhost:3000/sign').text
    data_json = get_one_page_videos_data(sec_uid, signature, max_cursor)
    if data_json and 'aweme_list' in data_json.keys():
        page_video_data = data_json['aweme_list']
    try:
        iscontinue = data_json['has_more']
    except BaseException:
        logger.info("服务器错误，请求再来一遍")
        return page_video_data, max_cursor
    else:
        if iscontinue:
            return page_video_data, data_json['max_cursor']
        else:
            return page_video_data, None


def get_videos(sec_uid):
    max_cursor = 0
    all_data = []
    while True:
        page_data, max_cursor = get_one_page_info(sec_uid, max_cursor)
        all_data += page_data
        logger.info(str(len(all_data)))
        if not max_cursor:
            break
    return all_data


if __name__ == "__main__":
    user_secid = []
    # 获得数据库中已经写过的信息
    mysql_data, mongodb_data = get_database_videos()
    with open('followers.txt', encoding='utf-8') as f:
        for item in f.readlines():
            user_secid.append(item.rstrip())
    error_user = []
    for item in user_secid:
        user, sec_id = item.split(':')
        user_video_datas = []
        logger.info(user+" "+sec_id)
        try:
            user_video_datas = get_videos(sec_id)
            # 写入MySQL,excel,TXT中的数据与mongod的不一样
            videos_data = datas_process(user_video_datas)
        except Exception as e:
            logger.info(e)
            error_user.append(user)
            logger.info(user + "has error")
        else:
            if len(videos_data) > 0:
                write2excel(videos_data, user)
                write2txt(videos_data, user)
                write2mysql(videos_data, user, db, cursor, mysql_data)
        finally:
            if len(user_video_datas) > 0:
                write2mongodb(user_video_datas, mongodb_data)
            else:
                logger.info(user + "\t咋一个作品都没有啊")
    logger.info(str(error_user))
    cursor.close()
    db.close()
