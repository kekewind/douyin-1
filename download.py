import os
import xlwings as xw
import re
import requests

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
        desc = re.sub('[\\\\/:*?"<>|\n]', '', desc)
        filename = aweme_id + "_" + desc
    savepath = path + "/" + filename + ".mp4"
    with open(savepath, mode='wb') as f:
        f.write(video_content)


def download(src, aweme_id, desc, author):
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
    wb = xw.Book('videos.xlsx')
    sheets = wb.sheets
    for sheet in sheets:
        author = sheet.name
        print(author)
        i = 1
        while True:
            src = sheet.range((i, 4)).value
            aweme_id = sheet.range((i, 1)).value
            desc = sheet.range((i, 3)).value
            if aweme_id not in done:
                download(src, aweme_id, desc, author)
            i += 1
            if sheet.range((i, 4)).value is None:
                break
    wb.close()


def download_from_txt():
    followers = [follower[0:-4] for follower in os.listdir('followers/')]
    for follower in followers:
        try:
            done = [video[0:19]
                    for video in os.listdir(fr'F:\douyin\{follower}')]
        except BaseException:
            done = []
        videos = [
            video.rstrip() for video in open(
                f'followers/{follower}.txt',
                encoding='utf-8').readlines()]
        for video in videos:
            aweme_id, vid, desc = video.split("==")
            if aweme_id not in done:
                print(follower, video, end='\t')
                download_url = 'https://aweme.snssdk.com/aweme/v1/play/?video_id={' \
                               '}&line=0&ratio=720p&media_type=4&vr_type=0&improve_bitrate=0&is_play_url=1&is_support_h265=0&source' \
                               '=PackSourceEnum_PUBLISH'.format(vid)
                response = requests.get(
                    url=download_url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Android 5.1.1; Mobile; rv:68.0) Gecko/68.0 Firefox/68.0',
                    },
                    timeout=10).content
                save_video(follower, aweme_id, desc, response)
                print("下载完成")
                done.append(aweme_id)


def download_favorite():
    favorites = [item[0:19] for item in os.listdir(r"F:\douyin\favorite")]
    for video in open('favorite.txt', encoding='utf-8'):
        aweme_id, vid, desc = video.rstrip().split("==")
        if aweme_id not in favorites:
            print(video.rstrip(), end='\t')
            download_url = 'https://aweme.snssdk.com/aweme/v1/play/?video_id={' \
                           '}&line=0&ratio=720p&media_type=4&vr_type=0&improve_bitrate=0&is_play_url=1&is_support_h265=0&source' \
                           '=PackSourceEnum_PUBLISH'.format(vid)
            response = requests.get(
                url=download_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Android 5.1.1; Mobile; rv:68.0) Gecko/68.0 Firefox/68.0',
                },
                timeout=10).content
            save_video(None, aweme_id, desc, response)
            print("下载完成")
            favorites.append(aweme_id)


if __name__ == '__main__':
    # download_favorite()
    download_from_txt()
    # download_from_excel()
