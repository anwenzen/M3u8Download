# -*- coding: UTF-8 -*-
# -*_ author: Vnzen -*-
import os
import re
import queue
import shutil
import requests
from concurrent.futures import ThreadPoolExecutor


class ThreadPoolExecutorWithQueueSizeLimit(ThreadPoolExecutor):
    def __init__(self, max_workers=None, *args, **kwargs):
        super().__init__(max_workers, *args, **kwargs)
        self._work_queue = queue.Queue(max_workers * 2)  # 队列数为线程数的2倍


class M3u8Download:
    def __init__(self, m3u8_url, save_dir='new_video', max_workers=64, ce_verify=False):
        self.m3u8_url = m3u8_url  # 完整的m3u8文件链接  如：M3U8_URL = "https://www.bilibili.com/example/index.m3u8"
        self.front_url = None
        self.save_dir = save_dir  # 保存m3u8的文件名夹  如：SAVE_DIR = "index"
        self.max_workers = max_workers  # 线程数，你的网速、服务器的网速跟不上，再大也没用。不要盲目加大
        self.ts_url_list = []
        self.success_sum = 0  # 记录下载成功的 .ts 文件个数
        self.ts_sum = 0  # 记录一个 .m3u8 文件含有 .ts 文件的总数
        self.fail_sum = 0
        self.ce_verify = ce_verify  # ssl,ce证书验证开关,当为False时忽略安全性
        self.start()

    def start(self):
        print(f"""M3U8_URL: {self.m3u8_url}\nSAVE_DIR: {os.getcwd()}/{self.save_dir}""")
        if not self.ce_verify:
            requests.packages.urllib3.disable_warnings()
        try:
            self.get_m3u8_info(self.m3u8_url)
        except:
            print(f"获取失败:{self.m3u8_url}")
            return
        for times in range(0, 5):  # 最多重试 5 次
            print(f"第 {times + 1} 次尝试中") if times==0 else print(f"\n第 {times + 1} 次尝试中")
            self.success_sum = 0
            self.fail_sum = 0
            with ThreadPoolExecutorWithQueueSizeLimit(self.max_workers) as pool:
                for ts_url, auto_id in zip(self.ts_url_list, range(0, len(self.ts_url_list))):
                    pool.submit(self.download_ts, ts_url, f"w_{auto_id + 1}.ts")
            if self.success_sum == self.ts_sum:
                self.merge_ts_file()
                break

    # 下载.m3u8   获取 .ts链接以及 .key链接
    def get_m3u8_info(self, m3u8_url):
        res = requests.get(m3u8_url, timeout=(5, 60), verify=self.ce_verify)
        self.front_url = res.request.url.split(res.request.path_url)[0]
        if "EXT-X-STREAM-INF" in res.text:  # 判定为顶级M3U8文件
            for line in res.text.split('\n'):
                if "#" in line:
                    continue
                elif re.search(r'^http', line) is not None:
                    self.m3u8_url = line
                    print(f"SECOND_M3U8_URL: {self.m3u8_url}")
                elif re.search(r'^/', line) is not None:
                    self.m3u8_url = self.front_url + line
                    print(f"SECOND_M3U8_URL: {self.m3u8_url}")
                else:
                    self.m3u8_url = self.m3u8_url.rsplit("/", 1)[0] + '/' + line
                    print(f"SECOND_M3U8_URL: {self.m3u8_url}")
            print(f"SELECT_SECONDARY_M3U8_URL: {self.m3u8_url}")
            self.get_m3u8_info(self.m3u8_url)
        else:
            m3u8_text_str = res.text
            res.close()
            self.get_ts_url(m3u8_text_str)
        res.close()

    def get_ts_url(self, m3u8_text_str):
        if not os.path.exists(f"./{self.save_dir}"):
            os.mkdir(f"./{self.save_dir}")
        if not os.path.exists(f"./{self.save_dir}/ts"):
            os.mkdir(f"./{self.save_dir}/ts")
        new_m3u8_file = open(f"./{self.save_dir}/new_{self.save_dir}.m3u8", 'w')
        for line in m3u8_text_str.split('\n'):
            if "#" in line:
                if "EXT-X-KEY" in line:
                    new_m3u8_file.writelines(self.download_key(line))
                    continue
                new_m3u8_file.writelines(line + "\n")
                if "EXT-X-ENDLIST" in line:
                    break
            elif re.search(r'^http', line) is not None:
                self.ts_sum += 1
                new_m3u8_file.writelines(f"./ts/w_{self.ts_sum}.ts\n")
                self.ts_url_list.append(line)
            elif re.search(r'^/', line) is not None:
                self.ts_sum += 1
                new_m3u8_file.writelines(f"./ts/w_{self.ts_sum}.ts\n")
                self.ts_url_list.append(self.front_url + line)
            else:
                self.ts_sum += 1
                new_m3u8_file.writelines(f"./ts/w_{self.ts_sum}.ts\n")
                self.ts_url_list.append(self.m3u8_url.rsplit("/", 1)[0] + '/' + line)

    # 下载 .ts 文件
    def download_ts(self, ts_url, save_ts_name):
        ts_url = ts_url.split('\n')[0]
        try:
            if not os.path.exists(f"./{self.save_dir}/ts/{save_ts_name}"):
                # ConnectTimeout= 5 s     ReadTimeout= 60 s
                res = requests.get(ts_url, stream=True, timeout=(5, 60), verify=self.ce_verify)
                if res.status_code == 200:
                    with open(f"./{self.save_dir}/ts/{save_ts_name}", "wb") as ts:
                        for chunk in res.iter_content(chunk_size=1024):
                            if chunk:
                                ts.write(chunk)
                    self.success_sum += 1
                    print(f"\r下载进度:{self.success_sum}/{self.ts_sum: <10}", end="")
                else:
                    print(f"\n下载./{self.save_dir}/ts/{save_ts_name}失败, [服务器响应码status_code!=200]")
                res.close()
            else:
                self.success_sum += 1
        except Exception:
            if os.path.exists(f"./{self.save_dir}/ts/{save_ts_name}"):
                os.remove(f"./{self.save_dir}/ts/{save_ts_name}")
#             print(f"\t下载./{self.save_dir}/ts/{save_ts_name}失败,连接或下载超时")
            self.fail_sum += 1
            print(f"\r下载进度:{self.success_sum}/{self.ts_sum: <10}失败数:{self.fail_sum}", end="")

    # 下载 .key 文件
    def download_key(self, key_line):
        mid_part = re.search(r"URI=[\'|\"].*?[\'|\"]", key_line).group()
        may_key_url = mid_part[5:-1]
        print(f"MAY_KEY_URL = {may_key_url}")
        if re.search(r'^http', may_key_url) is not None:
            true_key_url = may_key_url
        elif re.search(r'^/', may_key_url) is not None:
            true_key_url = self.front_url + may_key_url
        else:
            true_key_url = self.m3u8_url.rsplit("/", 1)[0] + '/' + may_key_url
        try:
            print(f"TRUE_KEY_URL = {true_key_url}")
            res = requests.get(true_key_url, timeout=(5, 60), verify=self.ce_verify)
            with open(f"./{self.save_dir}/ts/key.key", 'wb') as f:
                f.write(res.content)
            res.close()
        except Exception:
            if os.path.exists(f"./{self.save_dir}/ts/key.key"):
                os.remove(f"./{self.save_dir}/ts/key.key")
            print(f"\t如果你看见这个，证明 .key文件没有下载成功，并且这个视频属于加密的视频，请手动下载并改名，放在途径为 ./{self.save_dir}/ts/key.key")
        new_line = f'{key_line.split(mid_part)[0]}URI="./ts/key.key"{key_line.split(mid_part)[-1]}\n'
        return new_line

    # 合并.ts文件，输出mp4格式视频，需要ffmpeg
    def merge_ts_file(self):
        input_file = f"./{self.save_dir}/new_{self.save_dir}.m3u8"
        output_file = f"./{self.save_dir}.mp4"
        cmd = f"ffmpeg -allowed_extensions ALL -i {input_file} -acodec copy -vcodec copy -f mp4 {output_file}"
        print(f"\n{'合并开始':=^30}")
        os.system(cmd)
        shutil.rmtree(f"./{self.save_dir}")  # 合并成功后，删除 .ts 文件
        print(f"{'合并完成':=^30}")

        
if __name__ == "__main__":
    M3U8_URL_LIST = input("输入M3U8_URL，同时输入多个M3U8_URL时要用空格分开：").split(" ")
    SAVE_NAME = input("输入SAVE_NAME，同时输入多个SAVE_NAME要用空格分开：").split(" ")
    # 如果M3U8_URL的数量 ≠ SAVE_NAME的数量
    # 则只会使用第一个SAVE_NAME，并且会加尾数，方便(我自己)一次性下载一部电视剧
    START_NUMBER = 1
    for i in range(len(M3U8_URL_LIST)):
        M3u8Download(M3U8_URL_LIST[i], 
                     SAVE_NAME[i] if len(M3U8_URL_LIST)==len(SAVE_NAME) else f"{SAVE_NAME[0]}{START_NUMBER:02}",
                     64,
                     False)
        START_NUMBER += 1
