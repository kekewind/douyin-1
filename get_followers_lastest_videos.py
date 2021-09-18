# 获取各个正在关注人最新发布的几个视频
import os
import sys
import time
from utils import write2mongodb
from utils import write2mysql
from utils import log2file
from utils import get_database_videos
from utils import datas_process
from utils import get_downloadurl
from utils import update_user_videos
from utils import download_new_videos
import requests
import re
import json
logger = log2file('main', '获取关注们最新的视频', ch=True, mode='w', time=True)
logger2 = log2file('dwoload', '下载', mode='a')
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'referer': 'https://www.douyin.com/', }


def get_desc_src(aweme_id, mysql_data, mongodb_data, user):
    response = requests.get(
        url='https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={}&dytk='.format(aweme_id), headers=headers,
        timeout=5).text
    response_json = json.loads(response)
    # 将新的作品写入到mysql和mongodb
    write2mongodb(response_json['item_list'], mongodb_data)
    write2mysql(
        datas_process(
            response_json['item_list'])[0],
        user,
        mysql_data)
    # 将windows中文件名不支持的字符删除
    desc = re.sub(
        '[\\\\/:*?"<>|\n]',
        '',
        response_json['item_list'][0]['desc'])
    src = get_downloadurl(aweme_id)
    return desc, src


def main():
    mysql_data, mongodb_data = get_database_videos()
    logger.info('开始这次任务，获取所有关注的最新视频')
    for line in open('followers.txt', encoding='utf-8'):
        add_new = 0
        user, sec_uid = line.rstrip().split(':')
        logger.info(user + " start")
        try:
            f = open(f'followers/{user}.txt', encoding='utf-8')
        except BaseException:
            continue
        aweme_ids = [video[0:19] for video in f.readlines()]
        videos = [
            video.rstrip() for video in open(
                f'followers/{user}.txt',
                encoding='utf-8').readlines()]
        while True:
            response = requests.get(
                f"https://www.douyin.com/user/{sec_uid}",
                headers=headers)
            if response.text.startswith('<!DOCTYPE html>'):
                break
            time.sleep(3)
        new_aweme_ids = re.findall(
            'href="https://www.douyin.com/video/(\\d{1,19})',
            response.text)
        logger.info(len(new_aweme_ids))
        for new_aweme_id in new_aweme_ids:
            if new_aweme_id not in aweme_ids:
                desc, src = get_desc_src(
                    new_aweme_id, mysql_data, mongodb_data, user)
                video = new_aweme_id + " == " + desc + " == " + src
                videos.insert(0, video)
                add_new += 1
        f.close()
        # 将新的视频写入txt
        update_user_videos(user, videos)
        if add_new > 0:
            download_new_videos(user, add_new, [logger, logger2], os, sys)
            logger.info(f'{user}新增了{add_new}个视频')
        else:
            logger.info(f'{user}没有新增视频')
    logger.info('任务结束')
    logger.info("*" * 80 + '\n')


if __name__ == '__main__':
    main()
