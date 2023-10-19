"""Bla bla bla

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
    + Include the PyProj (cartographic projections and coordinate transformations library) functionalities required here:
        - Links:
            - PyPi: https://bit.ly/3r7YfY9
            - Github: https://bit.ly/3r5zc82
            - Documentation: https://bit.ly/3ExB8JO

"""
import math

import pyproj
from utils.geo_calc.macros import projection
from geomag import declination

import numpy as np
import pandas as pd

import geopandas as gpd
from shapely.geometry import Point
from movingpandas import Trajectory

from dtaidistance import dtw, dtw_visualisation as dtwvis

import matplotlib.pyplot as plt

from typing import Union





def get_declination(lat: float, lon: float) -> float:
    """Get the magnetic declination based on postion

    Args:
        lat (float): latitude
        lon (float): longitude

    Returns:
        float: Magnetic declination to the magnetic north in degrees
        
    Example:
        >> get_declination(54.7128, 10.0060)
    """

    # Specify the date for which you want to calculate the magnetic declination (in decimal years)
    date_decimal_year = 2023.5  # Example: Mid-2023

    # Calculate magnetic declination
    return declination(lat, lon, date_decimal_year) # in Degrees


def abs_bearing_and_distance(lat1, lon1, lat2, lon2):

    # Initialize the projection object with the WGS 84 ellipsoid parameters
    p = pyproj.Geod(ellps= projection)

    # Calculate the initial bearing from ship 1 to ship 2
    abs_bearing_12, abs_bearing_21, distance = p.inv(lon1, lat1, lon2, lat2)
    abs_bearing_12 = (abs_bearing_12 + 360) % 360  # Ensure the bearing is within [0, 360] degrees
    abs_bearing_21 = (abs_bearing_21 + 360) % 360  # Ensure the bearing is within [0, 360] degrees

    return abs_bearing_12, abs_bearing_21, distance

def rel_bearing(abs_bearing_12, heading1, abs_bearing_21, heading2):
    
    # Calculate the relative bearing (angle between heading1 and bearing1)
    rel_bearing_12 = (abs_bearing_12 - heading1) % 360
    rel_bearing_21 = (abs_bearing_21 - heading2) % 360

    return rel_bearing_12, rel_bearing_21


def two_trajectories_similarity(traj1: Trajectory, traj2: Trajectory) -> Union[float, np.ndarray, list]:
    """Compute the Distnace between two timeseries. These timeseries are allowed to be of different lengths.
    The distance is computed using Fast Dynamic Time Wrapping

    Args:
        traj1 (Trajectory): _description_
        traj2 (Trajectory): _description_

    Returns:
        Union[float, np.ndarray, list]: _description_
    """
    
    coords1 = np.array([(p.y, p.x) for p in traj1.df.geometry]).reshape(-1)
    coords2 = np.array([(p.y, p.x) for p in traj2.df.geometry]).reshape(-1)

    # distance_1 = dtw.distance_fast(coords1, coords2)
    distance, paths = dtw.warping_paths(coords1, coords2)
    best_path = dtw.best_path(paths)

    return distance, paths, best_path



def get_abs_bearings(lat1: float, lon1: float, lat2: float, lon2: float) -> dict:
    """Get the absolute bearings between two geographical locations

    Args:
        lat1 (float): Geographical latitude in degree
        lon1 (float): Geographical longitude in degree
        lat2 (float): Geographical latitude in degree
        lon2 (float): Geographical longitude in degree

    Returns:
        dict:
            abs_bearing_12 (key)
                val (float): Bearing angle in degrees of ship 1 to 2
            abs_bearing_21 (key)
                val (float): Bearing angle in degrees of ship 2 to 1 
                
    """

    # Initialize the projection object with the WGS 84 ellipsoid parameters
    p = pyproj.Geod(ellps= projection)

    # Calculate the initial bearing from ship 1 to ship 2
    abs_bearing_12, abs_bearing_21, _ = p.inv(lon1, lat1, lon2, lat2)
    abs_bearing_12 = (abs_bearing_12 + 360) % 360  # Ensure the bearing is within [0, 360] degrees
    abs_bearing_21 = (abs_bearing_21 + 360) % 360  # Ensure the bearing is within [0, 360] degrees

    return {'abs_bearing_12':abs_bearing_12, 'abs_bearing_21': abs_bearing_21}

def get_rel_bearings(lat1: float, lon1: float, heading1: float, lat2: float, lon2: float, heading2: float) -> dict:
    """Get the relative bearing between two ships with heading in degreen

    Args:
        lat1 (float): Geographical latitude in degree
        lon1 (float): Geographical longitude in degree
        heading1 (float): Heading of ship 1 in degrees
        lat2 (float): Geographical latitude in degree
        lon2 (float): Geographical longitude in degree
        heading2 (float): Heading of ship 2 in degrees

    Returns:
        rel_bearing_12 (key)
            val (float): Bearing angle in degrees from ship 1 to 2
        rel_bearing_21 (key)
            val (float): Bearing angle in degrees from ship 2 to 1 
    """
    abs_bearings = get_abs_bearings(lat1=lat1, lon1=lon1, lat2=lat2, lon2=lon2)
    abs_bearing_12 = abs_bearings['abs_bearing_12']
    abs_bearing_21 = abs_bearings['abs_bearing_21']
    
    # Calculate the relative bearing (angle between heading1 and bearing1)
    rel_bearing_12 = (abs_bearing_12 - heading1) % 360
    rel_bearing_21 = (abs_bearing_21 - heading2) % 360

    return {'rel_bearing_12': rel_bearing_12, 'rel_bearing_21': rel_bearing_21}


def relative_speed(speed1: float, course1: float, speed2: float, course2: float) -> float:
    """Calculate the relative speed between two ships considering their heading

    Args:
        speed1 (float): Speed of ship one
        course1 (float): Course over ground of ship 1
        speed2 (float): Speed of ship 2
        course2 (float): Course over ground of ship 1

    Returns:
        float: relative speed between ship one and two
    """
    # Convert courses to radians
    course1_rad = math.radians(course1)
    course2_rad = math.radians(course2)

    # Calculate components of speed along the north direction
    north_component1 = speed1 * math.cos(course1_rad)
    north_component2 = speed2 * math.cos(course2_rad)

    # Calculate components of speed perpendicular to north
    perpendicular_component1 = speed1 * math.sin(course1_rad)
    perpendicular_component2 = speed2 * math.sin(course2_rad)

    # Calculate relative components
    relative_north_component = north_component2 - north_component1
    relative_perpendicular_component = perpendicular_component2 - perpendicular_component1

    # Calculate the magnitude of the relative speed
    relative_speed = math.sqrt(relative_north_component ** 2 + relative_perpendicular_component ** 2)

    return relative_speed