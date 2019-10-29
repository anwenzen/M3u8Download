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
    res.close()
    TS_LIST = []
    SUM = 0
    NewFile = open("./" + DIR + "/playlist.m3u8", 'w')
    for line in open("./" + DIR + "/" + NAME, 'r'):
        if "#" in line:
            NewFile.writelines(line)
            continue
        if re.search(r'^http', line) != None:
            NewFile.writelines(str(SUM) + ".ts\n")
            SUM += 1
            TS_LIST.append(line)
            continue
        if re.search(r'^/', line) != None:
            NewFile.writelines(str(SUM) + ".ts\n")
            SUM += 1
            frontURL = re.search(r'https?://.*?/', URL)
            TS_LIST.append(frontURL.group() + line.split('/',1)[-1])
            continue
        NewFile.writelines(str(SUM) + ".ts\n")
        SUM += 1
        frontURL = URL.rsplit("/",1)[0]
        TS_LIST.append(frontURL + line)
    return TS_LIST


def REQUEST(URL, DIR, Name):
    try:
        if not os.path.exists("./" + DIR + "/" + Name):
            res = requests.get(URL, stream=True)
            if res.status_code == 200:
                with open("./" + DIR + "/" + Name, "wb") as ts:
                    for chunk in res.iter_content(chunk_size=1024):
                        if chunk:
                            ts.write(chunk)
            else:
                print("下载" + URL + "失败", end='\n')
            res.close()
    except ConnectionError:
        print("下载" + URL + "失败", end='\n')


# 下载.ts
def Download(TS_LIST, DIR, I):
    for LIST in TS_LIST:
        REQUEST(LIST, DIR, str(I) + ".ts")
        I += 1


class myThread(threading.Thread):  # 继承父类threading.Thread
    def __init__(self, Id, List, dir0, I):
        threading.Thread.__init__(self)
        self.ID = Id
        self.List = List
        self.dir = dir0
        self.i = I

    def run(self):  # 把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        print("线程：" + str(self.ID) + "开始", end="\n")
        Download(self.List, self.dir, self.i)
        print("线程：" + str(self.ID) + "结束", end="\n")


def Start(URL, NAME, SUM=""):
    DIR = NAME.split(".")[0]
    TS_LIST = Get(DIR, NAME, URL)
    length = len(TS_LIST)

    # 线程数（实际线程数 >= Threads）
    # 不要盲目加大，过大会造成服务器没反应，或者被黑
    Threads = 16
    L = int((length - (length % Threads)) / Threads)
    i, ID = 0, 1
    while True:
        myThread(ID, TS_LIST[i: i + L], DIR, i).start()
        ID += 1
        i += L
        if i < length <= i + L:
            myThread(ID, TS_LIST[i:], DIR, i).start()
            break


if __name__ == "__main__":
    # 完整的m3u8文件链接  如："https://www.bilibili.com/ACHED/A0001.m3u8"
    m3u8URL = "https://api.nmbaojie.com/api/data/lem3u8/31641683.m3u8"
    # 保存m3u8的文件名  如："index.m3u8"
    m3u8NAME = "index.m3u8"
    Start(m3u8URL, m3u8NAME)
