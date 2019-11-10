# -*- coding: UTF-8 -*-

from concurrent.futures import ThreadPoolExecutor
import os
import requests
import re

# 下载.m3u8   获取 .ts链接以及.key链接 
def Get(DIR, URL, TsURL=""):
    if not os.path.exists("./" + DIR):
        os.mkdir("./" + DIR)

    res = requests.get(URL)
    with open("./" + DIR + "/" + DIR, 'wb') as f:
        f.write(res.content)
    res.close()
    TS_LIST = []
    SUM = 0
    NewFile = open("./" + DIR + "/new_" + DIR + ".m3u8", 'w')
    for line in open("./" + DIR + "/" + DIR, 'r'):
        if "#" in line:
            if "EXT-X-KEY" in line:
                NewFile.writelines(Download_KEY(URL, DIR, line))
                continue
            NewFile.writelines(line)
            continue
        elif re.search(r'^http', line) != None:
            NewFile.writelines("w_" + str(SUM) + ".ts\n")
            SUM += 1
            TS_LIST.append(line)
            continue
        elif re.search(r'^/', line) != None:
            NewFile.writelines("w_" + str(SUM) + ".ts\n")
            SUM += 1
            frontURL = re.search(r'https?://.*?/', URL)
            TS_LIST.append(frontURL.group() + line.split('/',1)[-1])
            continue
        else:
            NewFile.writelines("w_" + str(SUM) + ".ts\n")
            SUM += 1
            frontURL = URL.rsplit("/",1)[0]
            TS_LIST.append(frontURL + '/' + line)
            continue
        print("如果你看见这个，说明没有正确找到 .ts 的URL")
    return TS_LIST


# 下载 .ts 文件
def Download(URL, DIR, Name):
    URL = URL.split('\n')[0]
    try:
        if not os.path.exists("./" + DIR + "/" + Name):
            print("下载\t./" + DIR + "/" + Name + "\t开始")
            res = requests.get(URL, stream=True)
            if res.status_code == 200:
                with open("./" + DIR + "/" + Name, "wb") as ts:
                    for chunk in res.iter_content(chunk_size=1024):
                        if chunk:
                            ts.write(chunk)
                print("下载\t./" + DIR + "/" + Name + "\t完成")
            else:
                print("下载 " + URL + " 失败")
            res.close()
    except ConnectionError:
        print("下载 " + URL + " 失败")


# 下载 .key 文件
def Download_KEY(URL, DIR, LINE):
    str1 = r"URI=[\'|\"].*?[\'|\"]"
    key = re.search(str1, LINE).group()[5:-1]

    if re.search(r'^http', key) != None:
        key_URL = key
    elif re.search(r'^/', key) != None:
        key_URL = re.search(r'https?://.*?/', URL).group() + key.split('/', 1)[-1]
    else:
        key_URL = URL.rsplit("/",1)[0] + '/' + key
    res = requests.get(key_URL)
    with open("./" + DIR + "/key.key", 'wb') as f:
        f.write(res.content) 
    res.close()

    new_result = LINE[0:re.search(str1, LINE).start()] + 'URI="key.key"' + LINE[re.search(str1, LINE).end():]
    return new_result


# 合并视频，需要ffmpeg
def FFMPEG(DIR):
    Input = "./" + DIR + "/new_" + DIR + ".m3u8"
    Output = "./" + DIR + "/new_" + DIR + ".mp4"
    CMD = "ffmpeg -allowed_extensions ALL -i " + Input + " -acodec copy -vcodec copy -f mp4 " + Output
    os.system(CMD)


def Start(URL, DIR, THREAD):
    TS_LIST = Get(DIR, URL)
    
    ID = 0
    with ThreadPoolExecutor(THREAD) as threadpool:
        for TS in TS_LIST:
            threadpool.submit(Download, TS, DIR, "w_"+str(ID)+".ts")
            ID += 1
        threadpool.shutdown(wait=False)
    FFMPEG(DIR)
    print("合并完成")


if __name__ == "__main__":
    # 完整的m3u8文件链接  如："https://www.bilibili.com/example/index.m3u8"
    URL = "https://www.bilibili.com/example/index.m3u8"
    # 保存m3u8的文件名夹  如："index"
    DIR = "index"
    # 线程数，网速跟不上再大也没用。不要盲目加大
    THR = 64
    Start(URL, DIR, THR)
