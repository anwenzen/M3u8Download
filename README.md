## HELLO 

一个不一定能用的小脚本


## 用处

1. 支持`m3u8`类型流媒体，~~能播放就能下载~~（可不一定）
2. 多线程下载
3. 批量任务、一次性下载一部电视剧都没问题  
4. 它不是万能的，有些m3u8文件乱得离谱，没有规律，我只能见一个改一下，也许你可以反馈一下

## 依赖

1. `python3.6+` ![img](img/1610781483234.jpg) 
2. `requests`库,使用`pip install requests`安装![img](img/1610781483232.jpg)  
3. [ffmpeg](http://www.ffmpeg.org)![img](img/1610781483229.jpg)
   对于Windows用户，需要将ffmpeg添加进环境变量中,直到你可以在CMD中使用ffmpeg命令   
    termux: `pkg install ffmpeg`  
    centos: `yum install ffmpeg`  
    mac os: `brew install ffmpeg`  
   

## 使用

1. 命令行敲入`python M3u8Download.py`
2. 输入 `url` `name` 即可使用  
   `完整的m3u8文件链接: url`  
   `保存m3u8的文件名: name`
   

## 演示

![img](img/1610781483225.jpg)
![img](img/1610781483227.jpg)


## 参数说明

![img](img/1610781483220.jpg)
