import os
import re
import sys
import time
import xlwings as xw
import requests
from utils import get_downloadurl

headers = {
    'authority': 'api.amemv.com',
    'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'zh-CN,zh;q=0.9,en-GB;q=0.8,en;q=0.7'
}


def save_video(user, aweme_id, desc, video_content):
    if user is None:
        path = 'F:/douyin/favorite'
    else:
        path = 'F:/douyin/' + user
    if not os.path.exists(path):
        os.mkdir(path)
    if desc is None or desc == "":
        filename = aweme_id + "_"
    else:
        filename = aweme_id + "_" + desc
    savepath = path + "/" + filename + ".mp4"
    with open(savepath, mode='wb') as f:
        f.write(video_content)
    if os.path.getsize(savepath) < 2:
        print(aweme_id + "\t下载出错，文件大小不正常，建议检查下程序")
        os.remove(savepath)
        sys.exit(0)


def download_video(src, aweme_id, desc, author):
    try:
        resp = requests.get(
            url=src,
            stream=True,
            headers=headers,
            timeout=10000).content
    except ConnectionError as e:
        print(e.args)
    else:
        save_video(author, aweme_id, desc, resp)
        print(aweme_id + "下载完成")


def download_from_excel():
    done = []
    for root, dirs, file in os.walk(r'F:\douyin', topdown=False):
        for name in file:
            done.append(name[0:19])
    wb = xw.Book('douyin.xlsx')
    sheets = wb.sheets
    for sheet in sheets:
        author = sheet.name
        print(author)
        i = 1
        while True:
            src = sheet.range((i, 3)).value
            aweme_id = sheet.range((i, 1)).value
            desc = sheet.range((i, 2)).value
            if aweme_id not in done:
                download_video(src, aweme_id, desc, author)
            i += 1
            if sheet.range((i, 3)).value is None:
                break
    wb.close()


def download_from_txt():
    followers = [follower[0:-4] for follower in os.listdir('followers/')]
    for follower in followers:
        done = []
        try:
            done += [video[0:19]
                    for video in os.listdir(fr'F:\douyin\{follower}')]
        except BaseException:
            pass
        print(f"{follower}已经下载的视频有{len(done)}个")
        videos = [
            video.rstrip() for video in open(
                f'followers/{follower}.txt',
                encoding='utf-8').readlines()]
        for video in videos:
            try:
                aweme_id, desc, src = video.split("==")
            except BaseException:
                video_split = video.split("==")
                aweme_id = video_split[0]
                src = video_split[-1]
                desc = str(video_split[21:-2 - len(src)])
            if aweme_id not in done:
                print(src)
                print(follower, aweme_id, desc, end='\t')
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
                        rurl = get_downloadurl(aweme_id)
                        if rurl is not None:
                            break
                    print(rurl)
                    response = requests.get(
                        url=rurl,
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Android 5.1.1; Mobile; rv:68.0) Gecko/68.0 Firefox/68.0',
                        },
                    )
                save_video(follower, aweme_id, desc, response.content)
                print("下载完成")
                done.append(aweme_id)
            # else:
            #     print(aweme_id + "已经下载过")


def download_favorite():
    favorites = [item[0:19] for item in os.listdir(r"F:\douyin\favorite")]
    for video in open('favorite.txt', encoding='utf-8'):
        aweme_id, desc, src = video.rstrip().split("==")
        if aweme_id not in favorites:
            print(src)
            print(aweme_id, desc, end='\t')
            while True:
                try:
                    response = requests.get(
                        url=src,
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Android 5.1.1; Mobile; rv:68.0) Gecko/68.0 Firefox/68.0',
                        },
                        timeout=10).content
                except Exception as e:
                    print(e)
                    time.sleep(7)
                else:
                    break
            save_video(None, aweme_id, desc, response)
            print("下载完成")
            favorites.append(aweme_id)


def download_photo(src, i, aweme_id, desc, author_dir):
    filename = aweme_id + "_" + desc + "_" + str(i + 1) + ".jpg"
    filepath = os.path.join(author_dir, filename)
    # 下载过了
    if os.path.exists(filepath):
        # 返回没下载
        return False
    response = requests.get(url=src, headers=headers)
    save_check_photo(filepath, aweme_id, response)
    # 返回下载了
    return True


def download_aweme_photos():
    secid2user = {}
    for line in open('followers.txt', encoding='utf-8'):
        user, sec_uid = line.rstrip().split(':')
        secid2user[sec_uid] = user
    rootdir = r"F:\douyin\images"
    from pymongo import MongoClient
    import json
    client = MongoClient("mongodb://localhost:27017/")
    database = client["douyin"]
    collection = database["followers_videos"]
    images_aweme = collection.find({'aweme_type': 2})
    for aweme in images_aweme:
        aweme_id = aweme['aweme_id']
        author = secid2user[aweme['author']['sec_uid']]
        author_dir = rootdir + os.sep + author
        if not os.path.exists(author_dir):
            os.makedirs(author_dir)
        desc = re.sub('[\\/:*?"<>|\n]', '', aweme['desc'])
        rs = requests.get(
            url='https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={}&dytk='.format(
                aweme_id),
            headers=headers,
            timeout=5).text
        response_json = json.loads(rs)
        if len(response_json['item_list']) == 0:
            continue
        aweme_images = response_json['item_list'][0]['images']
        if aweme_images is None:
            download_photo(
                src=response_json['item_list'][0]['image_infos'][0]['label_large']['url_list'][0],
                i=0,
                aweme_id=aweme_id,
                desc=desc,
                author_dir=author_dir)
            continue
        for i in range(len(aweme_images)):
            download_photo(
                src=aweme_images[i]['url_list'][0],
                i=i,
                aweme_id=aweme_id,
                desc=desc,
                author_dir=author_dir)


def save_check_photo(filepath, aweme_id, response):
    with open(filepath, mode='wb') as f:
        try:
            f.write(response.content)
            print(filepath + "\t下载完成")
        except Exception as e:
            print(aweme_id + "\t下载图片出错")
            print(e)
    if os.path.getsize(filepath) < 2:
        print(aweme_id + "\t下载出错，文件大小不正常，建议检查下程序")
        os.remove(filepath)
        sys.exit(0)


if __name__ == '__main__':
    download_favorite()
    download_from_txt()
    # download_from_excel()
    download_aweme_photos()
