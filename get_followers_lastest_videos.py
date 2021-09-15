# 获取各个正在关注人最新发布的几个视频
from utils import write2mongodb
from utils import write2mysql
import requests
import re
import json
from utils import log2file
from utils import get_database_videos
from utils import datas_process
from utils import db, cursor
from utils import get_downloadurl
logger = log2file('download.log', 'a', time=True)
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
        db,
        cursor,
        mysql_data)
    # 将windows中文件名不支持的字符删除
    desc = re.sub(
        '[\\\\/:*?"<>|\n]',
        '',
        response_json['item_list'][0]['desc'])
    src = get_downloadurl(aweme_id)
    return desc, src


# 更新文件写入新的视频
def update_user_videos(user, videos):
    with open(f'followers/{user}.txt', mode='w', encoding='utf-8') as f:
        for video in videos:
            f.write(video)
            f.write('\n')


def download_new_videos(user, number):
    path = 'F:/douyin/' + user
    videos = open(f'followers/{user}.txt',
                  encoding='utf-8').readlines()[:number]
    for video in videos:
        aweme_id, desc, src = video.rstrip().split("==")
        filename = aweme_id + "_" + desc
        savepath = path + "/" + filename + ".mp4"
        response = requests.get(
            url=src,
            headers={
                'User-Agent': 'Mozilla/5.0 (Android 5.1.1; Mobile; rv:68.0) Gecko/68.0 Firefox/68.0',
            },
            timeout=10).content
        with open(savepath, 'wb') as f:
            f.write(response)
            logger.info(video[0:19] + "\t下载完成")


def main():
    mysql_data, mongodb_data = get_database_videos()
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
        response = requests.get(
            f"https://www.douyin.com/user/{sec_uid}",
            headers=headers)
        new_aweme_ids = re.findall(
            'href="https://www.douyin.com/video/(\\d{1,19})',
            response.text)
        for new_aweme_id in new_aweme_ids:
            if new_aweme_id not in aweme_ids:
                desc, src = get_desc_src(
                    new_aweme_id, mysql_data, mongodb_data, user)
                video = new_aweme_id + " == " + desc + " == " + src
                videos.insert(0, video)
                add_new += 1
        f.close()
        update_user_videos(user, videos)
        logger.info(len(new_aweme_ids))
        if add_new > 0:
            download_new_videos(user, add_new)
            logger.info(f'{user}新增了{add_new}个视频')
    logger.info("*" * 80 + '\n')


if __name__ == '__main__':
    main()
