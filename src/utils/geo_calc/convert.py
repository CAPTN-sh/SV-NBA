"""Basic conversions needed in geoAnalysis

License:
    MIT

Autors:
    Ghassan Al-Falouji <gaf@informatik.uni-kiel.de>
    Lukas Haschke <lha@informatik.uni-kiel.de>

Status:
    Stable
    
Last update:
    230622
"""

import math
import pyproj
# from typing import Tuple



def deg_to_rad(angle: float) -> float:
    """Convert degrees to randian

    Args:
        angle (float): angle in degrees

    Returns:
        float: angle in radian
    """
    return math.radians(angle)

def rad_to_deg(angle: float) -> float:
    """Convert radians to degree

    Args:
        angle (float): angle in radian

    Returns:
        float: angle in degree
    """
    return math.degrees(angle)

def seamiles_to_meter(distance: float) -> float:
    """Convert sea miles to meter
    
    Args: 
        distance (float): distance in sea miles
    
    Returns:
        float: distance in meter
    """ 
    return distance*1852

def meter_to_seamiles(distance: float) -> float:
    """Convert meter to sea miles 
    
    Args: 
        distance (float): distance in meter
    
    Returns:
        float: distance in sea miles
    """ 
    return distance/1852

def meter_to_miles(distance: float) -> float:
    r"""Convert meter to miles 
    
    Args: 
        distance (float): distance in meter
    
    Returns:
        float: distance in miles
    """ 
    return distance/1609.34

def miles_to_meter(distance: float) -> float:
    r"""Convert miles to meter 
    
    Args: 
        distance (float): distance in meter
    
    Returns:
        float: distance in meter
    """ 
    return distance*1609.34

def seamiles_to_miles(distance: float) -> float:
    """Convert sea miles to miles 
    
    Args: 
        distance (float): distance in sea miles
    
    Returns:
        float: distance in miles
    """ 
    return distance*1.15078

def miles_to_seamiles(distance: float) -> float:
    """Convert miles to sea miles 
    
    Args: 
        distance (float): distance in miles
    
    Returns:
        float: distance in sea miles
    """ 
    return distance/1.15078

def knots_to_mps(speed: float) -> float:
    """Convert speed from knots to m/s

    Args:
        speed (float): speed in knots

    Returns:
        float: speed in m/s
    """
    return speed * 0.514444

def mps_to_knots(speed: float) -> float:
    """Convert speed from m/s to knots

    Args:
        speed (float): speed in m/s

    Returns:
        float: speed in knots
    """
    return speed / 0.514444

def knots_to_kmph(speed: float) -> float:
    """convert speed from knots to Km/h

    Args:
        speed (float): Speed to convert in knots

    Returns:
        float: Converted speed in Km/h
    """
    return speed * 1.852

def kmph_to_knots(speed: float) -> float:
    """convert Km/h to knots

    Args:
        speed (float): Speed to convert in km/h

    Returns:
        float: Converted speed in knots
    """
    return speed / 1.852

def geographical_to_chartesian3D(latitude: float, longitude: float) -> tuple[float, float, float]:
    """Convert geographical coordinates (latitude, longitude) to chartesian coordinates

    Args:
        latitude (float): latitude
        longitude (float): longitude

    Returns:
        tuple[float, float, float]: x, y, z coordinates
    """
    # Convert latitude and longitude to radians
    lat_rad = math.radians(latitude)
    lon_rad = math.radians(longitude)

    # Calculate Cartesian coordinates
    x = earth_radius * math.cos(lat_rad) * math.cos(lon_rad)
    y = earth_radius * math.cos(lat_rad) * math.sin(lon_rad)
    z = earth_radius * math.sin(lat_rad)

    return x, y, z

def geographical_to_chartesian(latitude: float, longitude: float) -> tuple[float, float]:
    geod = pyproj.Geod(ellps='WGS84')
    x, y, _ = geod.fwd(longitude, latitude, 0, 0)
    return x, y

def chartesian3D_to_geographical(x: float, y: float, z: float) -> tuple[float, float]:
    """Convert chartesian coordinates into geographaical

    Args:
        x (float): x
        y (float): y
        z (float): z

    Returns:
        tuple[float, float]: (latitude, longitude)
    """
    # Calculate latitude and longitude
    lat_rad = math.asin(z / earth_radius)
    lon_rad = math.atan2(y, x)

    # Convert latitude and longitude to degrees
    latitude = math.degrees(lat_rad)
    longitude = math.degrees(lon_rad)

    return latitude, longitude

def cartesian_to_geographical(x: float, y: float) -> tuple[float, float]:
    """Convert chartesian coordinates into geographaical.
    Ignore the z axis

    Args:
        x (float): x
        y (float): y
        z (float): z

    Returns:
        tuple[float, float]: (latitude, longitude)
    """
    geod = pyproj.Geod(ellps='WGS84')
    lon, lat, _ = geod.inv(x, y, 0, 90)
    return lat, lon