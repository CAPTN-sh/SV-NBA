from typing import List
from datetime import datetime

from shapely import Point, Polygon
from pandas import DataFrame, Series
from geopandas import GeoDataFrame
import movingpandas as mpd
from movingpandas import Trajectory, TrajectoryCollection

import sys
sys.path.append("../")
from src.macros.macros import (COLUMNS_DTYPES, 
                               DEFAULT_VAL, 
                               POS_REP_COLUMNS, 
                               VDF_FULLDAY_COLUMNS, 
                               SPEED_COL_NAME,
                               MAX_SPEED_HIKE_FILTER,
                               MAX_ALLOWED_GAP_DURATION,
                               MIN_ACTIVE_SPEED,
                               MAX_ACTIVE_SPEED,
                               MIN_SPEED_DURATION,
                               MAX_STOP_DIAMETER,
                               MIN_STOP_DURATION,
                               ALPHA_ZSCORE)
from src.utils.univariate_statistical_tests import z_score_test


def create_position_report_dataframe(data: List[dict]) -> DataFrame:
    """Create base position pandas.DataFrame from decoded ais position reports."""
    
    pos_data={}
    for c in POS_REP_COLUMNS:
        series_data = [d.get(c, DEFAULT_VAL[c]) for d in data]
        # series_data = [val if val is not None else DEFAULT_VAL[c] for val in series_data]
        pos_data[c] = Series(series_data, dtype=COLUMNS_DTYPES[c])
    
    return DataFrame(pos_data)

def create_ship_information_dataframe(data: List[dict]) -> DataFrame:
    """Create ship information.pandas DataFrame from decoded ais voyage related messages."""
    
    ship_data={}
    for c in VDF_FULLDAY_COLUMNS:
        series_data = [d.get(c, DEFAULT_VAL[c]) for d in data]
        # series_data = [val if val is not None else DEFAULT_VAL[c] for val in series_data]
        ship_data[c] = Series(series_data, dtype=COLUMNS_DTYPES[c])

    sdf = DataFrame(ship_data)

    ### Create length, width dimensions ###
    if not sdf.empty:
        sdf['length'] = [sum(xy) if -1 not in xy else -1 for xy in zip(sdf['to_bow'], sdf['to_stern'])]
        sdf['width'] = [sum(xy) if -1 not in xy else -1 for xy in zip(sdf['to_port'], sdf['to_starboard'])]

    else:
        print(f"Cannot create ship information DataFrame, data passed empty")

    return sdf

def create_base_trajectory(pos: DataFrame, mmsi: int) -> TrajectoryCollection:
    """Create a TrajectoryCollection containing one continuous base trjectory from the position report of an individual ship."""
    
    pos["date"] = pos.epoch.apply(datetime.utcfromtimestamp)
    pos["geometry"] = [Point(xy) for xy in zip(pos['lon'], pos['lat'])]
    
    pos_gdf = GeoDataFrame(pos)
    pos_gdf.set_geometry("geometry", inplace=True)
    pos_gdf.set_crs("epsg:4326", inplace=True)

    # base trajectories
    if len(pos_gdf.index) < 2:
        print(f"cannot create Trajectory, too few Points: {mmsi}")
        return TrajectoryCollection()


    base_trajectory = mpd.Trajectory(pos_gdf,
                                    traj_id=1,
                                    obj_id=mmsi,
                                    t="date",
                                    crs="epsg:4326")

    trajectories = mpd.TrajectoryCollection([base_trajectory],
                                            traj_id_col="traj_id",
                                            obj_id_col="obj_id",
                                            t="date",
                                            crs="epsg:4326",
                                            min_length=2)
    
    return trajectories


def collection_valid(trajectories: TrajectoryCollection) -> bool:
    """Returns whether all trajectories in a colletion are valid."""

    valid = True
    if not all([traj.is_valid() for traj in trajectories]):
        valid = False

    return valid

### segmentation ###

def geofence(trajectories: TrajectoryCollection,
             polygon: Polygon) -> TrajectoryCollection:
    
    for traj in trajectories:
            in_marinas_inds = traj.df[traj.df.geometry.within(polygon)].index
            traj.df.drop(in_marinas_inds, inplace=True)

    return trajectories


def speed_hike_filter(trajectories: TrajectoryCollection) -> TrajectoryCollection:
    
    for traj in trajectories.trajectories:
            if traj.get_speed_column_name() != SPEED_COL_NAME:
                traj.add_speed(overwrite=False,
                            name=SPEED_COL_NAME,
                            units=("nm", "h")
                            )
                
            hikes_inds = traj.df[traj.df[SPEED_COL_NAME] > MAX_SPEED_HIKE_FILTER].index
            
            traj.df.drop(hikes_inds, inplace=True)

    return trajectories


def smooth(trajectories: TrajectoryCollection) -> TrajectoryCollection:

    trajectories = mpd.KalmanSmootherCV(trajectories).smooth(
            process_noise_std=0.5,
            measurement_noise_std=1
            )

    return trajectories


def time_gap_split(trajectories: TrajectoryCollection) -> TrajectoryCollection:

    trajectories = mpd.ObservationGapSplitter(trajectories).split(gap=MAX_ALLOWED_GAP_DURATION)

    return trajectories


def speed_split(trajectories: TrajectoryCollection) -> TrajectoryCollection:

    trajectories = mpd.SpeedSplitter(trajectories).split(
            speed= MIN_ACTIVE_SPEED, 
            duration= MIN_SPEED_DURATION)

    return trajectories


def stop_split(trajectories: TrajectoryCollection) -> TrajectoryCollection:

    trajectories = mpd.StopSplitter(trajectories).split(
            max_diameter=MAX_STOP_DIAMETER,
            min_duration=MIN_STOP_DURATION
        )

    return trajectories


def remove_outlier(trajectories: TrajectoryCollection) -> TrajectoryCollection:

    for traj in trajectories.trajectories:
        if not 'distance' in traj.df.columns:
                traj.add_distance(overwrite=True, units='nm')

        anomaly_indices = z_score_test(s= traj.df['distance'],
                                       threshold=ALPHA_ZSCORE)
            
        traj.df.drop(anomaly_indices, inplace=True)

    return trajectories


def segment_trajectories(trajectories: TrajectoryCollection,
                        geofence_area=None,
                        geofence_berths=None,
                        drop_speed_hike=True,
                        split_by_time_gap=True,
                        split_by_speed=True,
                        split_by_stop=True,
                        smoothing=True) -> TrajectoryCollection:
     
    if geofence_area is not None:
        tmp = geofence(trajectories, geofence_area)
        if collection_valid(tmp):
            trajectories = tmp
    
    if geofence_berths is not None:
        tmp = geofence(trajectories, geofence_berths)
        if collection_valid(tmp):
            trajectories = tmp
    
    if drop_speed_hike:
        tmp = speed_hike_filter(trajectories)
        if collection_valid(tmp):
            trajectories = tmp
    
    if smoothing:
        tmp = smooth(trajectories)
        if collection_valid(tmp):
            trajectories = tmp
    
    if split_by_time_gap:
        tmp = time_gap_split(trajectories)
        if collection_valid(tmp):
            trajectories = tmp
    
    if split_by_speed:
        tmp = speed_split(trajectories)
        if collection_valid(tmp):
            trajectories = tmp
    
    if split_by_stop:
        tmp = stop_split(trajectories)
        if collection_valid(tmp):
            trajectories = tmp

    return trajectories
