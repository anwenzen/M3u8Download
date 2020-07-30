## 用处

1. 可以抓取某些只能在线播放的视频（手动滑稽）,所以可以通过下载,解决在线播放几秒一次卡顿的情况  

## 依赖

1. 使用了`f-string`,所有只支持`python3.6+`  
2. `requests`库,使用`pip install requests`安装既可  
3. [ffmpeg](http://www.ffmpeg.org),只是使用ffmpeg来合并,如何不合并,可在程序中注释相应的函数调用即可  
    termux: `pkg install ffmpeg`  
    centos: `yum install ffmpeg`  
    mac os: `brew install ffmpeg`  

## 使用

1. 输入 `完整的m3u8文件链接: url`、`保存m3u8的文件名: name`即可使用  
[!img](img/one_test.png)  
[!img](img/more_test.png)  
[!img](img/done.png)  
