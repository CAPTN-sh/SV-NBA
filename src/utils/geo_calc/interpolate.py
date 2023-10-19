"""bla bla bla

This includes:
    - Private Methods:

        
    + Public Methods:

        
    + Classes:

        
        
Authors:
    Ghassan Al-Falouji <gaf@informatik.uni-kiel.de>
    Lukas Haschke <lha@informatik.uni-kiel.de>
    
Project:
    CAPTN FördeAreal

License:
    MIT
    
Creation date: 
    July 2023

Modifications:

Known Bugs:

ToDos:

"""

from movingpandas import Trajectory
from scipy.interpolate import PchipInterpolator
import numpy as np


def is_strictly_monotonic_increasing(array):
  """
  Check if a NumPy array is monotonic increasing.

  Args:
    array: The NumPy array to check.

  Returns:
    True if the array is monotonic increasing, False otherwise.
  """

  diff = np.diff(array)
  return np.all(diff > 0)

def is_monotonic_increasing(array):
  """
  Check if a NumPy array is monotonic increasing.

  Args:
    array: The NumPy array to check.

  Returns:
    True if the array is monotonic increasing, False otherwise.
  """

  diff = np.diff(array)
  return np.all(diff >= 0)


def pchip_traj_interpolate_at(traj: Trajectory, t: int, drop_duplicates = True) -> dict:
    """
    Interpolate a trajectory at a time t (in Epoch timestamps) 

    Args:
        traj (Trajectory): Moving pandas trajectory that contains the following columns 
            epoch: a column for time in epoch time stamp
            lat: a column for the Geographical Latitude locations
            lon: a column for the Geographical Longitude locations
            
            
        t (float): Epoch time stamp to interpolate at
        
        drop_duplicates (bool, optional): If true drop the rows with duplicate epochs. Defaults to True

    Raises:
        ValueError: _description_
        ValueError: _description_

    Returns:
        TrajData: _description_
    """
    
    # Get the features to consider in the interpolation
    columns = ['lat', 'lon', 'speed', 'turn']
    
    # Get the dataframe from the trajectory
    traj_df = traj.df
    # Sort by epoch
    traj_df_sorted = traj_df.sort_values(by='epoch')
    
    # Remove rows with duplicate epochs and keep only the first
    if drop_duplicates: traj_df_sorted.drop_duplicates('epoch', keep='first', inplace=True)
    
    xi = traj_df_sorted['epoch'].to_numpy()    
    yi = traj_df_sorted[columns].to_numpy()
    
    # y = _pchip_interpolate_at(xi, yi, t)
    
    # Create a PCHIP interpolator
    interpolator = PchipInterpolator(xi, yi)

    # Interpolate y at x_i
    y = interpolator(t)

    
    traj_data_interp = {'epoch': t, 
                        columns[0]: round(y[0], 6), 
                        columns[1]: round(y[1], 6), 
                        columns[2]: y[2], 
                        columns[3]: y[-1]
                        }
    return traj_data_interp