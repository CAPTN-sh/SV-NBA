import numpy as np
from datetime import timedelta

# 1: Position report class A
# 2: Position report class A, assigned schedule
# 3: Position report class A, response to interrogation
# 5: Static and voyage related data
# 18: Standard class B position report
# 19: Extended class B equipment position report
POS_REP_MSG_TYPES = [1,2,3,18]
VOY_REL_MSG_TYPES = [5]
EQU_POS_MSG_TYPES = [19]

POS_REP_COLUMNS = [
    "epoch",
    "msg_type",
    "mmsi",
    "status",
    "turn",
    "speed",
    "accuracy",
    "lon",
    "lat",
    "course",
    "heading",
    "maneuver",
    ]

VDF_FULLDAY_COLUMNS = [
    "epoch",
    "msg_type",
    "mmsi",
    "imo",
    "ship_type",
    "to_bow",
    "to_stern",
    "to_port",
    "to_starboard",
    "draught",
    ]

#TODO fix shiptype vs ship_type mismatch in webcrawl
SHIPREG_COLUMNS = [
    "epoch",
    "mmsi",
    "ship_type",
    "length",
    "width",
    "volume",
    "tonnage",
    "draught",
    ]


COLUMNS_DTYPES = {
    "accuracy": bool,               # check bool type
    "course": np.float16,
    "draught": np.float64,
    "epoch": np.float64,            # double precision to avoid rounding errors from datetime.timestamp()
    # "geometry": Point,
    "heading": np.float16,
    "imo": np.int32,
    "lat": np.float64,
    "length": np.float16,
    "lon": np.float64,
    "maneuver": np.int8,
    "mmsi": np.int32,
    "msg_type": np.int8,
    "name": object,
    "ship_type": np.int8,
    "speed": np.float16,
    "status": np.int8,
    "to_bow": np.float16,
    "to_stern": np.float16,
    "to_port": np.float16,     
    "to_starboard": np.float16,
    "tonnage": np.float32,
    "turn": np.float16,
    "type_str": object,
    "volume": np.float32,
    "width": np.float16,
}

DEFAULT_VAL = {
    "accuracy": False,
    "course": 360.0,
    "draught": -1,
    "epoch": -1,
    # "geometry": Point([91.0, 181.0]),
    "heading": 511,
    "imo": -1,
    "lat": 181.0,
    "length": -1,
    "lon": 91.0,
    "maneuver": 0,
    "mmsi": -1,
    "msg_type": -1,
    "name": "unknown",
    "ship_type": 0,
    "speed": 102.3,
    "status": 15,
    "to_bow": -1,
    "to_stern": -1,
    "to_port": -1,
    "to_starboard": -1,
    "tonnage": -1.0,
    "turn": 128,
    "type_str": "Other",
    "volume": -1.0,
    "width": -1,
}

CRAWL_HEADERS = ['IMO',
           'MMSI',
           'Size',
           'GT',
           'DWT',
           'Draught'
           ]

NAME_CAST = {
    "epoch": "epoch",
    "Type": "type_str",
    "MMSI": "mmsi",
    "IMO": "imo",
    "length": "length",
    "width": "width",
    "GT": "volume",
    "DWT": "tonnage",
    "Draught": "draught"
}

SHIP_INFO_COLUMNS = ["mmsi",
                     "imo",
                     "ship_type",
                     "length",
                     "width",
                     "draught",
                     "tonnage",
                     "volume"]

CAST_SHIP_TYPES = {
    "Not available": 0,
    "Reserved": 10,
    "Reserved for future use": 10,
    "Wing in ground ": 20,
    "Wing in ground A": 21,
    "Wing in ground B": 22,
    "Wing in ground C": 23,
    "Wing in ground D": 24,
    "Fishing": 30,
    "Fishing Vessel": 30,
    "Fishery Research Vessel": 30,
    "Fishery Patrol Vessel": 30,
    "Trawler": 30,
    "Tug": 31,
    "Tug/Supply Vessel": 31,
    "Towing": 31,
    "Dredger": 33,
    "Dredging or underwater ops": 33,
    "Backhoe Dredger": 33,
    "Trailing Suction Hopper Dredger": 33,
    "Grab Dredger": 33,
    "Diving ops": 34,
    "Diving Support Vessel": 34,
    "Military ops": 35,
    "Naval Patrol Vessel": 35,
    "Naval Research Vessel": 35,
    "Combat Vessel": 35,
    "Sailing": 36,
    "Sailing Vessel": 36,
    "Pleasure Craft": 37,
    "Yacht": 37,
    "Exhibition Ship": 37,
    "Museum Ship": 37,
    "High speed craft": 40,
    "Pilot Vessel": 50,
    "Standby Safety Vessel": 51,
    "Search and Rescue vessel": 51,
    "Pusher Tug": 52,
    "Port Tender": 53,
    "Crew Boat": 53,
    "Pollution Control Vessel": 54,
    "Anti-pollution equipment": 54,
    "Law Enforcement": 55,
    "Patrol Vessel": 55,
    "Local Vessel": 56,
    "Utility Vessel": 59,
    "Motor Hopper": 59,
    "Offshore Supply Ship": 59,
    "Research/Survey Vessel": 59,
    "Anchor Handling Vessel": 59,
    "Buoy-laying Vessel": 59,
    "Cable Layer": 59,
    "Work Vessel": 59,
    "Pontoon": 59,
    "Crane Ship": 59,
    "Replenishment Vessel": 59,
    "Multi Purpose Offshore Vessel": 59,
    "Offshore Construction Jack Up": 59,
    "Heavy Lift Vessel": 59,
    "Training Ship": 59,
    "Passenger": 60,
    "Passengers Ship": 60,
    "Ro-Ro/Passenger Ship": 60,
    "Accommodation Ship": 60,
    "Passenger A": 61,
    "Passenger B": 62,
    "Passenger C": 63,
    "Passenger D": 64,
    "Cargo": 70,
    "General Cargo": 70,
    "Container Ship": 70,
    "Vehicles Carrier": 70,
    "Bulk Carrier": 70,
    "Ro-Ro Cargo": 70,
    "Cement Carrier": 70,
    "Cargo/Container Ship": 70,
    "Deck Cargo Ship": 70,
    "Reefer": 70,
    "Pallet Carrier": 70,
    "Stone Carrier": 70,
    "Limestone Carrier": 70,
    "Heavy Load Carrier": 70,
    "Self Discharging Bulk Carrier": 70,
    "Deck Cargo Pontoon": 70,
    "Cargo A": 71,
    "Cargo B": 72,
    "Cargo C": 73,
    "Cargo D": 74,
    "Tanker": 80,
    "Oil/Chemical Tanker": 80,
    "Chemical Tanker": 80,
    "Asphalt/Bitumen Tanker": 80,
    "Oil Products Tanker": 80,
    "Bunkering Tanker": 80,
    "Co2 Tanker": 80,
    "Edible Oil Tanker": 80,
    "Lpg/Chemical Tanker": 80,
    "Tanker A": 81,
    "Tanker B": 82,
    "Tanker C": 83,
    "Tanker D": 84,
    "Lng Tanker": 84,
    "Lpg Tanker": 84,
    "Other Type": 90,
    "Other": 90,
}

TYPES_TO_INT = {
"NOT_AVAILABLE" : np.array([0]),
"RESERVED": np.array([10]),
"WIG_FAMILY" : np.array([20,30]),
"FISHING_FAMILY" : np.array([30]),
"TUG_FAMILY" : range(31,34),
"DIVING_FAMILY" : np.array([34]),
"MILITARY_FAMILY" : np.array([35]),
"SAILING_FAMILY" : np.array([36]),
"SPORTBOAT_FAMILY" : np.array([37]),
"HIGHSPEED_FAMILY" : range(40,50),
"UTILITY_FAMILY" : range(50,60),
"PASSANGER_FAMILY" : range(60,70),
"CARGO_FAMILY" : range(70,80),
"TANKER_FAMILY" : range(80,90),
"OTHER" : [90]
}

SPEED_COL_NAME = 'calc_speed'
ALPHA_ZSCORE = 3  # [0.3, 99.7] percentile

# Speed Hike Filter
MAX_SPEED_HIKE_FILTER = 100 # unit less (considers column values)

# Time Gap Splitter
MAX_ALLOWED_GAP_DURATION = timedelta(hours=0,
                                     minutes=10,
                                     seconds=0)

# Speed Splitter
MIN_ACTIVE_SPEED = 0.1 # Knots
MAX_ACTIVE_SPEED = 50 # Knots 
MIN_SPEED_DURATION = timedelta(hours=0,
                               minutes=10,
                               seconds=0)

# Stop Splitter
MAX_STOP_DIAMETER = 50 # Meters
MIN_STOP_DURATION = timedelta(hours=0,
                              minutes=10,
                              seconds=0)


EPOCH_STEP_SIZE = 10 # seconds
Analysis_STEP_SIZE = 10 # seconds

# 30kn are 150m / 10s (100m / 6.67s)
ANALYSIS_STEP_SIZE = timedelta(seconds=6)

ASSESSMENT_RANGE = 5 # nm
ACTION_RANGE = 1 # nm

NUM_NEAREST_SHIPS = 10
COLUMNS_NEAREST_SHIPS = []