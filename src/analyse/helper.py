
from typing import Callable, Union

import pandas as pd
from pandas import Series, DataFrame
import numpy as np

import movingpandas as mpd
from geopandas import GeoDataFrame

def _get_bin_index(x: float, lo: float, step: float)->int:
    res = int((x - lo) / step)
    return res    
    
    
def discretize_equal_size(s: Series, lo_range: float=None, hi_range: float=None, num_bins: int=None, bin_size: float=None) -> Union[DataFrame, DataFrame, float]:
    """
    Create bins a pandas series

    Args:
        s (pandas series): series that contains the values to discretise
        lo_range (float, optional): smallest value in the bins. Defaults to None
        hi_range (float, optional): biggest value in the bins. Defaults to None
        num_bins (int, optional): The number of bins to create. Defaults to None
        bin_size (float, optional): The size of each bin. Defautls to None
        
    Returns:
        pd.DataFrame: Of the original series with indices saved in 'bin_indices' column.
        pd.DataFrame: Contains the summary of indicies with their boundaries.
        step_size: the size of a bin
    """
    # Ensure either num_bins or bin_size is provided, but not both.
    if (num_bins is None and bin_size is None) or (num_bins is not None and bin_size is not None):
        raise ValueError("Provide either 'num_bins' or 'bin_size', but not both.")
    
    # Initialize
    step_size: int = 0
    
    # Convert the series to dataframe. If the sereis has no name: create one
    if s.name is None: s.name='values'
    df = s.to_frame()
    
    # Find the low and hi ranges for the bins
    if lo_range is None: 
        lo_range = df[s.name].min()
    
    if hi_range is None: 
        hi_range = df[s.name].max()

    if lo_range >= hi_range:
        raise ValueError("lower range can not be bigger or equal to the higher range")

    # Create bins based on the specified method.
    if num_bins is not None: 
        step_size = (hi_range - lo_range)/num_bins 
    else:
        step_size = bin_size
        
    df['bin_indices'] = df[s.name].apply(_get_bin_index, lo=lo_range, step=step_size)
    return df


def geoDataFrame_to_trajCollection(gdf, traj_id_col, obj_id_col, t=None, crs="epsg:4326"):
    
    traj_collection = mpd.TrajectoryCollection(gdf,  
                                            traj_id_col=traj_id_col,
                                            obj_id_col=obj_id_col, # Only one mmsi in file
                                            t=t,
                                            crs=crs
                                            )
    
    return traj_collection
    