import numpy as np

def IcecloudFilter_function(ir120, ir087, ir108):
    arr = ir120 * 0
    """Ice cloud filter routine

    Difference of brightness temperatures in the 12.0 and 8.7 μm channels
    is used as an indicator of cloud phase (Strabala et al., 1994).
    Where it exceeds 2.5 K, a water-cloud-covered pixel is assumed with a
    large degree of certainty. This is combined with a straightforward
    temperature test, cutting off at very low 10.8 μm brightness
    temperatures (250 K).

    Args:
        | ir108 (:obj:`ndarray`): Array for the 10.8 μm channel.
        | ir087 (:obj:`ndarray`): Array for the 8.7 μm channel.
        | ir120 (:obj:`ndarray`): Array for the 12.0 μm channel.

    Returns:
        Filter image and filter mask.
    """
    print("Applying Snow Filter")
    # Apply infrared channel difference
    ic_diff = ir120 - ir087
    # Create ice cloud mask
    ice_mask = (ic_diff < 2.5) | (ir108 < 250)
    # Create snow mask for image array
    mask = ice_mask

    result = np.ma.array(arr, mask=mask)

    return mask


