# 获取用户最新的作品，不仅限与视频
import time
from utils import update_user_videos
from utils import write2mysql
from utils import write2mongodb
from utils import datas_process
from utils import get_database_videos
from utils import log2file
from utils import download_new_videos
from download import download_photo
import re
import json
import sys
import requests
import os
logger = log2file('main', '获取关注们最新的作品', ch=True, mode='w', time=True)
logger2 = log2file('download', '下载', mode='a')
headers = {
    'user-agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Mobile Safari/537.36 Edg/87.0.664.66'
}


def get_user_new(sec_uid, max_cursor, user_awemes):
    iscontinue = False
    user_new_add = []
    signature = requests.get('http://8.9.15.155:3000/sign').text
    # 控制速度
    time.sleep(3)
    while True:
        try:
            response = requests.get(
                f"https://www.iesdouyin.com/web/api/v2/aweme/post/?sec_uid={sec_uid}&count=30&max_cursor={max_cursor}&aid=1128&_signature={signature}&dytk=",
                headers=headers)
        except Exception as e:
            logger.info(e)
            time.sleep(10)
        else:
            break
    data_json = json.loads(response.text)
    user_latest_aweme = data_json['aweme_list']
    logger.info(len(user_latest_aweme))
    for aweme in user_latest_aweme:
        if aweme['aweme_id'] not in user_awemes:
            user_new_add.append(aweme)
    # 新增的不够，继续获取下一页
    if len(user_new_add) == len(user_latest_aweme) and data_json['has_more']:
        iscontinue = True
    return user_new_add, iscontinue, data_json['max_cursor']


def download_photo_aweme(aweme, username):
    rootdir = r"F:\douyin\images"
    author_dir = rootdir + os.sep + username
    if not os.path.exists(author_dir):
        os.makedirs(author_dir)
    rs = requests.get(
        url='https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={}&dytk='.format(
            aweme[0]),
        headers=headers,
        timeout=5).text
    response_json = json.loads(rs)
    desc = re.sub('[\\/:*?"<>|\n]', '', aweme[1])
    aweme_images = response_json['item_list'][0]['images']
    # 只有一张图片：
    if aweme_images is None:
        download_photo(
            src=response_json['item_list'][0]['image_infos'][0]['label_large']['url_list'][0],
            i=0,
            aweme_id=aweme[0],
            desc=desc,
            author_dir=author_dir)
    # 多张图片：
    else:
        for i in range(len(aweme_images)):
            download_photo(
                src=aweme_images[i]['url_list'][0],
                i=i,
                aweme_id=aweme[0],
                desc=desc,
                author_dir=author_dir)
    logger2.info(username + " photo_aweme " + aweme[0] + "\t下载完成")


if __name__ == '__main__':
    latests = []
    logger.info("*" * 80)
    logger.info('开始这次任务，获取所有关注的最新作品')
    mysql_data, mongodb_data = get_database_videos()
    all_user_new_aweme = 0
    all_user_new_photos_aweme = 0
    user2sec_uid = open('followers.txt', encoding='utf-8').readlines()
    usernum = len(user2sec_uid)
    for i, line in enumerate(user2sec_uid, start=1):
        user, sec_uid = line.rstrip().split(':')
        # 用户最新的所有作品
        user_latest_awme = []
        # 用户最新的视频aweme数量
        user_latest_videos_aweme_nums = 0
        # 用户最新的图片aweme数量
        user_latest_photos_aweme_nums = 0
        # 用来保存图片型的aweme
        user_latest_photos_aweme = []
        logger.info(f"第{i}个 " + user + " is start")
        logger.info(f'{user}的主页是：https://www.douyin.com/user/{sec_uid}')
        try:
            # 已经获取过的aweme
            videos = [
                video.rstrip() for video in open(
                    f'followers/{user}.txt',
                    encoding='utf-8').readlines()]
            try:
                photos = [photo[0:19]
                          for photo in os.listdir(fr'F:\douyin\images\{user}')]
            except BaseException:
                photos = []
        except Exception as e:
            logger.info(e)
            logger.info(f"{user} has error")
            sys.exit(0)
        else:
            # 已经获取过的aweme的aweme_id
            aweme_ids = [video[0:19] for video in videos] + list(set(photos))
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
                aweme_id = aweme['aweme_id']
                desc = re.sub('[\\\\/:*?"<>|\n]', '', aweme['desc'])
                latests.append('    '.join([user,aweme_id,desc]))
                if aweme['aweme_type'] == 4:
                    src = re.sub(
                        'watermark=1',
                        'watermark=0',
                        aweme['video']['download_addr']['url_list'][1])
                    video = aweme_id + "==" + desc + "==" + src
                    videos.insert(0, video)
                    user_latest_videos_aweme_nums += 1
                elif aweme['aweme_type'] == 2:
                    user_latest_photos_aweme.append(
                        [aweme_id, desc])
                    user_latest_photos_aweme_nums += 1
                    all_user_new_photos_aweme += 1
            # 有视频aweme，则写入txt，并下载视频
            if user_latest_videos_aweme_nums > 0:
                # 写入txt
                update_user_videos(user, videos)
                # 下载视频
                download_new_videos(
                    user, user_latest_videos_aweme_nums, [logger, logger2], os, sys)
            # 有图片aweme，则下载
            if user_latest_photos_aweme_nums > 0:
                for aweme in user_latest_photos_aweme:
                    download_photo_aweme(aweme, user)
            logger.info(f'{user}新增了{user_latest_aweme_nums}个作品')
            infos = "其中有:"
            if user_latest_videos_aweme_nums > 0:
                infos += f"{user_latest_videos_aweme_nums}个视频作品"
            if user_latest_photos_aweme_nums > 0:
                infos += f"{user_latest_photos_aweme_nums}个图片作品"
            logger.info(infos)
        else:
            logger.info(f'{user}没有最新的作品')
        logger.info(user + f"完成,还剩{usernum - i}个\n")
    alluser_new_video_aweme_num = all_user_new_aweme - all_user_new_photos_aweme
    if all_user_new_aweme > 0:
        infos = f'本次任务一共下载了{all_user_new_aweme}个作品,其中'
        if alluser_new_video_aweme_num > 0:
            infos += f"{alluser_new_video_aweme_num}个视频作品，"
        if all_user_new_photos_aweme > 0:
            infos += f"{all_user_new_photos_aweme}个图片作品，"
        infos += "它们是：\n"
        for latest in latests:
            infos += latest + "\n"
        logger.info(infos)
