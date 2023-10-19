"""Utility Methods and classes for Geographical Calculations.

This includes:
    - Private Methods:
        __point_to_tuple(): Convert shapely point to tuple
        __get_geodisc_distance(): Get distance between two geo points using geodisc 
        __get_greatcircle_distance(): Get distance between two geo points using great circle
        __get_haversine_distance(): Get distance between two geo points using haversine
        
    + Public Methods:
        get_geo_distance(): Get distance between two geo points using the chosen method
        
    + Classes:

        
Authors:
    Ghassan Al-Falouji <gaf@informatik.uni-kiel.de>
    
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

##> IMPORT MACROS
from .macros import *#earth_radius, accepted_distance_units

##> IMPORT DEPENDENCIES
from typing import List, Optional
from geopy.distance import geodesic as gd
from geopy.distance import great_circle as grc
from shapely import Polygon, within
from shapely.geometry import Point
from math import cos, sin, asin, sqrt
from .convert import deg_to_rad, meter_to_seamiles, meter_to_miles
from vincenty import vincenty 
from movingpandas import Trajectory
import numpy as np
from .ship import CAPTN_POINT, is_valid_latitude, is_valid_longitude


# import math
# from convert import deg_to_rad, rad_to_deg
# from point_in_polygon import point_in_polygon
    

def _point_to_tuple(point: Point) -> tuple[float, float, Optional[float]]:
    """convert shapely point to tuple

    Args:
        point (Point): point to convert

    Raises:
        TypeError: If input type is not of type shapely.geometry.Point

    Returns:
        tuple[float, float, Optional[float]]: (x, y, Optional[z])
    """
    if type(point) is not Point:
        raise TypeError("Passed input argument must be of type shapely.geometry.Point")
    return point.coords[0]

# def is_valid_latitude(latitude: float | None) -> bool:
#     return latitude is not None and latitude_range.min <= latitude <= latitude_range.max

# def is_valid_longitude(longitude: float | None) -> bool:
#     return longitude is not None and longitude_range.min <= longitude <= longitude_range.max


# class AbstractPoint(ABC):
#     def __init__(self, latitude: float, longitude: float):
#         self.latitude = latitude
#         self.longitude = longitude

#     @abstractmethod
#     def as_shapely_point(self) -> Point:
#         pass
    
# @dataclass
# class CAPTN_POINT(AbstractPoint):
#     """Geometrical Point structure used in CAPTN. 
#     It comes in the order (latitude, longitude).

#     Args:
#         latitutde (float): Latitude value between -90 and 90
#         longitude (float): Longitude value between -90 and 90
#         point (shapely.geometry.Point): Shape Point of (latitude, longitude)

#     Returns:
#         float: Latitude in range [-90, 90]
#         float: Longitude in range [-180, 180]
#         Point: Shapely Point that contains (Latitude, Longitude)
        
#     Examples:
#         captn_point1 = CAPTN_POINT(latitude=37.7749, longitude=-122.4194)
        
#         captn_point2 = CAPTN_POINT(point=Point(34.0522, -118.2437))
        
#     """
    
#     latitude: float # | None = None
#     longitude: float # | None = None
#     point: Point | None = None
#     # __slots__ = ('latitude', 'longitude', 'point')
    
#     def __post_init__ (self, **kwargs):
#         for k, v in kwargs.items():
#             if k in self.__dict__:
#                 setattr(self,k,v)
#             else:
#                 raise KeyError(k)
        
#         ##> Check input keys integrity
#         if self.point is not None:
#             if not isinstance(self.point, Point):
#                 raise TypeError(f'passed point must be of type Shapely.Point, not {type(self.point)}')
#             point_coords = self.point.coords[0]
#             super().__init__(latitude=point_coords[0], longitude=point_coords[1])
            
#         elif (self.latitude is not None) and (self.longitude is not None):
#             super().__init__(latitude=self.latitude, longitude=self.longitude)
#             self.point = Point(self.latitude, self.longitude)
            
#         else:
#             raise ValueError('Either pass a Shapely.Point value or two latitude and logintude values')
            
#         ##> Check input values integrity
#         if not is_valid_latitude(self.latitude):
#             raise ValueError(f'Latitude must be in the range of [{latitude_range.min}, {latitude_range.max}]')
#         if not is_valid_longitude(self.longitude):
#             raise ValueError(f'Longitude must be in the range of [{longitude_range.min}, {longitude_range.max}]')

#     def as_shapely_point(self) -> Point:
#         return self.point
#     def as_tuple(self) -> tuple:
#         return (self.latitude, self.longitude)



def _get_geodisc_distance(a: tuple[float, float], 
                           b: tuple[float, float], 
                           distance_unit: str = accepted_distance_units['kilo_meter']) -> float:
    r"""Get the shortest path between two points defined in (latitude, longitude) using the Geodisc measure

    Args:
        a (tuple[float, float]): tuple of (latitude, longitude) for the first location
        b (tuple[float, float]): tuple of (latitude, longitude) for the second location
        distance_unit (str, optional): _description_. Defaults to accepted_distance_units['kilo_meter'].

    Raises:
        AssertionError: If distance not correctly calculated and return value attempt is None

    Returns:
        float: Distance in the chosen unit
        
    References:
        - https://bit.ly/3JZFLiR
    """
    distance = None
    if distance_unit == accepted_distance_units['kilo_meter']:
        distance = gd(a, b).km
    elif distance_unit == accepted_distance_units['meter']:
        distance = gd(a, b).m
    elif distance_unit == accepted_distance_units['nautical_mile']:
        distance = gd(a, b).nm
    elif distance_unit == accepted_distance_units['mile']:
        distance=gd(a, b).miles
    
    assert distance is not None
    return distance

def _get_greatcircle_distance(a: tuple[float, float], 
                           b: tuple[float, float], 
                           distance_unit: str = accepted_distance_units['kilo_meter']) -> float:
    r"""Get the shortest path between two points defined in (latitude, longitude) using the great circular distance method.
    

    Args:
        a (tuple[float, float]): tuple of (latitude, longitude) for the first location
        b (tuple[float, float]): tuple of (latitude, longitude) for the second location
        distance_unit (str, optional): _description_. Defaults to accepted_distance_units['kilo_meter'].

    Raises:
        AssertionError: If distance not correctly calculated and return value attempt is None

    Returns:
        float: Distance in the chosen unit
        
    References:
        - https://bit.ly/3JZFLiR
    """
    distance = None
    if distance_unit == accepted_distance_units['kilo_meter']:
        distance = grc(a, b).km
    elif distance_unit == accepted_distance_units['meter']:
        distance = grc(a, b).m
    elif distance_unit == accepted_distance_units['nautical_mile']:
        distance = grc(a, b).nm
    elif distance_unit == accepted_distance_units['mile']:
        distance=grc(a, b).miles
    
    assert distance is not None
    return distance

def _get_haversine_distance(a: tuple[float, float], 
                             b: tuple[float, float], 
                             distance_unit: str = accepted_distance_units['kilo_meter']) -> float:
    r"""Get the shortest path between two points defined in (latitude, longitude) using the Haversine formula

    Args:
        a (tuple[float, float]): tuple of (latitude, longitude) for the first location
        b (tuple[float, float]): tuple of (latitude, longitude) for the second location
        distance_unit (str, optional): _description_. Defaults to accepted_distance_units['kilo_meter'].

    Raises:
        AssertionError: If distance not correctly calculated and return value attempt is None

    Returns:
        float: Distance in the chosen unit
        
    References:
        - https://bit.ly/3JZFLiR
    """
    la_a, lo_a = deg_to_rad(a[0]), deg_to_rad(a[1])
    la_b, lo_b = deg_to_rad(b[0]), deg_to_rad(b[1])
    
    ##> The Harvesian formula in Meters
    delta_la = la_b - la_a
    delta_lo = lo_b - lo_a
    
    __distance = sin(delta_la / 2)**2 + cos(la_a) * cos(la_b) * sin(delta_lo / 2)**2  
    __distance = 2 * asin(sqrt(__distance)) * earth_radius   
    
    distance = None
    if distance_unit == accepted_distance_units['kilo_meter']:
        distance = __distance/1000
    elif distance_unit == accepted_distance_units['meter']:
        distance = __distance
    elif distance_unit == accepted_distance_units['nautical_mile']:
        distance = meter_to_seamiles(__distance)
    elif distance_unit == accepted_distance_units['mile']:
        distance = meter_to_miles(__distance)
    
    assert distance is not None
    return distance


def _get_vincenty_distance(a: tuple[float, float], 
                            b: tuple[float, float], 
                            distance_unit: str = accepted_distance_units['kilo_meter']) -> float:
    r"""Get the shortest path between two points defined in (latitude, longitude) using the Vicenty's measure

    Args:
        a (tuple[float, float]): tuple of (latitude, longitude) for the first location
        b (tuple[float, float]): tuple of (latitude, longitude) for the second location
        distance_unit (str, optional): _description_. Defaults to accepted_distance_units['kilo_meter'].

    Raises:
        AssertionError: If distance not correctly calculated and return value attempt is None

    Returns:
        float: Distance in the chosen unit
        
    References:
        - https://en.wikipedia.org/wiki/Vincenty's_formulae
        
    Source:
        - https://github.com/maurycyp/vincenty
    """
    distance = None
    
    #> Get the distance in km
    _distance = vincenty(a, b, miles=False) # in KM
    assert _distance is not None
    
    #> Convert to the desired unit
    if distance_unit == accepted_distance_units['kilo_meter']:
        distance= _distance
    if distance_unit == accepted_distance_units['meter']:
        distance= _distance*1000
    elif distance_unit == accepted_distance_units['nautical_mile']:
        distance= meter_to_seamiles(_distance*1000)
    elif distance_unit == accepted_distance_units['mile']:
        distance= meter_to_miles(_distance*1000)
    
    assert distance is not None
    return distance

def get_geo_distance(a: tuple[float, float] | Point | CAPTN_POINT, 
                     b: tuple[float, float] | Point | CAPTN_POINT,
                     distance_method:   str = accepted_distance_methods['vicenty'], 
                    #  distance_unit:     str = accepted_distance_units['kilo_meter']) -> float:
    """Get the shortest path between two points defined in (latitude, longitude) using the Haversine formula

    Args:
        a (tuple[float, float] | Point | CAPTN_POINT): tuple of (latitude, longitude) for the first location
        b (tuple[float, float] | Point | CAPTN_POINT): tuple of (latitude, longitude) for the second location
        distance_unit (str, optional): selected distance method for the calculation. Defaults to accepted_distance_methods['vicenty'].
        distance_unit (str, optional): selected distance unit for the output. Defaults to accepted_distance_units['kilo_meter'].

    Raises:
        ValueError: Non recognized distance unit
        ValueError: Non recognized distance method
        AssertionError: If distance not correctly calculated and return value attempt is None 
        

    Returns:
        float: Distance in the chosen unit
        
    References:
        - https://bit.ly/3JZFLiR
    """
    ##> Validate optional keys
    distance_unit = distance_unit.lower()
    if distance_unit not in accepted_distance_units.values(): 
        raise ValueError(f"Accepted distance units are {accepted_distance_units}")
    
    distance_method = distance_method.lower()
    if distance_method not in accepted_distance_methods.values(): 
        raise ValueError(f"Accepted distance units are {accepted_distance_methods}")
    
    ##> Adjust the input types
    if type(a) is Point:
        a = _point_to_tuple(a)
    elif type(a) is CAPTN_POINT:
        a = a.as_tuple()
        
    if type(b) is Point:
        b = _point_to_tuple(b)
    elif type(b) is CAPTN_POINT:
        b = b.as_tuple()
        
    # # ##> Check the oalidity of Latitude, Longitude
    if not is_valid_latitude(a[0]):
        raise ValueError(f"First enetry contains a non-valid latitude. Expected value in range [{latitude_range.min}, {latitude_range.max}]")
    if not is_valid_latitude(b[0]):
        raise ValueError(f"Second enetry contains a non-valid latitude. Expected value in range [{latitude_range.min}, {latitude_range.max}]")
    if not is_valid_longitude(a[1]):
        raise ValueError(f"First enetry contains a non-valid longitude. Expected value in range [{longitude_range.min}, {longitude_range.max}]")
    if not is_valid_longitude(b[1]):
        raise ValueError(f"Second enetry contains a non-valid longitude. Expected value in range [{longitude_range.min}, {longitude_range.max}]")
    
    distance = None
    if distance_method == accepted_distance_methods['vicenty']:
        distance = _get_vincenty_distance(a=a, b=b, distance_unit=distance_unit)
    elif distance_method == accepted_distance_methods['haversine']:
        distance = _get_haversine_distance(a=a, b=b, distance_unit=distance_unit)
    elif distance_method == accepted_distance_methods['great_circle']:
        distance = _get_greatcircle_distance(a=a, b=b, distance_unit=distance_unit)
    elif distance_method == accepted_distance_methods['geodisc']:
        distance = _get_geodisc_distance(a=a, b=b, distance_unit=distance_unit)
    else:
        raise KeyError("Unrecognised or unimplemented distance method")
    
    assert distance is not None
    return distance
    


def exceeds_geo_fence(position: CAPTN_POINT, geo_fence: Polygon) -> bool:
    """Check if a position is outside the Geofence area

    Args:
        position (CAPTN_POINT): Geographical position of the ship
        geo_fence (Shapely.Polygon): Geofence limits to check if the point falls out of it

    Returns:
        bool:
            False: position is within geo_fence
            Ture: position is out of geo_fence
    """

    #TODO clean up the mess with lon/lat in geojson files/mpd
    pt = position.as_shapely_point()
    lat = pt.x
    lon = pt.y

    return not within(Point(lon,lat),geo_fence)


def traj_calculate_distance(traj: Trajectory,
                            sortby_col_name: str = None,
                            distance_method:   str = accepted_distance_methods['vicenty'], 
                            distance_unit:     str = accepted_distance_units['meter']) -> List[float]:
    """
    Get the distances between trajectory locations

    Args:
        traj (Trajectory): Movingpandas trajectory
        sortby_col_name (str, optional): Column name to use for sorting the trajcectories dataframe. Defaults to None.
        distance_unit (str, optional): selected distance method for the calculation. Defaults to accepted_distance_methods['vicenty'].
        distance_unit (str, optional): selected distance unit for the output. Defaults to accepted_distance_units['meter'].

    Returns:
        List[float]: Calculated distances
    """
    # Get the dataframe from the Trajectory object
    traj_df = traj.df
    
    # Sort the dataframe based on the epoch timestamp column. Preserve the original index
    if sortby_col_name is not None:
        traj_df.sort_values(by=sortby_col_name)
    
    # Inistialise the result
    traj_dist = np.zeros(len(traj_df['lat']))
    
    # Loop over the dataframe and compute the distances
    for i, (index, row) in enumerate(traj_df.iterrows()):
        
        # Exit the loop before processing the last row
        if i == len(traj_df) - 1:
            break  
        # print(f"{i}: {index}: {row['epoch']}")
        point_1 = (traj_df['lat'].iloc[i], traj_df['lon'].iloc[i])
        point_2 = (traj_df['lat'].iloc[i+1], traj_df['lon'].iloc[i+1])
        
        # Get the distance between two consequent locations in nautical miles
        traj_dist[i + 1] = get_geo_distance(point_1, point_2, 
                                            distance_method=  distance_method,
                                            distance_unit= distance_unit)
        # END FOR
    return traj_dist.tolist()
    
    
    
    
    
# def is_equal(location1, location2, epsilon=0):
#     # Test whether two locations are equal or approximately equal
#     if location1 and location2:
#         return (abs(get_latitude(location1) - get_latitude(location2)) <= epsilon) and \
#                (abs(get_longitude(location1) - get_longitude(location2)) <= epsilon)
#     else:
#         return False

# def is_lat_lon(object):
#     return object and isinstance(object, dict) and 'lat' in object and 'lon' in object and \
#            isinstance(object['lat'], (int, float)) and isinstance(object['lon'], (int, float))

# def is_lat_lng(object):
#     return object and isinstance(object, dict) and 'lat' in object and 'lng' in object and \
#            isinstance(object['lat'], (int, float)) and isinstance(object['lng'], (int, float))

# def is_latitude_longitude(object):
#     return object and isinstance(object, dict) and 'latitude' in object and 'longitude' in object and \
#            isinstance(object['latitude'], (int, float)) and isinstance(object['longitude'], (int, float))

# def is_lon_lat_tuple(object):
#     return object and isinstance(object, list) and len(object) == 2 and \
#            isinstance(object[0], (int, float)) and isinstance(object[1], (int, float))

# def get_location_type(location):
#     if is_lon_lat_tuple(location):
#         return 'LonLatTuple'
#     elif is_lat_lon(location):
#         return 'LatLon'
#     elif is_lat_lng(location):
#         return 'LatLng'
#     elif is_latitude_longitude(location):
#         return 'LatitudeLongitude'
#     else:
#         raise ValueError('Unknown location format ' + str(location))

# def create_location(latitude, longitude, location_type):
#     if location_type == 'LonLatTuple':
#         return [longitude, latitude]
#     elif location_type == 'LatLon':
#         return {'lat': latitude, 'lon': longitude}
#     elif location_type == 'LatLng':
#         return {'lat': latitude, 'lng': longitude}
#     elif location_type == 'LatitudeLongitude':
#         return {'latitude': latitude, 'longitude': longitude}
#     else:
#         raise ValueError('Unknown location format ' + location_type)

# def to_lat_lon(location):
#     if is_lon_lat_tuple(location):
#         return {'lat': location[1], 'lon': location[0]}
#     elif is_lat_lon(location):
#         return {'lat': location['lat'], 'lon': location['lon']}
#     elif is_lat_lng(location):
#         return {'lat': location['lat'], 'lon': location['lng']}
#     elif is_latitude_longitude(location):
#         return {'lat': location['latitude'], 'lon': location['longitude']}
#     else:
#         raise ValueError('Unknown location format ' + str(location))

# def to_lat_lng(location):
#     if is_lon_lat_tuple(location):
#         return {'lat': location[1], 'lng': location[0]}
#     elif is_lat_lon(location):
#         return {'lat': location['lat'], 'lng': location['lon']}
#     elif is_lat_lng(location):
#         return {'lat': location['lat'], 'lng': location['lng']}
#     elif is_latitude_longitude(location):
#         return {'lat': location['latitude'], 'lng': location['longitude']}
#     else:
#         raise ValueError('Unknown location format ' + str(location))

# def to_latitude_longitude(location):
#     if is_lon_lat_tuple(location):
#         return {'latitude': location