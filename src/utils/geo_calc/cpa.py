""" Methods and classes for Calculating the relative motion of ships.

This includes:
    - Private Methods:
        
        
    + Public Methods:
        
        
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
    -[] Convert class ship to Abstract Class.
        From Class Ship, define subclasses for each ship type.  
        All these subclasses, inherit/implement from Ship,
        with additional properties and methods that define the subclass
        type and characteristics.
        
References:
    https://github.com/nawre/arpaocalc/tree/master


"""

"""
Erwan - 2015

Project : ARPAoCALC
License : MIT

About :
ARPAoCALC is a python library written for ARPA calculations computing CPA (Closest Point of Approach) & TCPA (Time to Closest Point of Approach)
between two objects on the Earth.

Longitude and latitude are in decimal degrees
Object speed is expressed in knots
Bearing and angles are expressed in degrees
CPA result is expressed in nautical miles
TCPA result is expressed in minutes

Source: https://github.com/nawre/arpaocalc/tree/master

"""

import math
from math import sin,cos,asin,atan2
from dataclasses import dataclass
from .geo import get_geo_distance, exceeds_geo_fence
from .macros import *
from .convert import *
from .ship import CAPTN_POINT, Ship

import geopy
from geopy.distance import distance, geodesic, great_circle



##> Define the distance method and distance unit that will be used in this module
default_distance_method = accepted_distance_methods.vicenty
default_distance_unit = accepted_distance_units.nautical_mile
distance_tolerance = 0.0135 # Sea Miles (roughly 25m)
course_tolerance = 0.1 # Degrees 
max_cpa_time_steps = 6*(60*60) # Seconda => 6H
max_unknown_interaction_count = 100 # Maximum number taking steps in cpa while interaction type is unkown

@dataclass
class _SHIP_CPA(object):
    tcpa: int                   # seconds
    dcpa: float                 # Any of the distance units in .macros.accepted_distance_units
    postion: CAPTN_POINT       # Geographical location of the reposted CPA
    mmsi: int                   # Ship's ID



@dataclass
class CPA_OUTPUT(object):
    interaction: int
    ship1: _SHIP_CPA
    ship2: _SHIP_CPA
    distance: float
    
    

        
# def __step(position: CAPTN_POINT, course: float, speed: float, time: int) -> CAPTN_POINT:
#     """Take a step in the given course at the defined speed form the start position.
#     Results the new position.

#     Args:
#         position (CAPTN_POINT): current geographical position of the ship
#         course (float): current course over ground (COG) in degrees
#         speed (float): current speed of the ship in knots
#         time (int): Time in SECONDS to step in the given direct and speed.

#     Returns:
#         CAPTN_POINT: new geographical position of the ship after taking the step
        
#     References:
#         https://bit.ly/3RfSdQ3
#     """
#     # Initialize result with None
#     result = None
    
#     # Convert latitude and longitude from degrees to radians
#     lat = deg_to_rad(position.latitude)
#     lon = deg_to_rad(position.longitude)

#     # Convert course from degrees to radians
#     course_rad = deg_to_rad(course)

#     # Convert speed from knots to km/h
#     speed = knots_to_kmph(speed)

#     # Calculate the distance (in KM) covered in time
#     # Assuming speed is in km/h and time is in hours
#     d = speed * time/3600

#     # Radius of the Earth in km
#     R = earth_radius/1000

#     # Calculate new position using the Haversine formula
#     lat_new = asin(sin(lat)*cos(d/R) + cos(lat)*sin(d/R)*cos(course_rad))
#     lon_new = lon + atan2(sin(course_rad)*sin(d/R)*cos(lat), cos(d/R)-sin(lat)*sin(lat_new))

#     # Convert latitude and longitude from radians to degrees and pack in CAPTN_POINT
#     lat_new = rad_to_deg(lat_new)
#     lon_new = rad_to_deg(lon_new)
#     result = CAPTN_POINT(latitude=lat_new, longitude=lon_new)
    
#     assert result is not None

#     return result

def __step(position: CAPTN_POINT, course: float, speed: float, time: int) -> CAPTN_POINT:
    """Take a step in the given course at the defined speed form the start position.
    Results the new position.

    Args:
        position (CAPTN_POINT): current geographical position of the ship
        course (float): current course over ground (COG) in degrees
        speed (float): current speed of the ship in knots
        time (int): Time in SECONDS to step in the given direct and speed.

    Returns:
        CAPTN_POINT: new geographical position of the ship after taking the step
        
    References:
        https://bit.ly/3RfSdQ3
    """
    # Initialize result with None
    result = None
    
    lat = position.latitude
    lon = position.longitude

    # Convert speed from knots to km/h
    speed = knots_to_kmph(speed)

    # Calculate the distance (in KM) covered in time
    # Assuming speed is in km/h and time is in hours
    d = speed * time/3600

    # Radius of the Earth in km
    R = earth_radius/1000
    
    # Calculate new position using geopy
    origin = geopy.Point(lat, lon)
    destination = great_circle(kilometers=d).destination(origin, course)

    lat_new, lon_new = destination.latitude, destination.longitude

    result = CAPTN_POINT(latitude=lat_new, longitude=lon_new)
    
    assert result is not None

    return result


def itterative_cpa_deprecated(_ship1: Ship, 
                   _ship2: Ship, 
                   geo_fence = None, 
                   time_step_size: int = 1,                   # Size of a time step -> 1 second               
                   max_steps: int = max_cpa_time_steps) -> tuple[CPA_OUTPUT, int]:
    """_summary_

    Args:
        _ship1 (Ship): First ship
        _ship2 (Ship): Second ship
        geo_fence (_type_, optional): _description_. Defaults to None.
        max_time_steps (int, optional): _description_. Defaults to 0.

    Returns:
        CPA_OUTPUT: CPA calculation output
        int: Number of itterations till the itterations complete
    """
    
    #> Initialize the interaction type and the counter of repetition while the status is unknown
    iterrations_counter = 0
    interaction = s_interaction_types.unknown
    unkown_coutner = max_unknown_interaction_count
    steps_counter = max_steps
    tcpa = 0
    
    #> Check ships mmsi, if any does not have one, follow the order they were passed with
    if _ship1.mmsi == default_mmsi: _ship1.mmsi = 1
    if _ship2.mmsi == default_mmsi: _ship2.mmsi = 2
    
    result = CPA_OUTPUT(interaction = interaction,
                        ship1=_SHIP_CPA(tcpa= -1,
                                         dcpa= -1,
                                         postion= _ship1.position,
                                         mmsi= _ship1.mmsi),
                        ship2=_SHIP_CPA(tcpa= -1,
                                         dcpa= -1,
                                         postion= _ship2.position,
                                         mmsi= _ship2.mmsi),
                        distance = -1)
    
    
    #> Get the initial distance between the two ships
    initial_distance = get_geo_distance(a= _ship1.position, 
                                        b= _ship2.position, 
                                       distance_method= default_distance_method,
                                       distance_unit= default_distance_unit)
    
    # inital values in main loop
    distance = initial_distance
    ship1_position = _ship1.position
    ship2_position = _ship2.position
    
    while((interaction == s_interaction_types.converging) or 
          (interaction == s_interaction_types.unknown and (unkown_coutner>0))):
        
        #> Take a step for ships
        ship1_new_position = __step(position= ship1_position, 
                                    course= _ship1.course, 
                                    speed= _ship1.speed, 
                                    time= time_step_size)
        ship2_new_position = __step(position= ship2_position, 
                                    course= _ship2.course, 
                                    speed= _ship2.speed, 
                                    time= time_step_size)
        
        # If any of the ships exceeds the geofence: break
        if geo_fence is not None:
            ships_2_geo_fence_list = [exceeds_geo_fence(ship1_new_position, geo_fence),
                                     exceeds_geo_fence(ship2_new_position, geo_fence)]
            if any(ships_2_geo_fence_list):
                # print(f"Taking step {iterrations_counter}:\n results with ship(s) {[i+1 for i, x in enumerate(ships_2_geo_fence_list) if x]} to exceed the geofence")

                #TODO return last cpa_output
                break
        
        #> Find the new distance and the interaction
        new_distance = get_geo_distance(a= ship1_new_position, 
                                        b= ship2_new_position, 
                                        distance_method= default_distance_method,
                                        distance_unit= default_distance_unit)
        
        #> converging case
        if new_distance < distance: 
            print("\t new < old")
            interaction = s_interaction_types.converging
            # Update the values
            distance = new_distance
            ship1_position = ship1_new_position
            ship2_position = ship2_new_position
            tcpa += time_step_size
            
            # Update the result
            result = CPA_OUTPUT(interaction = interaction,
                                ship1=_SHIP_CPA(tcpa= tcpa,
                                                 dcpa= get_geo_distance(
                                                     a= ship1_position,
                                                     b= _ship1.position,
                                                     distance_method= default_distance_method,
                                                     distance_unit= default_distance_unit),
                                                 postion= ship1_position,
                                                 mmsi= _ship1.mmsi),
                                ship2=_SHIP_CPA(tcpa= tcpa,
                                                 dcpa= get_geo_distance(
                                                     a= ship2_position, 
                                                     b= _ship2.position,
                                                     distance_method= default_distance_method,
                                                     distance_unit= default_distance_unit),
                                                 postion= ship2_position,
                                                 mmsi= _ship2.mmsi),
                                distance = distance)
            
            #> Update the counter
            iterrations_counter += 1
            
        #> diverging
        elif new_distance > (distance + distance_tolerance):
            print("\t new > old + tol")
            interaction = s_interaction_types.diverging
            
            result = CPA_OUTPUT(interaction = interaction,
                                ship1=_SHIP_CPA(tcpa= tcpa,
                                                 dcpa= get_geo_distance(
                                                     a= ship1_position, 
                                                     b= _ship1.position,
                                                     distance_method= default_distance_method,
                                                     distance_unit= default_distance_unit),
                                                 postion= ship1_position,
                                                 mmsi= _ship1.mmsi),
                                ship2=_SHIP_CPA(tcpa= tcpa,
                                                 dcpa= get_geo_distance(
                                                     a= ship2_position, 
                                                     b= _ship2.position,
                                                     distance_method= default_distance_method,
                                                     distance_unit= default_distance_unit),
                                                 postion= ship2_position,
                                                 mmsi= _ship2.mmsi),
                                distance = distance)
            
            #> Update the counter
            iterrations_counter += 1
            
            break
            
        #> almost parallel (still deverging)
        elif abs(new_distance - distance) <= distance_tolerance:
            print("\t new - old < tol")
            if abs(_ship1.course - _ship2.course) <= course_tolerance:
                print("parallel")
                interaction = s_interaction_types.parallel   
                # Update values
                distance = new_distance
                             
                # Update the result
                result = CPA_OUTPUT(interaction = interaction,
                                    ship1=_SHIP_CPA(tcpa= tcpa,
                                                    dcpa= 0,
                                                    postion= _ship1.position,
                                                    mmsi= _ship1.mmsi),
                                    ship2=_SHIP_CPA(tcpa= tcpa,
                                                    dcpa= 0,
                                                    postion= _ship2.position,
                                                    mmsi= _ship2.mmsi),
                                    distance = distance)
                
                #TODO fix location
                #> Update the counter
                iterrations_counter += 1
                
            else: 
                break
                
            

        else:
            interaction = s_interaction_types.unknown
            tcpa += time_step_size
            unkown_coutner -= 1
            
        #> Exit the while loop if the max step counter is exceeded
        steps_counter -= time_step_size
        if (steps_counter <= 0):
            break
        
        # END WHILE
    return result, iterrations_counter

def itterative_cpa(_ship1: Ship, 
                   _ship2: Ship, 
                   geo_fence = None, 
                   time_step_size: int = 1,                   # Size of a time step -> 1 second               
                   max_steps: int = max_cpa_time_steps) -> tuple[CPA_OUTPUT, int]:
    """_summary_

    Args:
        _ship1 (Ship): First ship
        _ship2 (Ship): Second ship
        geo_fence (_type_, optional): _description_. Defaults to None.
        max_time_steps (int, optional): _description_. Defaults to 0.

    Returns:
        CPA_OUTPUT: CPA calculation output
        int: Number of itterations till the itterations complete
    """
    
    #> Initialize the interaction type and the counter of repetition while the status is unknown
    iterrations_counter = 0
    interaction = s_interaction_types.diverging
    unkown_coutner = max_unknown_interaction_count
    steps_counter = max_steps
    tcpa = 0
    
    #> Check ships mmsi, if any does not have one, follow the order they were passed with
    if _ship1.mmsi == default_mmsi: _ship1.mmsi = 1
    if _ship2.mmsi == default_mmsi: _ship2.mmsi = 2

    ### initial setup ###
    
    #> Get the initial distance between the two ships
    initial_distance = get_geo_distance(a= _ship1.position, 
                                        b= _ship2.position, 
                                       distance_method= default_distance_method,
                                       distance_unit= default_distance_unit)
    
    result = CPA_OUTPUT(interaction = interaction,
                        ship1=_SHIP_CPA(tcpa= 0,
                                         dcpa= 0,
                                         postion= _ship1.position,
                                         mmsi= _ship1.mmsi),
                        ship2=_SHIP_CPA(tcpa= 0,
                                         dcpa= 0,
                                         postion= _ship2.position,
                                         mmsi= _ship2.mmsi),
                        distance = initial_distance)
    result_tcpa = tcpa
    ### end initial ###
    
    
    # initalise values for main loop
    distance = initial_distance
    ship1_position = _ship1.position
    ship2_position = _ship2.position
    new_tcpa = tcpa
    
    while(
        (iterrations_counter < max_steps) and
        (
            (interaction == s_interaction_types.converging)
            or
            (interaction == s_interaction_types.diverging 
            and (unkown_coutner>0))
        )
    ):

        #> Take a step for ships
        ship1_new_position = __step(position= ship1_position, 
                                    course= _ship1.course, 
                                    speed= _ship1.speed, 
                                    time= time_step_size)
        ship2_new_position = __step(position= ship2_position, 
                                    course= _ship2.course, 
                                    speed= _ship2.speed, 
                                    time= time_step_size)
        
        # If any of the ships exceeds the geofence: break
        if geo_fence is not None:
            ships_2_geo_fence_list = [
                exceeds_geo_fence(ship1_new_position, geo_fence),
                exceeds_geo_fence(ship2_new_position, geo_fence)]
            if any(ships_2_geo_fence_list):
                # print(f"Taking step {iterrations_counter}:\n results with ship(s) {[i+1 for i, x in enumerate(ships_2_geo_fence_list) if x]} to exceed the geofence")
                break
        
        #> Find the new distance and the interaction
        new_distance = get_geo_distance(a= ship1_new_position, 
                                        b= ship2_new_position, 
                                        distance_method= default_distance_method,
                                        distance_unit= default_distance_unit)
        
        # Update the result
        new_tcpa = new_tcpa + time_step_size
        new_result = CPA_OUTPUT(interaction = interaction,
                                ship1=_SHIP_CPA(tcpa= new_tcpa,
                                                 dcpa= get_geo_distance(
                                                     a= ship1_position,
                                                     b= _ship1.position,
                                                     distance_method= default_distance_method,
                                                     distance_unit= default_distance_unit),
                                                 postion= ship1_position,
                                                 mmsi= _ship1.mmsi),
                                ship2=_SHIP_CPA(tcpa= new_tcpa,
                                                 dcpa= get_geo_distance(
                                                     a= ship2_position, 
                                                     b= _ship2.position,
                                                     distance_method= default_distance_method,
                                                     distance_unit= default_distance_unit),
                                                 postion= ship2_position,
                                                 mmsi= _ship2.mmsi),
                                distance = distance)
        
        
        #> converging case
        if new_distance < distance:
            interaction = s_interaction_types.converging
            # Update the values
            distance = new_distance
            ship1_position = ship1_new_position
            ship2_position = ship2_new_position

            result = new_result
            result_tcpa = new_tcpa
            
        #> diverging (maybe parallel)
        else:
            interaction = s_interaction_types.diverging
            unkown_coutner -= 1
            
        #> Update the counter
        iterrations_counter += 1
            
        # END WHILE
    return result, iterrations_counter
    
        
        

# def compute_cpa(ship1_lat, ship1_lon, ship1_course, ship1_speed, ship2_lat, ship2_lon, ship2_course, ship2_speed):
#     # Convert speeds from knots to meters per second
#     ship1_speed_mps = ship1_speed * 0.514444
#     ship2_speed_mps = ship2_speed * 0.514444
    
#     # Calculate the relative bearing between the ships (bearing from ship1 to ship2)
#     delta_lon = math.radians(ship2_lon - ship1_lon)
#     ship1_lat_rad = math.radians(ship1_lat)
#     ship2_lat_rad = math.radians(ship2_lat)
    
#     y = math.sin(delta_lon) * math.cos(ship2_lat_rad)
#     x = math.cos(ship1_lat_rad) * math.sin(ship2_lat_rad) - math.sin(ship1_lat_rad) * math.cos(ship2_lat_rad) * math.cos(delta_lon)
#     relative_bearing = math.degrees(math.atan2(y, x))
    
#     # Calculate the distance between the ships
#     dist = distance((ship1_lat, ship1_lon), (ship2_lat, ship2_lon)).meters
    
#     # Check if both ships have the same speed
#     if ship1_speed_mps == ship2_speed_mps:
#         ship_relation = "moving in parallel"
#         collision_point = None
#         tcpa = None
#         dcpa = None
#     else:
#         # Calculate the time to collision (TTC)
#         ttc = dist / abs(ship1_speed_mps - ship2_speed_mps)
        
#         # Determine if ships are converging or moving in parallel
#         if relative_bearing > 90 and relative_bearing < 270:
#             ship_relation = "converging"
            
#             # Calculate the collision point
#             collision_point_lat = ship1_lat + (ship1_speed_mps * ttc * math.cos(math.radians(ship1_course)))
#             collision_point_lon = ship1_lon + (ship1_speed_mps * ttc * math.sin(math.radians(ship1_course)))
            
#             # Calculate TCPA (Time to Closest Point of Approach)
#             tcpa = ttc
            
#             # Calculate DCPA (Distance at Closest Point of Approach)
#             dcpa = abs(ship1_speed_mps - ship2_speed_mps) * tcpa
#             collision_point = (collision_point_lat, collision_point_lon)
#         else:
#             ship_relation = "moving in parallel"
#             collision_point = None
#             tcpa = None
#             dcpa = None
    
#     return ship_relation, collision_point, tcpa, dcpa 