# -*- codeing = utf-8 -*-
# @Time : 2022/7/16 12:14
# @Author : Ranyz
# @File : H8_download.py
# @Software: PyCharm

import time
from ftplib import FTP
import os

# 连接登录ftp站点
# This fuction is used for connecting the ftp site, the username is your account and
# the password is your site account password
def ftp_connect():
    """用于FTP连接"""
    ftp_server = 'ftp.ptree.jaxa.jp'  # ftp站点对应的IP地址
    username = 'your account number'  # 用户名
    password = 'your ftp password'  # 密码
    ftp = FTP()
    ftp.set_debuglevel(0) # 较高的级别方便排查问题
    ftp.connect(ftp_server, 21)
    ftp.login(username, password)
    return ftp

# 检测是否存在要下载的文件
#  remote_path = "/xxx/yy/z/"  # 远端目录
# This function is used for determining if the file you want to download exists,
# the remote_path refers to the path where the file you want to download is located
def remote_file_exists(remote_path,filename):
     """用于FTP站点目标文件存在检测"""
     ftp = ftp_connect()
     ftp.cwd(remote_path) # 进入目标目录
     remote_file_names = ftp.nlst()  # 获取文件列表
     ftp.quit()
     if filename in remote_file_names:
         return True
     else:
         return False

# 下载文件
# This function is used for downloading file from the ftp site
def download_file(local_file,remote_file):
     """用于目标文件下载"""
     ftp = ftp_connect()
     bufsize = 1024
     fp = open(local_file, 'wb')
     ftp.set_debuglevel(0) # 较高的级别方便排查问题

     ftp.retrbinary('RETR ' + remote_file, fp.write, bufsize)

     fp.close()
     ftp.quit()

if __name__ == '__main__':

    # 开始日期
    start_date = '20171201'
    # 结束日期
    end_date = '20171218'

    '''
    # YYYY: year
    # MM: month
    # DD: day
    # hh: hour
    # ss: minuts
    '''

    # 定义ftp的路径ftp_path, 要下载的文件在ftp上的文件名remote_filename, 下载到本地的路径 local_filepath
    ftp_path = '/jma/netcdf/YYYYMM/DD'
    remote_filename = 'NC_H08_YYYYMMDD_hhmm_R21_FLDK.06001_06001.nc'
    local_filepath = 'E:\H8_Data\H8DATA'

    # 定义每次下载整点时刻的24个文件
    time = ['0000','0100','0200','0300','0400','0500',
            '0600','0700','0800','0900','1000','1100',
            '1200','1300','1400','1500','1600','1700',
            '1800','1900','2000','2100','2200','2300']

    # 解析文件名
    year_month = start_date[:6]
    day_num = int(end_date[6:8])-int(start_date[6:8]) + 1
    print('day number: ', day_num)

    # 获取ftp目录和文件名
    for d in range(day_num):
        # 得到当天的天数
        day = '%02d' % (int(start_date[6:8])+d)

        curr_path = ftp_path.replace('YYYYMM', year_month).replace('DD',day)
        print("current path: ", curr_path)

        for t in time:
            curr_file = remote_filename.replace('YYYYMMDD',year_month+day).replace('hhmm',t)
            print("current filename: ", curr_file)

            print('analysis filepath and filename success, start downloading this file!!!')
            # 下载该文件
            remote_file = curr_path + '/' + curr_file  # 远端文件名
            print(remote_file)

            # 设置本地文件名
            local_file = os.path.join(local_filepath,year_month+day)

            # 判断本地文件路径是否存在
            if not os.path.exists(local_file):
                os.mkdir(local_file)

            # 拼接本地文件名
            local_curr_file = os.path.join(local_file,curr_file)

            # 判断ftp目录是否存在该文件，如果存在则执行下载命令
            if remote_file_exists(curr_path, curr_file):
                # 再判断下本地文件路径下是否存在该文件，存在就不下载了
                if not os.path.exists(local_curr_file):
                    # 下载文件到本地
                    download_file(local_curr_file,remote_file)
