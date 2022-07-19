# -*- codeing = utf-8 -*-
# @Time : 2022/7/19 14:44
# @Author : Ranyz
# @File : Data_preprocessing.py
# @Software: PyCharm

import h5py,os,time
import numpy as np
from numpy import float16
from osgeo import gdal, osr
from netCDF4 import Dataset

'''
H8数据预处理的步骤为：
1. 读取所有反射率/亮度温度数据：
   反射率数据 = 反射率数据*0.0001
   亮度温度数据 = 亮度温度数据*0.01+273.15

2. 读取经度和纬度数据，投影方式为GLL, 即等经纬度投影，
   等经纬度投影的经纬度范围为（0：360，90：-90）
   其中左上角经纬度：80，60，右下角经纬度：200，-60
   像素分辨率的0.02°，空间分辨率为2km

3. 读取其他数据，如果需要（SOA,SZA,SAA,SAZ）

4. 左上角x坐标， 水平分辨率，旋转参数， 左上角y坐标，旋转参数，竖直分辨率
   Geotransform = (80,0.02,0,60,0,0.02)
'''

# 该函数读取HDF5格式文件，filename为文件全路径名，sds为HDF文件中的数据集
def ReadHDF5SDS(filename, sds):
    if os.path.exists(filename):
        with h5py.File(filename, 'r') as f:
            data = f[sds][:].astype('float16')
            f.close()
    else:
        print("%s is not exists, Read HDF Data fileld!" % (filename))

    return data

# 该函数读取NC格式文件，filename为文件全路径名，sds为NC文件中的数据集
def ReadNC(filename, sds):
    if os.path.exists(filename):
        nc_obj = Dataset(filename)
        data = nc_obj.variables[sds][:]
        nc_obj.close()
    else:
        print("%s is not exists, Read HDF Data fileld!" % (filename))

    return data

# 该函数对所有波段进行预处理
# 添加优化代码：将掩膜做出来
def ReadData(filename):
    # 读取 角度数据并预处理
    SAA = ReadNC(filename, 'SAA')
    SAZ = ReadNC(filename, 'SAZ')
    SOZ = ReadNC(filename, 'SOZ')
    SOA = ReadNC(filename, 'SOA')
    # 读取 反射率数据并预处理
    Ref_01 = ReadNC(filename, 'albedo_01')
    Ref_02 = ReadNC(filename, 'albedo_02')
    Ref_03 = ReadNC(filename, 'albedo_03')
    Ref_04 = ReadNC(filename, 'albedo_04')
    Ref_05 = ReadNC(filename, 'albedo_05')
    Ref_06 = ReadNC(filename, 'albedo_06')
    # 读取 亮温数据并预处理
    # 亮温：Tbb*0.01+273.15
    Tbb_07 = ReadNC(filename, 'tbb_07')
    Tbb_08 = ReadNC(filename, 'tbb_08')
    Tbb_09 = ReadNC(filename, 'tbb_09')
    Tbb_10 = ReadNC(filename, 'tbb_10')
    Tbb_11 = ReadNC(filename, 'tbb_11')
    Tbb_12 = ReadNC(filename, 'tbb_12')
    Tbb_13 = ReadNC(filename, 'tbb_13')
    Tbb_14 = ReadNC(filename, 'tbb_14')
    Tbb_15 = ReadNC(filename, 'tbb_15')
    Tbb_16 = ReadNC(filename, 'tbb_16')

    return SAA,SAZ,SOZ,SOA,Ref_01,Ref_02,Ref_03,Ref_04,Ref_05,Ref_06,Tbb_07,Tbb_08,Tbb_09,Tbb_10,Tbb_11,Tbb_12,Tbb_13,Tbb_14,Tbb_15,Tbb_16

#  保存为tif
def array2raster(TifName, array):
    cols = array.shape[1]  # 矩阵列数
    rows = array.shape[0]  # 矩阵行数
    bands = array.shape[2]
    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(TifName, cols, rows, bands, gdal.GDT_Float32)
    # 括号中两个0表示起始像元的行列号从(0,0)开始
    outRaster.SetGeoTransform([80, 0.02, 0, 60, 0, 0.02])
    # 获取数据集第一个波段，是从1开始，不是从0开始
    for i in range(bands):
        outband = outRaster.GetRasterBand(i + 1)
        outband.WriteArray(array[:, :, i])
    outRasterSRS = osr.SpatialReference()
    # 代码4326表示WGS84坐标
    outRasterSRS.ImportFromEPSG(4326)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()

# 执行所有命令
def main(filename, outfilename):
    SAA, SAZ, SOZ, SOA, Ref_01, Ref_02,\
    Ref_03, Ref_04, Ref_05, Ref_06, \
    Tbb_07, Tbb_08, Tbb_09, Tbb_10, \
    Tbb_11, Tbb_12, Tbb_13, Tbb_14, \
    Tbb_15, Tbb_16 = ReadData(filename)

    arr = np.empty((Ref_03.shape[0], Ref_03.shape[1], 20), dtype=float16)
    arr[:, :, 0] = Ref_01
    arr[:, :, 1] = Ref_02
    arr[:, :, 2] = Ref_03
    arr[:, :, 3] = Ref_04
    arr[:, :, 4] = Ref_05
    arr[:, :, 5] = Ref_06
    arr[:, :, 6] = Tbb_07
    arr[:, :, 7] = Tbb_08
    arr[:, :, 8] = Tbb_09
    arr[:, :, 9] = Tbb_10
    arr[:, :, 10] = Tbb_11
    arr[:, :, 11] = Tbb_12
    arr[:, :, 12] = Tbb_13
    arr[:, :, 13] = Tbb_14
    arr[:, :, 14] = Tbb_15
    arr[:, :, 15] = Tbb_16
    arr[:, :, 16] = SAA
    arr[:, :, 17] = SAZ
    arr[:, :, 18] = SOA
    arr[:, :, 19] = SOZ

    array2raster(outfilename, arr)


if __name__ == '__main__':

    start = time.time()

    filename = r'D:\Remote sensing of environment\h8-data\20171201\NC_H08_20171201_0000_R21_FLDK.06001_06001.nc'

    outfilename = 'D:/Remote sensing of environment/h8-data/H08_20171201_0000.tif'

    main(filename, outfilename)

    end = time.time()

    print("cost time: ", end - start)