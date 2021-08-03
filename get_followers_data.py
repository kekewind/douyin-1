# 获取正在关注的人的所有上传视频
import requests
import re
import xlwings as xw
import pymysql
app = xw.App(visible=False, add_book=False)
wb = app.books.add()


def get_data(sec_uid, signature, max_cursor):
    url = f'https://www.iesdouyin.com/web/api/v2/aweme/post/?sec_uid={sec_uid}&count=21&max_cursor={max_cursor}&aid=1128&_signature={signature}&dytk='
    headers = {
        'accept': 'application/json',
        'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
    }
    response = requests.request("GET", url, headers=headers)
    return response.json()


def get_one_page(sec_uid, max_cursor):
    page_data = []
    signature = requests.get('http://localhost:3000/sign').text
    data_json = get_data(sec_uid, signature, max_cursor)
    if data_json and 'aweme_list' in data_json.keys():
        aweme_list = data_json['aweme_list']
        for item in aweme_list:
            if item['aweme_type'] == 4:
                aweme_id = item['aweme_id']
                vid = item['video']['vid']
                temp_src = item['video']['download_addr']['url_list'][0]
                src = re.sub('&watermark=1', '&watermark=0', temp_src, re.S)
                desc = re.sub('[\\/:*?"<>|\n]', '', item['desc'])
                page_data.append([aweme_id, vid, desc, src])

    try:
        iscontinue = data_json['has_more']
    except BaseException:
        print('keyerror')
    else:
        if iscontinue:
            return page_data, data_json['max_cursor']
        else:
            return page_data, None


def get_videos(sec_uid):
    max_cursor = 0
    all_data = []
    while True:
        page_data, max_cursor = get_one_page(sec_uid, max_cursor)
        all_data += page_data
        print(len(all_data))
        if not max_cursor:
            break
    return all_data


def write2txt(datas, user):
    with open(f'followers/{user}.txt', mode='w', encoding='utf-8') as f:
        for video in datas:
            f.write(video[0] + "==" + video[1] + "==" + video[2])
            f.write('\n')


def write2excel(data, user):
    active_sheet = wb.sheets.add(user)
    active_sheet.range("A:A").api.NumberFormat = "@"
    for i in range(len(data)):
        for j in range(len(data[i])):
            active_sheet.range((i + 1, j + 1)).value = data[i][j]


def connetmysql():
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
    cursor = db.cursor()
    sql = f'drop table if exists followers_datas'
    cursor.execute(sql)
    # page_data.append([aweme_id, vid, desc, src])
    create_table = f"""CREATE TABLE followers_datas (
                    author varchar(50) comment '作者',
                    aweme_id varchar(25),
                    vid varchar(100),
                    description varchar(255),
                    src varchar(255),
                    primary key (aweme_id))"""
    cursor.execute(create_table)
    return db, cursor


def write2mysql(datas, username, db, cursor):
    for data in datas:
        inser_sql = "insert into followers_datas values('{user}',{data})".format(
            user=username, data=str(data)[1:-1])
        try:
            cursor.execute(inser_sql)
            db.commit()
        except BaseException:
            db.rollback()


if __name__ == "__main__":
    user_secid = []
    with open('followers.txt', encoding='utf-8') as f:
        for item in f.readlines():
            user_secid.append(item.rstrip())
    db, cursor = connetmysql()
    for item in user_secid:
        user, sec_id = item.split(':')
        print(user, sec_id)
        try:
            user_data = get_videos(sec_id)
        except Exception as e:
            print(e)
            print(user + "has error")
        else:
            if len(user_data) > 0:
                write2excel(user_data, user)
                write2txt(user_data, user)
                write2mysql(user_data, user, db, cursor)
    cursor.close()
    db.close()
    del wb.sheets['Sheet1']
    wb.save('videos.xlsx')
    wb.close()
    app.quit()
