# 获取最新关注所有的作品
import json
import os
import re
import sys
import time
import requests
from utils import write2mysql
from utils import write2excel
from utils import datas_process
from utils import write2mongodb
from utils import write2txt
from download import save_check_photo
rootdir = r'F:\douyin\images'


class douyin():
    def __init__(self, url):
        self.url = url
        self.user_all_awemes = []
        self.awemes_num = 0
        self.video_aweme_num = 0
        self.photo_aweme_num = 0
        self.user_video_aweme = []
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'referer': 'https://www.douyin.com/',
        }

    def start(self):
        username, sec_id = self.get_username_secuid()
        print(f'这个人用户名是：{username}')
        _ = input("请输入自定义名称，输入enter表示不需要自定义\n-->")
        if _ == '':
            pass
        else:
            username = _
        self.get_user_awemes(username, sec_id)
        if len(self.user_all_awemes) > 0:
            for aweme in self.user_all_awemes:
                if aweme['aweme_type'] == 4:
                    aweme_id = aweme['aweme_id']
                    desc = re.sub('[\\/:*?"<>|\n]', '', aweme['desc'])
                    src = re.sub(
                        'watermark=1',
                        'watermark=0',
                        aweme['video']['download_addr']['url_list'][1])
                    self.save_video_aweme(username, aweme_id, desc, src)
                    self.user_video_aweme.append(aweme)
                    self.video_aweme_num += 1
                if aweme['aweme_type'] == 2:
                    aweme_id = aweme['aweme_id']
                    desc = re.sub('[\\/:*?"<>|\n]', '', aweme['desc'])
                    author_dir = rootdir + os.sep + username
                    if not os.path.exists(author_dir):
                        os.makedirs(author_dir)
                    rs = requests.get(
                        url='https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={}&dytk='.format(
                            aweme_id),
                        headers=self.headers,
                        timeout=5).text
                    response_json = json.loads(rs)
                    aweme_images = response_json['item_list'][0]['images']
                    if aweme_images is None:
                        self.download_save_photo(
                            src=response_json['item_list'][0]['image_infos'][0]['label_large']['url_list'][0],
                            i=0,
                            aweme_id=aweme_id,
                            desc=desc,
                            author_dir=author_dir)
                        continue
                    for i in range(len(aweme_images)):
                        self.download_save_photo(
                            src=aweme_images[i]['url_list'][0],
                            i=i,
                            aweme_id=aweme_id,
                            desc=desc,
                            author_dir=author_dir)
                    self.photo_aweme_num += 1
        self.update_database(username, sec_uid=sec_id)
        print(f'{username}下载完成，一共有{len(self.user_all_awemes)}个作品')
        print(f'其中有{self.video_aweme_num}个视频作品')
        if self.photo_aweme_num > 0:
            print(f'有{self.photo_aweme_num}个图片作品')
        else:
            print(f'没有图片作品')

    def get_username_secuid(self):
        # 获取用户名和sec_id
        while True:
            while True:
                try:
                    response = requests.get(
                        url=self.url,
                        headers=self.headers)
                except Exception as e:
                    time.sleep(8)
                else:
                    break
            if response.text.startswith('<!DOCTYPE html>'):
                break
            time.sleep(8)
        sec_uid = re.search('/user/(.*)\\?', response.url).group(1)
        username = re.search(
            '<title data-react-helmet="true">([\\s\\S]*?)</title>',
            response.text).group(1)[
            0:-8]
        return username, sec_uid

    def get_user_awemes(self, username, sec_uid):
        # 获取用户所有的awemes
        print(f"正在获取{username}的所有作品")
        max_cursor = 0
        while True:
            page_data, max_cursor = self.get_one_page_info(sec_uid, max_cursor)
            self.user_all_awemes += page_data
            print(len(self.user_all_awemes))
            if not max_cursor:
                break
        print(f"获取{username}的所有作品结束")

    def get_one_page_info(self, sec_uid, max_cursor):
        # 获取用户名一页的信息（包括一页的awme list和是否继续获取下一页）
        page_aweme = []
        signature = requests.get('http://8.9.15.155:3000/sign').text
        data_json = self.get_one_page_aweme(
            sec_uid, signature, max_cursor)
        if data_json and 'aweme_list' in data_json.keys():
            page_aweme = data_json['aweme_list']
        try:
            iscontinue = data_json['has_more']
        except BaseException:
            print("服务器错误，请求再来一遍")
            return page_aweme, max_cursor
        else:
            if iscontinue:
                return page_aweme, data_json['max_cursor']
            else:
                return page_aweme, None

    def get_one_page_aweme(self, sec_uid, signature, max_cursor):
        # 获取用户名一页的aweme
        url = f'https://www.iesdouyin.com/web/api/v2/aweme/post/?sec_uid={sec_uid}&count=21&max_cursor={max_cursor}&aid=1128&_signature={signature}&dytk='
        headers = {
            'accept': 'application/json',
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
        }
        response = requests.request("GET", url, headers=headers)
        return response.json()

    def save_video_aweme(self, username, aweme_id, desc, src):
        # 下载和保存video型的aweme
        video_response = self.download_video(aweme_id, src)
        self.save_video(username, aweme_id, desc, video_response)

    def download_video(self, aweme_id, src):
        # 下载视频
        print(aweme_id, end='\t')
        while True:
            try:
                response = requests.get(
                    url=src,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Android 5.1.1; Mobile; rv:68.0) Gecko/68.0 Firefox/68.0',
                    },
                    timeout=10)
            except Exception as e:
                print(e)
                time.sleep(6)
            else:
                break
        if response.status_code == 403:
            print(
                "\n" +
                aweme_id +
                "的下载url地址有问题，获取新的下载url地址",
                end='\t')
            while True:
                rurl = self.get_downloadurl(aweme_id)
                if rurl is not None:
                    break
            print(rurl)
            response = requests.get(
                url=rurl,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Android 5.1.1; Mobile; rv:68.0) Gecko/68.0 Firefox/68.0',
                },
            )
        return response

    def get_downloadurl(self, aweme_id):
        # 获取视频aweme新的下载地址
        data = {
            'url': 'https://www.douyin.com/video/{}'.format(aweme_id)
        }
        response = requests.post(
            'https://www.daimadog.com/wp-content/themes/mytheme/action/dyjx.php',
            data=data)
        return response.json()['playurl']

    # 保存视频到本地
    def save_video(self, username, aweme_id, desc, video):
        if username is None:
            path = 'F:/douyin/favorite'
        else:
            path = 'F:/douyin/' + username
        if not os.path.exists(path):
            os.mkdir(path)
        if desc is None or desc == "":
            filename = aweme_id + "_"
        else:
            filename = aweme_id + "_" + desc
        savepath = path + "/" + filename + ".mp4"
        with open(savepath, mode='wb') as f:
            f.write(video.content)
        if os.path.getsize(savepath) < 2:
            print(aweme_id + "\t下载出错，文件大小不正常，建议检查下程序")
            os.remove(savepath)
            sys.exit(0)
        print(desc, '下载完成，文件保存在：' + savepath)

    def download_save_photo(self, src, i, aweme_id, desc, author_dir):
        filename = aweme_id + "_" + desc + "_" + str(i + 1) + ".jpg"
        savepath = os.path.join(author_dir, filename)
        # 下载过了
        if os.path.exists(savepath):
            return
        response = requests.get(url=src, headers=self.headers)
        save_check_photo(savepath,aweme_id,response)
        print(filename, '图片下载完成，文件保存在：' + savepath)

    def update_database(self, username, sec_uid):
        videos_data, photo_aweme_num = datas_process(self.user_all_awemes)
        write2excel(videos_data, username)
        write2txt(videos_data, username)
        write2mysql(videos_data, username, [])
        if len(self.user_all_awemes) > 0:
            write2mongodb(self.user_all_awemes, [])
        followers = [
            line.rstrip() for line in open(
                'followers.txt',
                encoding='utf-8').readlines()]
        followers.insert(0, username + ":" + sec_uid)
        with open('followers.txt', encoding='utf-8', mode='w') as f:
            for follower in followers:
                f.write(follower)
                f.write('\n')


if __name__ == '__main__':
    print("请输入分享地址url，形如：https://v.douyin.com/dBMSvq1/ \n"
          "或者 https://www.douyin.com/user/MS4wLjABAAAA9ZT9Oi0o4cnYo-u7ndgkToQyRmLup5YDgzEQLb-5WCrUWWiRZEI3xBuNG5QkMcOf?previous_page=app_code_link")
    while True:
        url = input('-->')
        douyin(url).start()
        print("开始下一个，请继续输入分享主页，如果不需要请关闭程序")
