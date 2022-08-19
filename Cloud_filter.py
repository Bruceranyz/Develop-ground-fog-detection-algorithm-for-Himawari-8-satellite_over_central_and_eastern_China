import numpy as np
import time, os, h5py
from netCDF4 import Dataset
from osgeo import gdal
import matplotlib.pyplot as plt
from scipy.signal import find_peaks_cwt
from Snow_filter import SnowFilter as snow

"""Cloud filtering for satellite images."""
"""
Required inputs
MIR: Brightness temperature at 3.9um
TIR: Brightness temperature at 11.2um
CCR: Cloud confidence range (default 5)
"""
# 该函数读取NC格式文件，filename为文件全路径名，sds为NC文件中的数据集
def ReadNC(filename, sds):
    if os.path.exists(filename):
        nc_obj = Dataset(filename)
        data = nc_obj.variables[sds][:]
        nc_obj.close()
    else:
        print("%s is not exists, Read HDF Data fileld!" % (filename))

    return data

def Get_MIR_TIR(filename):

    # 读取 亮温数据并预处理
    # 亮温：Tbb*0.01+273.15
    Tbb_07 = ReadNC(filename, 'tbb_07')

    Tbb_14 = ReadNC(filename, 'tbb_14')

    return Tbb_07, Tbb_14

def Get_res(filename):
    # 读取 亮温数据并预处理
    # 亮温：Tbb*0.01+273.15
    vis_03 = ReadNC(filename, 'albedo_03')
    vis_04 = ReadNC(filename, 'albedo_04')

    vis_05 = ReadNC(filename, 'albedo_05')

    return vis_03, vis_04, vis_05


def ReadHDF5SDS(filename, sds):
    if os.path.exists(filename):
        with h5py.File(filename, 'r') as f:
            data = f[sds][:]
    else:
        print("%s is not exists, Read HDF Data fileld!" % (filename))
    return data

def get_slope_decline(y, x):
    """ Compute the slope declination of a histogram."""
    slope = np.diff(y) / np.diff(x)
    decline = slope[1:] * slope[:-1]
    # Point of slope declination
    thres_id = np.where(np.logical_and(slope[1:] > 0, decline > 0))[0]
    if len(thres_id) != 0:
        decline_points = x[thres_id + 2]
        thres = np.min(decline_points[decline_points > -5])
    else:
        thres = None
    return (slope, thres)

def plot_cloud_hist(hist, saveto=None):
    """Plot the histogram of brightness temperature differences."""
    plt.bar(hist[1][:-1], hist[0])
    plt.title("Histogram with 'auto' bins")
    if saveto is None:
        plt.show()
    else:
         plt.savefig(saveto)

def CloudFilter(MIR, TIR, ccr=5):
    arr = MIR*0 + 1
    prange = (-20, 10)  # Min - max peak range

    # Infrared channel difference
    cm_diff = np.ma.asarray(TIR - MIR)

    # Create histogram
    hist = (np.histogram(cm_diff.compressed(), bins='auto'))

    # Find local min and max values
    peaks = np.sign(np.diff(hist[0]))
    localmin = (np.diff(peaks) > 0).nonzero()[0] + 1

    # Utilize scipy signal funciton to find peaks
    peakind = find_peaks_cwt(hist[0],
                             np.arange(1, len(hist[1]) / 10))
    histpeaks = hist[1][peakind]
    peakrange = histpeaks[(histpeaks >= prange[0]) &
                          (histpeaks < prange[1])]
    if len(peakrange) == 1:
        print("Not enough peaks found in range {} - {} \n"
                     "Using slope declination as threshold"
                     .format(prange[0], prange[1]))
        slope, thres = get_slope_decline(hist[0],
                                              hist[1][:-1])
    elif len(peakrange) >= 2:
        minpeak = np.min(peakrange)
        maxpeak = np.max(peakrange)

        # Determine threshold
        print("Histogram range for cloudy/clear sky pixels: {} - {}"
                     .format(minpeak, maxpeak))
        thres_index = localmin[(hist[1][localmin] <= maxpeak) &
                               (hist[1][localmin] >= minpeak) &
                               (hist[1][localmin] < 0.5)]
        thres = np.max(hist[1][thres_index])
    else:
        raise ValueError

    if thres > 0 or thres < -5:
        print("Cloud maks difference threshold {} outside normal"
                       " range (from -5 to 0)".format(thres))
    else:
        print("Cloud mask difference threshold set to {}"
                     .format(thres))
    # Compute cloud confidence level
    ccl = (cm_diff - thres - ccr) / (-2 * ccr)
    # Limit range to 0 (cloudfree) and 1 (cloudy)
    ccl[ccl > 1] = 1
    ccl[ccl < 0] = 0

    # Create cloud mask for image array
    mask = cm_diff > thres

    result = np.ma.array(arr, mask=mask)

    return ~mask

def array2raster(TifName, array):
    cols = array.shape[1]  # 矩阵列数
    rows = array.shape[0]  # 矩阵行数

    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(TifName, cols, rows, 1, gdal.GDT_Float32)
    # 括号中两个0表示起始像元的行列号从(0,0)开始
    #outRaster.SetGeoTransform([80, 0.02, 0, 60, 0, 0.02])
    # 获取数据集第一个波段，是从1开始，不是从0开始

    outband = outRaster.GetRasterBand( 1)
    outband.WriteArray(array[:, :])
    # outRasterSRS = osr.SpatialReference()
    # 代码4326表示WGS84坐标
    # outRasterSRS.ImportFromEPSG(4326)
    # outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()


if __name__=="__main__":

    start = time.time()
    filename = r'D:\Remote sensing of environment\h8-data\20171201\NC_H08_20171201_0000_R21_FLDK.06001_06001.nc'
    TifName_cloud = r'D:\Remote sensing of environment\h8-data\20171201\NC_H08_20171201_0000_R21_FLDK_cloud_result.tif'
    TifName_snow = r'D:\Remote sensing of environment\h8-data\20171201\NC_H08_20171201_0000_R21_FLDK_snow_result.tif'
    # 云检测
    # 获得数据
    MIR, TIR = Get_MIR_TIR(filename)

    out_data = CloudFilter(MIR, TIR)

    array2raster(TifName_cloud, out_data)

    vis_03, vis_04, vis_05 = Get_res(filename)

    out_data = snow(vis_03, vis_05, vis_04, TIR)

    array2raster(TifName_snow, out_data)