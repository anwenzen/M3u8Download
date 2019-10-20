# -*- coding: UTF-8 -*-

import os
import threading
import requests
import re


# 下载.m3u8
def Get(DIR, NAME, URL, TsURL=""):
    if not os.path.exists("./" + DIR):
        os.mkdir("./" + DIR)

    res = requests.get(URL)
    with open("./" + DIR + "/" + NAME, 'wb') as f:
        f.write(res.content)
    TS_LIST = []
    NewFile = open("./" + DIR + "/playlist.m3u8", 'w')
    for line in open("./" + DIR + "/" + NAME, 'r'):
        if "#" in line:
            NewFile.writelines(line)
            continue
        result = re.search(r"(.*)\.ts",line).group().rsplit("/")[-1]
        NewFile.writelines(result + "\n")
        TS = (line.rsplit("\n", 1)[0]).rsplit("/", 1)[-1]
        TS = TsURL + TS
        TS_LIST.append(TS)
    res.close()
    return TS_LIST


def REQUEST(LIST, DIR, ErrorFile="/ErrorList01.txt"):
    try:
        if not os.path.exists("./" + DIR + "/" + (LIST.split("\n")[0]).rsplit("/", 1)[-1]):
            res = requests.get(LIST, stream=True)
            if res.status_code == 200:
                result = re.search(r"(http|https)(.*)\.ts",LIST).group().rsplit("/")[-1]
                with open("./" + DIR + "/" + result, "wb") as ts:
                    for chunk in res.iter_content(chunk_size=1024):
                        if chunk:
                            ts.write(chunk)
            else:
                print("下载" + LIST + "失败", end='\n')
                with open("./" + DIR + ErrorFile, "w+") as file:
                    file.writelines(LIST + "\n")
            res.close()
    except ConnectionError:
        print("下载" + LIST + "失败", end='\n')
        with open("./" + DIR + ErrorFile, "w+") as file:
            file.writelines(LIST + "\n")


# 下载.ts
def Download(TS_LIST, DIR):
    for LIST in TS_LIST:
        REQUEST(LIST, DIR)


class myThread(threading.Thread):  # 继承父类threading.Thread
    def __init__(self, Id, List, dir0):
        threading.Thread.__init__(self)
        self.ID = Id
        self.List = List
        self.dir = dir0

    def run(self):  # 把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        print("线程：" + str(self.ID) + "开始", end="\n")
        Download(self.List, self.dir)
        print("线程：" + str(self.ID) + "结束", end="\n")


def Start(URL, NAME, TsURL=""):
    DIR = NAME.split(".")[0]
    TS_LIST = Get(DIR, NAME, URL, TsURL)
    # print(TS_LIST)
    length = len(TS_LIST)

    # 线程数（实际线程数 >= Threads）
    # 不要盲目加大，过大会造成服务器没反应，或者被黑
    Threads = 16
    L = int((length - (length % Threads)) / Threads)
    i, ID = 0, 1
    while True:
        myThread(ID, TS_LIST[i: i + L], DIR).start()
        ID += 1
        i += L
        if i < length <= i + L:
            myThread(ID, TS_LIST[i:], DIR).start()
            break


if __name__ == "__main__":
    # 完整的m3u8文件链接  如："https://www.bilibili.com/ACHED/A0001.m3u8"
    m3u8URL = "https://zy.kubozy-sohu-360-sogou.com/20191012/12689_d9d140b4/1000k/hls/index.m3u8"
    # .ts链接的所有前缀  如： "https://www.bilibili.com/ACHED/A0001.ts" 的 "https://www.bilibili.com/ACHED/"
    tsURL = "https://zy.kubozy-sohu-360-sogou.com/20191012/12689_d9d140b4/1000k/hls/"
    # 保存m3u8的文件名  如："index.m3u8"
    m3u8NAME = "哪吒.m3u8"
    Start(m3u8URL, m3u8NAME, tsURL)
