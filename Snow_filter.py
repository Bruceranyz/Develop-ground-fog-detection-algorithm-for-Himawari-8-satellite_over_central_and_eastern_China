import numpy as np

def SnowFilter(vis006, nir016, vis008, ir108):
    """Snow filter routine
    Snow has a certain minimum reflectance (0.11 at 0.8 μm) and snow has a
    certain minimum temperature (256 K)
    Snow displays a lower reflectivity than water clouds at 1.6 μm,
    combined with a slightly higher level of absorption
    (Wiscombe and Warren, 1980)
    thresholds are applied in combination with the Normalized Difference
    Snow Index.

    Args:
        | vis006 (:obj:`ndarray`): Array for the 0.6 μm channel.
        | nir016 (:obj:`ndarray`): Array for the 1.6 μm channel.
        | vis008 (:obj:`ndarray`): Array for the 0.8 μm channel.
        | ir108 (:obj:`ndarray`): Array for the 10.8 μm channel.

    Returns:
        Filter image and filter mask.
    """
    arr = vis006 * 0
    print("Applying Snow Filter")
    # Calculate Normalized Difference Snow Index
    ndsi = (vis006 - nir016) / (vis006 + nir016)

    # Where the NDSI exceeds a certain threshold (0.4) and the two other
    # criteria are met, a pixel is rejected as snow-covered.
    # Create snow mask for image array
    temp_thres = (vis008 / 100 >= 0.11) & (ir108 >= 256)
    ndsi_thres = ndsi >= 0.4
    # Create snow mask for image array
    mask = temp_thres & ndsi_thres

    result = np.ma.array(arr, mask=mask)

    return mask
