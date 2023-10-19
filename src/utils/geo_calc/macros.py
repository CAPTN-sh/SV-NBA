
import dotsi

import sys, os
sys.path.append("../../")
from src.macros.macros import DEFAULT_VAL as dval
from src.macros.macros import COLUMNS_DTYPES as ctype

##> Macros
earth_radius = 6371009 #Meters (for WGS-84)# 6371000 # in meters
__accepted_distance_units = {'kilo_meter'     :'km',
                           'meter'          : 'm' ,
                           'nautical_mile'  : 'nm',
                           'mile'           :'mile'
                          }
accepted_distance_units = dotsi.Dict(__accepted_distance_units)


__latitude_range = {'min': -90, # degrees
                    'max': +90  # degrees
                   }
latitude_range = dotsi.Dict(__latitude_range)

__longitude_range = {'min': -180, # degrees
                     'max': +180  # degrees
                    }
longitude_range = dotsi.Dict(__longitude_range)


__accepted_distance_methods = {'geodisc'      : 'geodisc',
                               'great_circle' : 'great_circle',
                               'haversine'    : 'haversine',
                               'vicenty'      : 'vicenty'}
accepted_distance_methods = dotsi.Dict(__accepted_distance_methods)

##> Default values used in cpa
default_speed   = dval['speed']         # Knots
default_heading = dval['heading']       # degrees
default_course  = dval['course']        # degrees
default_type    = dval['ship_type']      # int
default_mmsi    = dval['mmsi']

##> Keys for types of ship interactions used in cpa.get_ship_interaction()
__s_interaction_types = {'diverging'  : -1,
                         'parallel'   :  0,
                         'converging' :  1,
                         'unknown'    : 42
                        }
s_interaction_types = dotsi.Dict(__s_interaction_types)


##> The used ellipsoidal Projection
projection = "WGS84"



