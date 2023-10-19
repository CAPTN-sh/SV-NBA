import os
import sys
sys.path.append("../../")

import datetime
from dataclasses import dataclass
import re
import numpy as np
from pandas import DataFrame, read_csv, to_datetime

from src.macros.macros1 import COLUMNS_DTYPES

MMSI_MATCH = re.compile(r'.*_(?P<m>[0-9]{9})_.*')

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

###############################################################################
@dataclass
class MMSIperDayFeatures:
    
    mmsi: int
    day: datetime.date
    static: DataFrame
    own: DataFrame
    s2s: DataFrame

    def __repr__(self) -> str:
        rep_str = f"mmsi: {self.mmsi}, \n"
        rep_str = rep_str + f"date: {self.day}, \n"
        rep_str = rep_str + f"static: {self.static}, \n"
        rep_str = rep_str + f"own: {self.own}, \n"
        rep_str = rep_str + f"s2s: {self.s2s}, \n"
        
        return rep_str

def get_date_range(start, end):
    """returns
        list of datetime.date objects to iterate through
    """
    # initialise
    curr_date = start
    delta = datetime.timedelta(days=1)
    date_buffer = []
    
    # iterate over range of dates
    while (curr_date <= end):
        date_buffer.append(curr_date)
        curr_date += delta

    return date_buffer


def get_mmsis(base):
    """returns
        all unique mmsi numbers of ships for which feature files exist in base folder
    """
    files = os.listdir(base)
    csv_files = [f for f in files if '.csv' in f]
    
    buffer = []
    for c in csv_files:
        m = MMSI_MATCH.match(c)
        if m is not None:
            buffer.append(int(m.groups('m')[0]))

    return np.unique(buffer).tolist()


def load_data_features_to_dataclass(base: str,
                                    day: datetime.date,
                                    mmsi: int):
    """returns
        list of ShipFeature objects, each storing:
            - mmsi
            - date
            - static df
            - own df
            - s2s df
        for ONE given day
        and ONE given mmsi
    """
    
    # assemble the full paths to the files
    base_path = base
    ship_prefix = str(day) + "_" + str(mmsi)
    
    static_file = ship_prefix + "_static.csv"
    static_path = os.path.join(base_path, static_file)
    
    own_file = ship_prefix + "_own.csv"
    own_path = os.path.join(base_path, own_file)
    
    s2s_file = ship_prefix + "_s2s.csv"
    s2s_path = os.path.join(base_path, s2s_file)

    # load files to dataframes
    if os.path.exists(static_path):    
        stat_df = read_csv(static_path,
                           index_col=0,
                           dtype=COLUMNS_DTYPES)
    else:
        stat_df = DataFrame()

    if os.path.exists(own_path):
        own_df = read_csv(own_path,
                          dtype=COLUMNS_DTYPES)
    
        own_df['t'] = to_datetime(own_df["t"])
        own_df.set_index('t', inplace=True)

    else:
        own_df = DataFrame()

    if os.path.exists(s2s_path):
        s2s_df = read_csv(s2s_path,
                          dtype=COLUMNS_DTYPES)
        s2s_df['t'] = to_datetime(s2s_df["t"])
        s2s_df.set_index('t', inplace=True)

    else:
        s2s_df = DataFrame()

    mpdf = MMSIperDayFeatures(mmsi=mmsi,
                              day=day,
                              static=stat_df,
                              own=own_df,
                              s2s=s2s_df)
    
    return mpdf

def load_data_features_per_day(src, day):
    """returns
        a list of list of all ShipFeature objects that were recorded on a given day
    """
    base = os.path.join(src, str(day))
    mmsis = get_mmsis(base)

    buffer = []
    for mmsi in mmsis:
        mpdf = load_data_features_to_dataclass(base,
                                                day,
                                                mmsi)
        buffer.append(mpdf)

    return buffer

### import the latter two ###

def get_data_for_time_frame(src, start, end):
    """returns
        a list of list of all ShipFeature objects that were recorded in the specified TIME WINDOW
    """
    drange = get_date_range(start=start, end=end)
    buffer = []
    
    for day in drange:
        buffer = buffer + load_data_features_per_day(src, day)

    return buffer


# only one type per query supported 
def query_by_type(buffer, ship_type):
    """returns
        the ShipFeature objects from buffer that fulfill the type query
    """

    q = [mpdf for mpdf in buffer
         if (mpdf.static['ship_type'].iloc[0] in TYPES_TO_INT[ship_type])]
    
    return q