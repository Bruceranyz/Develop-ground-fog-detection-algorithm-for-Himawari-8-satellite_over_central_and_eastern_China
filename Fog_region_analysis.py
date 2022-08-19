import os, h5py
import numpy as np
import pandas as pd
import xarray as xr
from sklearn_som.som import SOM
import pandas as pd
import matplotlib.pyplot as plt

def ReadHDF5SDS(filename, sds):
    if os.path.exists(filename):
        with h5py.File(filename, 'r') as f:
            data = f[sds][:]
    else:
        print("%s is not exists, Read HDF Data fileld!" % (filename))
    return data

'''
# 从array中创建xarray数据，用于时间序列分析
# Data shape: rows * cols * time
# lat shape = rows
# lon shape = cols
# time shape = time
# start_time：'2000-01-01'
'''
def Create_time_series_data(Fog_monthly_data, lat, lon, start_date):
    # Data’s third axis is time series
    atae = Fog_monthly_data  # 3d array
    lat_atae = lat  # latitude is the same size as the first axis
    lon_atae = lon  # longitude is the same size as second axis

    time_atae = pd.date_range(start_date, periods=Fog_monthly_data.shape[2], freq='D')  # time is the 3rd axis

    data_xr = xr.DataArray(atae, coords={'lat': lat_atae, 'lon': lon_atae, 'time': time_atae},
                           dims=["lat", "lon", "time"])
    return data_xr


'''
# 定义了一个som网络，输入的m*n代表分类个数，data为输入数据
# data size：time * rows * cols
'''
def calc_som(m, n, data_xr):
    data = data_xr
    lat_dim = data.shape[1]
    lon_dim = data.shape[2]

    # Build a m x n SOM
    som = SOM(m=m, n=n, dim=lat_dim * lon_dim, lr=0.5)

    # Fit it to the data
    som.fit(data.reshape((data.shape[0], lat_dim * lon_dim)), epochs=100)

    # Assign each datapoint to its predicted cluster
    predictions = som.predict(data.reshape((data.shape[0], lat_dim * lon_dim)))

    return som, predictions

# 对som结果进行数据分配
def data_som(FPI, m, n, predictions):
    som_dict = {}
    for i in range(0, m * n):
        mask = predictions == i
        som_FWI = FPI[mask]
        mean_FWI = som_FWI.mean(dim="time")
        som_dict[str(i)] = mean_FWI.load()

        return som_dict

# 对som结果可视化
def visual_som(FPI,m,n,som_dict):
    proj = FPI.salem.cartopy()
    color_map ="Reds"
    fig = plt.figure(figsize=[16,12])
    for i in range(0,m*n):
        ax = plt.subplot(m, n, i+1, projection=proj)
        som_dict[str(i)].plot(cmap=color_map, transform=proj, vmin=0, vmax=1, extend="both")

        ax.coastlines('10m', linewidth=1)
        ax.set_aspect('auto')
        ax.set_extent(FPI.salem.grid.extent, crs=proj)
        ax.gridlines(alpha=0.7)
        plt.tight_layout()