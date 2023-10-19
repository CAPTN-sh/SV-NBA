

from dataclasses import dataclass
from shapely.geometry import Point

@dataclass
class Location:
    lat: float
    long: float
    
    @property
    def pos(self):
        """geometry position as (lat, lon)

        Returns:
            (float, float): tuple containing the lat and lon
        """
        return Point(self.lat, self.lon)
    @pos.setter
    def pos(self, lat: float, lon: float):
        self.lat, self.lon = lat, lon

@dataclass
class BoundingBox:
    topLeft: Location
    bottomRight: Location
    
    
@dataclass
class HeadingDistance:
    heading: float
    distance: float
    
    
@dataclass
class LocationHeadingSpeed:
    location: Location
    speed: float
    heading: float
    

@dataclass
class TimeDistance:
    time: float
    distance: float
