from typing import List
from dataclasses import dataclass

from datetime import datetime
from shapely import Point
from pandas import DataFrame
from geopandas import GeoDataFrame
import movingpandas as mpd
from movingpandas import TrajectoryCollection

import sys
sys.path.append("../")
from src.macros.macros import SHIP_INFO_COLUMNS, DEFAULT_VAL
from src.utils.io import load_file_data
from src.decode.decode import decode_file_data, split_by_message_type
from src.preprocess.segment import (create_position_report_dataframe, 
                                    create_ship_information_dataframe,
                                    create_base_trajectory,
                                    segment_trajectories,
                                    remove_outlier)

def get_mmsis(data: DataFrame) -> List[int] | None:
    """Extracts the unique mmsi numbers of ships from a positional data frame."""

    mmsis = None

    if (data is None) or (data.empty):
        return None

    mmsis = data.mmsi.unique()

    if (mmsis is None) or (mmsis.size == 0):
        return None

    return mmsis

@dataclass
class ShipTrip:
    """Dataclass that holds trip information for a ship on on a single day.

    Attributes:
      mmsi: int
        The unique MMSI number identifying the ship.
      ship_info: dict
        A dictionary containing the static ship details of interest. These are a selection from the data available from AIS messages of type 5 and from crawled sources. Here, the selection is ['mmsi', 'imo', 'ship_type', 'length', 'width', 'draught', 'tonnage', 'volume'].
      trajectories: TrajectoryCollection (movingpandas)
        The trajectories that ship followed on this trip. Of type TrajectoryCollection from movingpandas.
      start_time : datetime
        Time of first data point of the trajectories.
      end_time : datetime
        Time of last data point of the trajectories.
      """

    mmsi: int
    ship_info: dict
    trajectories: TrajectoryCollection
    start_time: datetime
    end_time: datetime

    def __init__(self, mmsi, ship_info, trajectories) -> None:
        self.mmsi = mmsi
        self.ship_info = ship_info
        self.trajectories = trajectories
        self.start_time = trajectories.trajectories[0].get_start_time()
        self.end_time = trajectories.trajectories[-1].get_end_time()

    def __repr__(self) -> str:
        rep_str = f"{{ShipTrip: {self.mmsi}, "
        rep_str = rep_str + f"info: {self.ship_info}, "
        rep_str = rep_str + \
            f"interval: {self.start_time.date()} {self.start_time.time()} - {self.end_time.time()}, "
        rep_str = rep_str + f"{self.trajectories}}}"

        return rep_str


#TODO annotate return
def assemble_trajectories_per_day(file: str,
                                  geofence_area=None,
                                  geofence_berths=None,
                                  drop_speed_hike=True,
                                  split_by_time_gap=True,
                                  split_by_speed=True,
                                  split_by_stop=True,
                                  smoothing=True):
    """Extract the trajectories for each ship from the recorded data of a single day.

    Parameters:
        geofence_area=None (Polygon)
            Polygon to filter out waypoints outside of bound.
        geofence_berts=None (Polygon)
            Polygon to filter out waypoints inside of berthing areas.
        drop_speed_hike=True
            If set to True, filter out unnormally high speed values.
        split_by_time_gap=True (bool)
            If set True, split trajectories into chunks with mpd ObservationGapSplitter.
        split_by_speed=True (bool)
            If set True, split trajectories into chunks with mpd SpeedSplitter.
        split_by_stop_gap=True (bool)
            If set True, split trajectories into chunks when mpd StopSplitter.
        smoothing=True (bool)
            If set True, smooth trajectories with mpd KalmanSmootherCV.

    Returns:
        (True, ship_buffer) where ship_buffer is a list of ShipTrip instances.
        (False, None) if data is missing or one of the internal buffers for pos, voy or ship_reg of the invoking FileLoader instance is empty.

    Return type:
        (bool, list(ShipTrip)/None)
    """

    # loading
    data = load_file_data(file)
    if data is None:
        print("Error loading the file.")
        return None

    # decoding
    decoded = decode_file_data(data)
    if decoded is None:
        print("Error decoding the data.")
        return None
    
    p, v, _ = split_by_message_type(decoded)
    
    # categorisation
    pos_df = create_position_report_dataframe(p)
    voy_df = create_ship_information_dataframe(v)

    # extract unique mmsi numbers of the recorded ships
    mmsis = get_mmsis(pos_df)
    if mmsis is None:
        print("Error: no ship data found.")
        return None
    
    trip_buffer = []
        
    for mmsi in mmsis:
        
        pos = (pos_df[pos_df.mmsi == mmsi]).copy(deep=True)
        voy = (voy_df[voy_df.mmsi == mmsi]).copy(deep=True)

        # additional ship info
        #TODO add webcrawl
        info_data = {}
        for c in SHIP_INFO_COLUMNS:
            vc = voy.get(c, DataFrame())

            if not vc.empty:
                info_data[c] = vc.iloc[0]
            else:
                info_data[c] = DEFAULT_VAL[c]

        # base trajectory
        base = create_base_trajectory(pos, mmsi)

        # segmentation
        trajectories = segment_trajectories(
            base, 
            geofence_area=geofence_area,
            geofence_berths=geofence_berths,
            drop_speed_hike=drop_speed_hike,
            split_by_time_gap=split_by_time_gap,
            split_by_speed=split_by_speed,
            split_by_stop=split_by_stop,
            smoothing=smoothing
            )

        # outlier removal
        trajectories = remove_outlier(trajectories)

        trip_buffer.append(ShipTrip(mmsi=mmsi,
                             ship_info=info_data,
                             trajectories=trajectories))
        
    return trip_buffer
