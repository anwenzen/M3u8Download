# -*- coding: UTF-8 -*-

from concurrent.futures import ThreadPoolExecutor
import os
import requests
import re
import shutil

sum_Front = 0   #记录下载成功的 .ts 文件个数
sum_Next = 0    #记录一个 .m3u8 文件含有 .ts 文件的个数


# 下载.m3u8   获取 .ts链接以及 .key链接
def Get(DIR, URL, TsURL=""):
    global sum_Next
    if not os.path.exists(f"./{DIR}"):
        os.mkdir(f"./{DIR}")
        os.mkdir(f"./{DIR}/ts")

    res = requests.get(URL)
    with open(f"./{DIR}/ts/{DIR}.m3u8", 'wb') as f:
        f.write(res.content)
    res.close()
    TS_LIST = []
    NewFile = open(f"./{DIR}/new_{DIR}.m3u8", 'w')
    for line in open(f"./{DIR}/ts/{DIR}.m3u8", 'r'):
        if "#" in line:
            if "EXT-X-KEY" in line:
                NewFile.writelines(Download_KEY(URL, DIR, line))
                continue
            NewFile.writelines(line)
            continue
        elif re.search(r'^http', line) != None:
            sum_Next += 1
            NewFile.writelines(f"./ts/w_{sum_Next}.ts\n")
            TS_LIST.append(line)
            continue
        elif re.search(r'^/', line) != None:
            sum_Next += 1
            NewFile.writelines(f"./ts/w_{sum_Next}.ts\n")
            frontURL = re.search(r'https?://.*?/', URL)
            TS_LIST.append(frontURL.group() + line.split('/', 1)[-1])
            continue
        else:
            sum_Next += 1
            NewFile.writelines(f"./ts/w_{sum_Next}.ts\n")
            frontURL = URL.rsplit("/", 1)[0]
            TS_LIST.append(frontURL + '/' + line)
            continue
    return TS_LIST


# 下载 .ts 文件
def Download(URL, DIR, Name):
    global sum_Front, sum_Next
    URL = URL.split('\n')[0]
    try:
        if not os.path.exists(f"./{DIR}/ts/{Name}"):
            res = requests.get(URL, stream=True, timeout=(5, 60))       # ConnectTimeout= 5 s     ReadTimeout= 60 s
            if res.status_code == 200:
                with open(f"./{DIR}/ts/{Name}", "wb") as ts:
                    for chunk in res.iter_content(chunk_size=1024):
                        if chunk:
                            ts.write(chunk)
                sum_Front += 1
                print(f"\r下载进度：\t{sum_Front}/{sum_Next}", end="")
            else:
                print(f"下载./{DIR}/ts/{Name}失败, [服务器响应码status_code!=200]")
            res.close()

    except Exception:
        if os.path.exists(f"./{DIR}/ts/{Name}"):
            os.remove(f"./{DIR}/ts/{Name}")
        print(f"下载./{DIR}/ts/{Name}失败,连接或下载超时")


# 下载 .key 文件
def Download_KEY(URL, DIR, LINE):
    str1 = r"URI=[\'|\"].*?[\'|\"]"
    key = re.search(str1, LINE).group()[5:-1]

    if re.search(r'^http', key) != None:
        key_URL = key
    elif re.search(r'^/', key) != None:
        key_URL = re.search(r'https?://.*?/', URL).group() + key.split('/', 1)[-1]
    else:
        key_URL = URL.rsplit("/", 1)[0] + '/' + key
    try:
        res = requests.get(key_URL)
        with open(f"./{DIR}/ts/key.key", 'wb') as f:
            f.write(res.content)
        res.close()
    except Exception:
        print("如果你看见这个，证明 .key文件 没有下载成功，并且这个视频属于加密的视频，请手动下载并改名，放在途径为 ./ts/key.key")
    new_result = LINE[0:re.search(str1, LINE).start()] + 'URI="./ts/key.key"' + LINE[re.search(str1, LINE).end():]
    return new_result


# 合并视频，需要ffmpeg
def FFMPEG(DIR):
    Input = f"./{DIR}/new_{DIR}.m3u8"
    Output = f"./{DIR}/{DIR}.mp4"
    CMD = f"ffmpeg -allowed_extensions ALL -i {Input} -acodec copy -vcodec copy -f mp4 {Output}"
    print(f"\n{'合并开始':=^20}")
    os.system(CMD)
    print(f"\n{'合并完成':=^20}")


def Main(URL, DIR, THREAD):
    global sum_Front, sum_Next
    TS_LIST = Get(DIR, URL)
    ID = 0
    trytimes = 0
    for trytimes in range(0, 3):    # 3 次重试
        with ThreadPoolExecutor(THREAD) as threadpool:
            for TS in TS_LIST:
                ID += 1
                threadpool.submit(Download, TS, DIR, f"w_{ID}.ts")
            threadpool.shutdown(wait=False)
        if sum_Front == sum_Next:
            FFMPEG(DIR)
            shutil.rmtree(f"./{DIR}/ts")  # 合并成功后，删除 .ts 文件
            os.remove(f"./{DIR}/new_{DIR}.m3u8")  # 合并成功后，删除 .m3u8 文件
            break
        print(f"\n第{trytimes}次重试中")


if __name__ == "__main__":
    # 完整的m3u8文件链接  如：URL = "https://www.bilibili.com/example/index.m3u8"
    URL = input("输入URL：")
    # 保存m3u8的文件名夹  如：DIR = "index"
    DIR = input("输入文件夹名：")
    # 线程数，你的网速、服务器的网速跟不上，再大也没用。不要盲目加大
    THR = 64
    Main(URL, DIR, THR)
