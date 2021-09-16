# 获取正在关注的人的所有上传视频
# https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids=7006608594028334347
from utils import *
logger = log2file('get_followers_data.log', 'w')


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
    signature = requests.get('http://8.9.15.155:3000/sign').text
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
    all_aweme = 0
    all_video_aweme = 0
    all_photo_aweme = 0
    users = []
    user_secid = []
    # 获得数据库中已经写过的信息
    mysql_data, mongodb_data = get_database_videos()
    with open('followers.txt', encoding='utf-8') as f:
        for item in f.readlines():
            user_secid.append(item.rstrip())
    error_user = []
    for item in user_secid:
        user, sec_id = item.split(':')
        users.append(user)
        user_video_datas = []
        logger.info(user + " " + sec_id)
        try:
            user_video_datas = get_videos(sec_id)
            # 写入MySQL,excel,TXT中的数据与mongod的不一样
            videos_data, photo_aweme_num = datas_process(user_video_datas)
            all_photo_aweme += photo_aweme_num
        except Exception as e:
            logger.info(e)
            error_user.append(user)
            users.remove(user)
            logger.info(user + "has error")
        else:
            user_awemes_videos = len(videos_data)
            all_video_aweme += user_awemes_videos
            if user_awemes_videos > 0:
                write2excel(videos_data, user)
                write2txt(videos_data, user)
                write2mysql(videos_data, user, mysql_data)
            else:
                # 没有视频，只创建txt文件
                logger.info(user + "\t作品中没有一个视频，只创建空文件")
                write2txt(videos_data, user)
        finally:
            user_awemes_nums = len(user_video_datas)
            all_aweme += user_awemes_nums
            if user_awemes_nums > 0:
                write2mongodb(user_video_datas, mongodb_data)
            else:
                logger.info(user + "\t咋一个作品都没有啊")
    cursor.close()
    db.close()
    # 获取信息后直接下载
    # download_from_txt()
    # download_imgs()
    # 输出统计信息
    usersnum = len(users)
    distinct_user = list(set(users))
    distinct_usersnum = len(distinct_user)
    logger.info(f"本次运行一共获取{usersnum}个follower关注的数据")
    if len(error_user) > 0:
        logger.info("其中出错的foller：" + str(error_user)[1:-1])
    logger.info(f"剔除重名和出错的，一共有{distinct_usersnum}个follower，他们是:")
    for i in range(0, len(distinct_user), 5):
        j = i
        info = ''
        for j in range(j, j + 5):
            try:
                info += distinct_user[j].ljust(12,' ')
            except Exception as e:
                pass
        logger.info(info)
    logger.info(
        f"这么多关注中一共有{all_aweme}个作品，其中有{all_video_aweme}个视频，其他的{all_aweme-all_video_aweme}个都是图片类型作品")
