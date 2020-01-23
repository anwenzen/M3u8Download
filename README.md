# 用处

1. 可以抓取某些只能在线播放的视频（手动滑稽）,所以可以通过下载,解决在线播放几秒一次卡顿的情况  
2. 下载后,会在文件夹内生成新的 `new_SAVE_DIR.m3u8` 文件（SAVE_DIR为输入的文件夹）,可用播放起播放本地已经下载的部分,下载完成时会被删除  
3. 加入`超时控制`,现在`不会卡死`  
4. 由于学会超时控制,所有支持重试了,已经添加代码注释,网络不好的可自定义修改  
5. 有简单的`进度显示`了  
6. 会自动下载`.key`文件,所以`支持解密`了  
7. 有多级m3u8的,支持多级m3u8分析,但不支持清晰度的选择,默认选择最后一个,因为有点乱
8. 已经封装成类,且加入`线程队列`控制,避免队列太长,减少资源浪费

## 依赖

1. 使用了`f-string`,所有只支持`python3.6+`  
2. `requests`库,使用`pip install requests`安装既可  
3. [ffmpeg](http://www.ffmpeg.org),只是使用ffmpeg来合并,如何不合并,可在程序中注释相应的函数调用即可  
    termux: `pkg install ffmpeg`  
    centos: `yum install ffmpeg`  
    mac os: `brew install ffmpeg`  

## 使用

1. 输入 `完整的m3u8文件链接: M3U8_URL`、`保存m3u8的文件名夹: SAVE_DIR`即可使用  

## 感谢

1. [ffmpeg-简单AES加解密记录](https://blog.csdn.net/Yao_2333/article/details/82910560)
