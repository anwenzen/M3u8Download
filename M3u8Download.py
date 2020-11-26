# _*_ coding: utf-8 _*_
# _*_ author: anwenzen _*_

import os
import re
import sys
import queue
import requests
from concurrent.futures import ThreadPoolExecutor


class ThreadPoolExecutorWithQueueSizeLimit(ThreadPoolExecutor):
    """
    实现多线程有界队列
    队列数为线程数的2倍
    """

    def __init__(self, max_workers=None, *args, **kwargs):
        super().__init__(max_workers, *args, **kwargs)
        self._work_queue = queue.Queue(max_workers * 2)


def make_sum():
    ts_num = 0
    while True:
        yield ts_num
        ts_num += 1


class M3u8Download:
    """
    :param url: 完整的m3u8文件链接 如"https://www.bilibili.com/example/index.m3u8"
    :param name: 保存m3u8的文件名 如"index"
    :param max_workers: 多线程最大线程数
    :param num_retries: 重试次数
    """

    def __init__(self, url, name, max_workers=64, num_retries=5):
        self._url = url
        self._name = name
        self._max_workers = max_workers
        self._num_retries = num_retries
        self._file_path = os.path.join(os.getcwd(), self._name)
        self._front_url = None
        self._ts_url_list = []
        self._success_sum = 0
        self._ts_sum = 0
        self._headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) \
        AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'}

        requests.packages.urllib3.disable_warnings()

        self.get_m3u8_info(self._url, self._num_retries)
        print('Downloading', self._name)
        with ThreadPoolExecutorWithQueueSizeLimit(self._max_workers) as pool:
            for k, ts_url in enumerate(self._ts_url_list):
                pool.submit(self.download_ts, ts_url, os.path.join(self._file_path, str(k)), self._num_retries)
        if self._success_sum == self._ts_sum:
            self.output_mp4()

    def get_m3u8_info(self, m3u8_url, num_retries):
        """
        获取m3u8信息
        """
        try:
            res = requests.get(m3u8_url, timeout=(3, 30), verify=False, headers=self._headers)
            self._front_url = res.url.split(res.request.path_url)[0]
            if "EXT-X-STREAM-INF" in res.text:  # 判定为顶级M3U8文件
                for line in res.text.split('\n'):
                    if "#" in line:
                        continue
                    elif re.search(r'^http', line) is not None:
                        self._url = line
                    elif re.search(r'^/', line) is not None:
                        self._url = self._front_url + line
                    else:
                        self._url = self._url.rsplit("/", 1)[0] + '/' + line
                self.get_m3u8_info(self._url, self._num_retries)
            else:
                m3u8_text_str = res.text
                self.get_ts_url(m3u8_text_str)
        except Exception as e:
            print(e)
            if num_retries > 0:
                self.get_m3u8_info(m3u8_url, num_retries - 1)

    def get_ts_url(self, m3u8_text_str):
        """
        获取每一个ts文件的链接
        """
        if not os.path.exists(self._file_path):
            os.mkdir(self._file_path)
        new_m3u8_str = ''
        ts = make_sum()
        for line in m3u8_text_str.split('\n'):
            if "#" in line:
                if "EXT-X-KEY" in line and "URI=" in line:
                    key = self.download_key(line, 5)
                    if key:
                        new_m3u8_str += f'{key}\n'
                        continue
                new_m3u8_str += f'{line}\n'
                if "EXT-X-ENDLIST" in line:
                    break
            elif re.search(r'^http', line) is not None:
                new_m3u8_str += f"./{self._name}/{next(ts)}\n"
                self._ts_url_list.append(line)
            elif re.search(r'^/', line) is not None:
                new_m3u8_str += f"./{self._name}/{next(ts)}\n"
                self._ts_url_list.append(self._front_url + line)
            else:
                new_m3u8_str += f"./{self._name}/{next(ts)}\n"
                self._ts_url_list.append(self._url.rsplit("/", 1)[0] + '/' + line)
        self._ts_sum = next(ts)
        with open(self._file_path + '.m3u8', "w") as f:
            f.write(new_m3u8_str)

    def download_ts(self, ts_url, name, num_retries):
        """
        下载 .ts 文件
        """
        ts_url = ts_url.split('\n')[0]
        try:
            if not os.path.exists(name):
                res = requests.get(ts_url, stream=True, timeout=(5, 60), verify=False, headers=self._headers)
                if res.status_code == 200:
                    with open(name, "wb") as ts:
                        for chunk in res.iter_content(chunk_size=1024):
                            if chunk:
                                ts.write(chunk)
                    self._success_sum += 1
                    sys.stdout.write('\r[%-25s](%d/%d)' % ("*" * (100 * self._success_sum // self._ts_sum // 4),
                                                           self._success_sum, self._ts_sum))
                    sys.stdout.flush()
                else:
                    self.download_ts(ts_url, name, num_retries - 1)
                res.close()
            else:
                self._success_sum += 1
        except Exception:
            if os.path.exists(name):
                os.remove(name)
            if num_retries > 0:
                self.download_ts(ts_url, name, num_retries - 1)

    def download_key(self, key_line, num_retries):
        """
        下载key文件
        """
        mid_part = re.search(r"URI=[\'|\"].*?[\'|\"]", key_line).group()
        may_key_url = mid_part[5:-1]
        if re.search(r'^http', may_key_url) is not None:
            true_key_url = may_key_url
        elif re.search(r'^/', may_key_url) is not None:
            true_key_url = self._front_url + may_key_url
        else:
            true_key_url = self._url.rsplit("/", 1)[0] + '/' + may_key_url
        try:
            res = requests.get(true_key_url, timeout=(5, 60), verify=False, headers=self._headers)
            with open(os.path.join(self._file_path, 'key'), 'wb') as f:
                f.write(res.content)
            res.close()
            return f'{key_line.split(mid_part)[0]}URI="./{self._name}/key"{key_line.split(mid_part)[-1]}'
        except Exception as e:
            print(e)
            if os.path.exists(os.path.join(self._file_path, 'key')):
                os.remove(os.path.join(self._file_path, 'key'))
            print("加密视频,无法加载key,揭秘失败")
            if num_retries > 0:
                self.download_key(key_line, num_retries - 1)

    def output_mp4(self):
        """
        合并.ts文件，输出mp4格式视频，需要ffmpeg
        """
        cmd = f"ffmpeg -allowed_extensions ALL -i {self._name}.m3u8 -acodec copy -vcodec copy -f mp4 {self._name}.mp4"
        os.system(cmd)
        file = os.listdir(self._file_path)
        for item in file:
            os.remove(os.path.join(self._file_path, item))
        os.removedirs(self._file_path)
        os.remove(self._file_path + '.m3u8')
        print(f"Download successfully --> {self._name}")


if __name__ == "__main__":
    url_list = input("输入url，若同时输入多个url时要用空格分开：").split()
    name_list = input("输入name，若同时输入多个name要用空格分开：").split()
    # 如果M3U8_URL的数量 ≠ SAVE_NAME的数量
    # 下载一部电视剧时，只需要输入一个name就可以了
    for i, u in enumerate(url_list):
        M3u8Download(u,
                     name_list[i] if len(url_list) == len(name_list) else f"{name_list[0]}{i + 1:02}",
                     max_workers=64,
                     num_retries=10
                     )
