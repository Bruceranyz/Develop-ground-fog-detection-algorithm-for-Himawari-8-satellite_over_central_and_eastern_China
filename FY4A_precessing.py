import h5py
import numpy as np
from numpy import uint8
import time
import os
from PIL import Image
from osgeo import gdal, osr
from numpy import deg2rad, rad2deg, arctan, arcsin, tan, sqrt, cos, sin

# 读取hdf文件
def ReadHDF5SDS(filename, sds):
    if os.path.exists(filename):
        with h5py.File(filename, 'r') as f:
            data = f[sds][:].astype("float16")
            f.close()
    else:
        print("%s is not exists, Read HDF Data fileld!" % (filename))
    return data

# 当前数据可视化
def FY4B_rgb_visual(FY4B_file, out_file):
    # 3.1 读取定标系数（反射率和辐射亮度）
    COFF = ReadHDF5SDS(FY4B_file, 'CALIBRATION_COEF(SCALE+OFFSET)')

    # 3.2 设置rgb波段，
    # 中心波长：0.47，0.65，0.825，1.375，1.61，2.25，
    # 3.75，3.75，6.25，7.1，8.5，10.7，12.0，13.5
    R = ReadHDF5SDS(FY4B_file, 'NOMChannel03') * COFF[2, 0] + COFF[2, 1]
    G = ReadHDF5SDS(FY4B_file, 'NOMChannel02') * COFF[1, 0] + COFF[1, 1]
    B = ReadHDF5SDS(FY4B_file, 'NOMChannel01') * COFF[0, 0] + COFF[0, 1]

    # 3.3 剔除填充值、无效值
    R[(R > 1) | (R < 0)] = np.nan
    G[(G > 1) | (G < 0)] = np.nan
    B[(B > 1) | (B < 0)] = np.nan

    # 3.4 可视化，生成图片
    out_png = os.path.splitext(out_file)[0] + '.png'

    data = np.zeros((R.shape[0], R.shape[1], 3),dtype=uint8)
    data[:, :, 0] = G*255
    data[:, :, 1] = B*255
    data[:, :, 2] = R*255

    # 在fromarray中默认显示为GBR，所以先转置
    # data = data.transpose(1,2,0)

    # 数组转化为矩阵
    pic = Image.fromarray(data).convert('RGB')
    if not os.path.exists(os.path.split(out_png)[0]):
        os.mkdir(os.path.split(out_png)[0])
    pic.save(out_png)

# 输出数据
def FY4B_writer(out_file, data):
    cols = data.shape[1]  # 矩阵列数
    rows = data.shape[0]  # 矩阵行数
    bands = data.shape[2]  # 矩阵行数

    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(out_file, cols, rows, bands, gdal.GDT_Float32)
    # 括号中两个0表示起始像元的行列号从(0,0)开始
    # GeoTransform = (lon_min, 0.02, 0, lat_min, 0, 0.02)
    # outRaster.SetGeoTransform(tuple(GeoTransform))
    # 获取数据集第一个波段，是从1开始，不是从0开始
    for i in range(bands):
        outband = outRaster.GetRasterBand(i+1)
        outband.WriteArray(data[:,:,i])
        outRasterSRS = osr.SpatialReference()

    # 代码4326表示WGS84坐标
    outRasterSRS.ImportFromEPSG(4326)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()

    print('Write FY4B L2 data success!')

# 辐射定标
def Calibration_FY4BL1(filename, out_file):
    # 1.读取对应原始波段DN值
    band_str = 'NOMChannel'
    LUT_str = 'CALChannel'
    band_num = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14']
    data = np.zeros((2748, 2748, 14), dtype=np.float16)
    for i in range(len(band_num)):
        print("Read band %d: %s" %(i+1, band_str + band_num[i]))
        data[:, :, i] = ReadHDF5SDS(FY4B_file, band_str + band_num[i])
        if i == 6:
            temp = data[:, :, i]
            mask = (temp < 0) | (temp > 65534)
            temp[mask] = np.nan
            data[:, :, i] = temp
        else:
            temp = data[:, :, i]
            mask = (temp < 0) | (temp > 4095)
            temp[mask] = np.nan
            data[:, :, i] = temp

    # 2.读取对应定标查找表数据并进行定标
    for i in range(len(band_num)):
        LUT = ReadHDF5SDS(FY4B_file, LUT_str + band_num[i])
        if i == 6:
            for j in range(data.shape[0]):
                for k in range(data.shape[1]):
                    if 0 <= data[j,k,i] <= 65534:
                        data[j, k, i] = LUT[int(data[j, k, i])]
            print("Calibrate band %d: %s success!" % (i + 1, LUT_str + band_num[i]))
        else:
            for j in range(data.shape[0]):
                for k in range(data.shape[1]):
                    if 0 <= data[j,k,i] <= 4095:
                        data[j, k, i] = LUT[int(data[j, k, i])]
            print("Calibrate band %d: %s success!" %(i+1, LUT_str + band_num[i]))

    # 3.输出结果未tif或者hdf格式
    FY4B_writer(out_file, data)

    return data

# 投影程序1(不知道经纬度数据时，可以使用它)
def latlon2linecolumn(lat, lon, resolution):
    # 设置基本参数
    ea = 6378.137  # 地球的半长轴[km]
    eb = 6356.7523  # 地球的短半轴[km]
    h = 42164  # 地心到卫星质心的距离[km]
    λD = deg2rad(104.7)  # 卫星星下点所在经度

    # 列偏移
    COFF = {"0500M": 10991.5,
            "1000M": 5495.5,
            "2000M": 2747.5,
            "4000M": 1373.5}
    # 列比例因子
    CFAC = {"0500M": 81865099,
            "1000M": 40932549,
            "2000M": 20466274,
            "4000M": 10233137}
    LOFF = COFF  # 行偏移
    LFAC = CFAC  # 行比例因子

    """
    (lat, lon) → (line, column)
    resolution：文件名中的分辨率{'0500M', '1000M', '2000M', '4000M'}
    line, column不是整数
    """
    # Step1.检查地理经纬度
    # Step2.将地理经纬度的角度表示转化为弧度表示
    lat = deg2rad(lat)
    lon = deg2rad(lon)
    # Step3.将地理经纬度转化成地心经纬度
    eb2_ea2 = eb**2 / ea**2
    λe = lon
    φe = arctan(eb2_ea2 * tan(lat))
    # Step4.求Re
    cosφe = cos(φe)
    re = eb / sqrt(1 - (1 - eb2_ea2) * cosφe**2)
    # Step5.求r1,r2,r3
    λe_λD = λe - λD
    r1 = h - re * cosφe * cos(λe_λD)
    r2 = -re * cosφe * sin(λe_λD)
    r3 = re * sin(φe)
    # Step6.求rn,x,y
    rn = sqrt(r1**2 + r2**2 + r3**2)
    x = rad2deg(arctan(-r2 / r1))
    y = rad2deg(arcsin(-r3 / rn))
    # Step7.求c,l
    column = COFF[resolution] + x * 2**-16 * CFAC[resolution]
    line = LOFF[resolution] + y * 2**-16 * LFAC[resolution]
    return line, column

# 投影程序2(知道经纬度数据时，可以使用查找表方法)
# 从全员盘到区域，等经纬度投影
def projection(LatLon_file, FY4B_Cal_data, start_lon, start_lat, end_lon, end_lat):
    # 判断输入的经纬度是否正确
    if start_lon >= end_lon or start_lat <= end_lat:
        print("Input lon and lat error, please check the input parm!!!")
    if not os.path.exists(LatLon_file):
        print("%s is not exists, process will return!!!" % (LatLon_file))
    # 计算行列号
    cols = int((end_lon - start_lon)/0.04)
    rows = int((start_lat - end_lat)/0.04)
    print("current row: %d, cols: %d" % (rows, cols))
    # 读取经纬度矩阵
    lat = ReadHDF5SDS(LatLon_file, 'Latitude')
    lon = ReadHDF5SDS(LatLon_file, 'Longitude')
    # 开始投影赋值
    arr = np.zeros((rows, cols), 14)-99999
    for i in range(lat.shape[0]):
        for j in range(lat.shape[1]):
            if start_lon <= lon[i,j] <= end_lon and end_lat <= lat[i,j] <= start_lat:
                curr_row = int((start_lat - lat[i,j])/0.04)
                curr_col = int((start_lon + lon[i,j])/0.04)
                arr[curr_row, curr_col,:] = FY4B_Cal_data[i, j, :]
    # 输出投影后的结果
    return arr

if __name__ == '__main__':
    start = time.time()
    ## 设置研究区域经纬度
    start_lon = 104.5
    start_lat = 47.5
    end_lon = 136
    end_lat = 33
    # 1. 设置输入文件所在路径

    FY4B_file = r'D:\XY\Z_SATE_C_BAWX_20220704001650_P_FY4A-_AGRI--_N_DISK_1047E_L1-_FDI-_MULT_NOM_20220704000000_20220704001459_4000M_V0001.HDF'
    LatLon_file = r'D:\XY\Result\FullMask_Grid_4000M_Lat_Lon.HDF'
    # 2. 设置输出文件所在路径

    out_file = r'D:\XY\Result\FY4B_L2_20220704_001459_4000M.tif'

    # 3. 读取需要的3个波段进行可视化展示（输入序号即可）
    png_flag = True
    # 默认可视化展示，如果不想可视化，将 True 改为 False
    if png_flag:
        FY4B_rgb_visual(FY4B_file, out_file)

    # 4. 辐射定标，采用查找表方法
    FY4B_Cal_data = Calibration_FY4BL1(FY4B_file,out_file)

    # 5. 投影转换，获得研究区

    study_data = projection(LatLon_file, FY4B_Cal_data, start_lon, start_lat, end_lon, end_lat)

    # 6. 调用函数执行文献算法（暂时未开发）

    # 7. 计算程序运行的时间
    end = time.time()
    print('cost time: ', -start+end)




