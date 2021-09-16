# 获取用户最新的作品，不仅限与视频
from utils import update_user_videos
from utils import write2mysql
from utils import write2mongodb
from utils import datas_process
from utils import get_database_videos
from utils import log2file
from utils import download_new_videos
from download import download_aweme_photos
import json
import sys
import requests
import os
logger = log2file('followers_latest.log', 'w', True)
headers = {
    'user-agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Mobile Safari/537.36 Edg/87.0.664.66'
}


def get_user_new(sec_uid, max_cursor, user_awemes):
    iscontinue = False
    user_new_add = []
    signature = requests.get('http://8.9.15.155:3000/sign').text
    response = requests.get(
        f"https://www.iesdouyin.com/web/api/v2/aweme/post/?sec_uid={sec_uid}&count=30&max_cursor={max_cursor}&aid=1128&_signature={signature}&dytk=",
        headers=headers)
    data_json = json.loads(response.text)
    user_latest_aweme = data_json['aweme_list']
    for aweme in user_latest_aweme:
        if aweme['aweme_id'] not in user_awemes:
            user_new_add.append(aweme)
    # 新增的不够，继续获取下一页
    if len(user_new_add) == len(user_latest_aweme) and data_json['has_more']:
        iscontinue = True
    return user_new_add, iscontinue, data_json['max_cursor']


if __name__ == '__main__':
    mysql_data, mongodb_data = get_database_videos()
    all_user_new_aweme = 0
    all_user_new_photos_aweme = 0
    for line in open('followers.txt', encoding='utf-8'):
        user, sec_uid = line.rstrip().split(':')
        # 用户最新的所有作品
        user_latest_awme = []
        # 用户最新的视频aweme数量
        user_latest_videos_aweme_nums = 0
        # 用户最新的图片aweme数量
        user_latest_photos_aweme_nums = 0
        # 用来保存图片型的aweme
        logger.info(user + " is start")
        try:
            # 已经获取过的aweme
            videos = [
                video.rstrip() for video in open(
                    f'followers/{user}.txt',
                    encoding='utf-8').readlines()]
        except Exception as e:
            logger.info(e)
            logger.info(f"{user} has error")
            sys.exit(0)
        else:
            aweme_ids = [video[0:19] for video in videos]
            max_cursor = 0
            while True:
                new, goahead, max_cursor = get_user_new(
                    sec_uid=sec_uid, max_cursor=max_cursor, user_awemes=aweme_ids)
                user_latest_awme += new
                if not goahead:
                    break
        # user_latest_aweme_nums最新的作品新增数量
        user_latest_aweme_nums = len(user_latest_awme)
        all_user_new_aweme += user_latest_aweme_nums
        if user_latest_aweme_nums > 0:
            # 写入mongodb
            write2mongodb(user_latest_awme, mongodb_data)
            # 写入mysql
            write2mysql(datas_process(user_latest_awme)[0], user, mysql_data)
            for aweme in user_latest_awme:
                if aweme['aweme_type'] == 4:
                    new_aweme_id = aweme['aweme_id']
                    desc = aweme['desc']
                    src = aweme['video']['play_addr']['url_list'][0]
                    video = new_aweme_id + " == " + desc + " == " + src
                    videos.insert(0, video)
                    user_latest_videos_aweme_nums += 1
                elif aweme['aweme_type'] == 2:
                    user_latest_photos_aweme_nums += 1
            # 有视频aweme，则写入txt
            if user_latest_videos_aweme_nums > 0:
                update_user_videos(user, videos)
            # 有图片aweme，则下载
            if user_latest_photos_aweme_nums > 0:
                user_images = os.listdir(fr'F:\douyin\images\{user}')
                photos_awemes = [photo[0:19] for photo in user_images]
                # Todo 下图片的函数
                for aweme in user:
                    pass
                # all_user_new_photos_aweme += user_latest_photos_aweme_nums
            download_new_videos(user, user_latest_videos_aweme_nums,logger,os,sys)
            logger.info(f'{user}新增了{user_latest_aweme_nums}个作品')
            logger.info(f'其中有{user_latest_videos_aweme_nums}个视频作品，{user_latest_photos_aweme_nums}个图片作品')
        else:
            logger.info(f'{user}没有新作品发布')
    if all_user_new_photos_aweme > 0:
        download_aweme_photos()
