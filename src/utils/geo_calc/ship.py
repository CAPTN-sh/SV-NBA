"""Utility classes that defines the Ship, CAPTN_POINT

This includes:
    - Private Methods:

    + Public Methods:
        is_valid_latitude(): Checks the validity of latitude value
        is_valid_longitude(): Checks the validity of longitude value

        
    + Classes:
        AbstractPoint: Abstract class for geographical point
        CAPTN_POINT: Class for geographical point, with its related functionalities
        
        
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

from shapely.geometry import Point
from abc import ABC, abstractmethod
from dataclasses import dataclass
from numbers import Number
# from .geo import CAPTN_POINT
from .macros import *

def is_valid_latitude(latitude: float | None) -> bool:
    return latitude is not None and latitude_range.min <= latitude <= latitude_range.max

def is_valid_longitude(longitude: float | None) -> bool:
    return longitude is not None and longitude_range.min <= longitude <= longitude_range.max




class AbstractPoint(ABC):
    def __init__(self, latitude: float, longitude: float):
        self.latitude = latitude
        self.longitude = longitude

    @abstractmethod
    def as_shapely_point(self) -> Point:
        pass

@dataclass
class CAPTN_POINT(AbstractPoint):
    """Geometrical Point structure used in CAPTN. 
    It comes in the order (latitude, longitude).

    Args:
        latitutde (float): Latitude value between -90 and 90
        longitude (float): Longitude value between -90 and 90
        point (shapely.geometry.Point): Shape Point of (latitude, longitude)

    Returns:
        float: Latitude in range [-90, 90]
        float: Longitude in range [-180, 180]
        Point: Shapely Point that contains (Latitude, Longitude)
        
    Examples:
        captn_point1 = CAPTN_POINT(latitude=37.7749, longitude=-122.4194)
        
        captn_point2 = CAPTN_POINT(point=Point(34.0522, -118.2437))
        
    """
    
    latitude: float # | None = None
    longitude: float # | None = None
    point: Point | None = None
    # __slots__ = ('latitude', 'longitude', 'point')
    
    def __post_init__ (self, **kwargs):
        for k, v in kwargs.items():
            if k in self.__dict__:
                setattr(self,k,v)
            else:
                raise KeyError(k)
        
        ##> Check input keys integrity
        if self.point is not None:
            if not isinstance(self.point, Point):
                raise TypeError(f'passed point must be of type Shapely.Point, not {type(self.point)}')
            point_coords = self.point.coords[0]
            super().__init__(latitude=point_coords[0], longitude=point_coords[1])
            
        elif (self.latitude is not None) and (self.longitude is not None):
            super().__init__(latitude=self.latitude, longitude=self.longitude)
            self.point = Point(self.latitude, self.longitude)
            
        else:
            raise ValueError('Either pass a Shapely.Point value or two latitude and logintude values')
            
        ##> Check input values integrity
        if not is_valid_latitude(self.latitude):
            raise ValueError(f'Latitude must be in the range of [{latitude_range.min}, {latitude_range.max}]')
        if not is_valid_longitude(self.longitude):
            raise ValueError(f'Longitude must be in the range of [{longitude_range.min}, {longitude_range.max}]')

    def as_shapely_point(self) -> Point:
        return self.point
    def as_tuple(self) -> tuple:
        return (self.latitude, self.longitude)

@dataclass
class Ship(object):
    
    position: CAPTN_POINT #= CAPTN_POINT(None, None, None)
    mmsi    : int   = default_mmsi      # Ship's id
    speed   : float = default_speed     # Knots
    heading : float = default_heading   # Degrees
    course  : float = default_course    # Degrees
    stype   : int   = default_type      # int
    
    def __init__(self, 
                 position: CAPTN_POINT, 
                 speed: float, 
                 course: float, 
                 heading: float = default_heading, 
                 stype: int = default_type, 
                 mmsi: int = default_mmsi):
        #> Input validity check
        if not isinstance(position, CAPTN_POINT):
            raise TypeError('Your ship instance has not a valid position type')
        if not isinstance(speed, Number):
            raise TypeError('Your ship instance has not a valid speed type')
        if not isinstance(course, Number):
            raise TypeError('Your ship instance has not a valid course type')
        if not isinstance(heading, Number):
            raise TypeError('Your ship instance has not a valid heading type')
        if not isinstance(stype, Number):
            raise TypeError('Your ship instance has not a valid ship_type')
        if not isinstance(mmsi, Number):
            raise TypeError('Your ship instance has not a valid mmsi type')
        
        self.position   = position
        self.speed      = speed
        self.course     = course
        self.heading    = heading
        self.stype      = stype
        self.mmsi       = mmsi