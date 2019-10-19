# -*- coding: UTF-8 -*-

import m3u8Download
import os


# 尝试下载失败列表
def tryDownload(DIR):
    for LIST in open("./" + DIR + "/ErrorList01.txt", "r"):
        m3u8Download.REQUEST(LIST.split("\n")[0], DIR, ErrorFile="/ErrorList02.txt")


# 合并，需要ffmpeg
# 如果需要key，key的链接在 m3u8 文件中，如 #EXT-X-KEY:METHOD=AES-128,URI="ACHED/key.key"
# 1⃣ 下载放到同一目录下，并修改为路径 如：URI="key.key"
# 2⃣ 补全 如：URL="https://www.bilibili.com/ACHED/key.key" ，合并需要网络
def FFMPEG(DIR):
    Input = "./" + DIR + "/playlist.m3u8"
    Output = "./" + DIR + "/playlist.mp4"
    CMD = "ffmpeg -allowed_extensions ALL -i " + Input + " -acodec copy -vcodec copy -f mp4 " + Output
    os.system(CMD)


if __name__ == "__main__":
    # 文件夹
    Folder = ""
    tryDownload(Folder)
    FFMPEG(Folder)
