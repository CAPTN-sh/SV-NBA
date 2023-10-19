import os
import sys
sys.path.append("../")

from datetime import date, datetime, time, timedelta
from dataclasses import dataclass
from itertools import combinations
from time import sleep
import multiprocessing

import ast
import numpy as np
import pandas as pd
from pandas import concat, DataFrame

from geopandas import points_from_xy, GeoDataFrame, GeoSeries
from movingpandas import Trajectory, TrajectoryCollection, ObservationGapSplitter
from shapely import Point, Polygon
from shapely.ops import nearest_points

from src.macros.macros import ANALYSIS_STEP_SIZE, ASSESSMENT_RANGE, ACTION_RANGE, NUM_NEAREST_SHIPS, COLUMNS_NEAREST_SHIPS

from src.utils.geo_calc.interpolate import pchip_traj_interpolate_at
from src.utils.geo_calc.geo import _point_to_tuple
from src.assemble.assemble import ShipTrip
from src.utils.metrics import abs_bearing_and_distance, rel_bearing
from src.utils.geo_calc.geo import _point_to_tuple, get_geo_distance
from src.utils.metrics import get_abs_bearings, get_rel_bearings, relative_speed
from src.utils.geo_calc.ship import Ship, CAPTN_POINT
from src.utils.geo_calc.cpa import itterative_cpa

from src.assemble.assemble import *

# hard coded dates to loop through in the analysis
START_DATE = date(2022, 3, 24)
END_DATE = date(2023, 6, 30)

def daterange(start_date: date, end_date: date):
    """Iterator yielding each new date in between start_date and end_date."""
    for n in range(int((end_date - start_date).days)+1):
        yield start_date + timedelta(n)


def timerange(loop_date: datetime,
              step_size: timedelta = ANALYSIS_STEP_SIZE):
    """Iterator yielding each time point on loop date for given step size."""
    if isinstance(loop_date, date):
        loop_date = datetime.combine(loop_date, time())
    # stops ar 23:57 o'clock, add +1 to include midnight of next day
    for n in range(int(timedelta(days=1) / step_size) + 1):
        yield loop_date + n * step_size


def get_active_ships(dt: datetime, ship_trips):
    """Returns all ship trips containing trajectory data for given time dt."""
    out_buffer = []

    for s in ship_trips:
        if (s.start_time <= dt) and (dt <= s.end_time):
            out_buffer.append(s)

    return out_buffer


def get_active_trajectory(dt: datetime, ship_trip):
    """Returns the active trajectory data for given time dt."""
    id = None
    active = None

    for num, trajectory in enumerate(ship_trip.trajectories):
        if ((trajectory.get_start_time() <= dt) and
                (dt <= trajectory.get_end_time())):
            id = num
            active = trajectory
            break

    return (id, active)


### helper function for converting [str ...] to np.array [mmsi ...]
def str_to_nparray(array_string):
            array_string = ','.join(array_string.replace('[ ', '[').split())
            return np.array(ast.literal_eval(array_string))


@dataclass
class ShipFeatures:
    
    # 'mmsi'
    # 'imo'
    # 'ship_type'
    # 'length'
    # 'width'
    # 'draught'
    # 'tonnage'
    # 'volume'
    static: dict
    
    # epoch (actual index)
    # date (from traj.df)
    # rate of AIS transmissions
    # nav. status
    # heading
    # COG
    # SOG
    # ROT
    # interp. Position
    own: DataFrame

    # interp. heading
    # interp. COG
    # interp. SOG
    # interp. ROT
    # acceleration

    # active
    s2s: DataFrame

    def __init__(self, ship_info) -> None:
        self.static = ship_info
        self.own = DataFrame()
        
        self.s2s = DataFrame()

    def __repr__(self) -> str:
        rep_str = f"{{static: {self.static}, \n"
        rep_str = rep_str + f"own: {self.own}, \n"
        rep_str = rep_str + f"s2s: {self.s2s}, \n"
        
        return rep_str


def _calc_own_features(ship_trips,
                       ship_features,
                       current_date):
    
    # initial time step at 00:00:00 on current_date
    t_prev = datetime(current_date.year,
                        current_date.month,
                        current_date.day)

    active_ships_df = DataFrame()

    ########################################################
    ### Main Loop: sample the data in discrete time steps ###
    #########################################################
    for t in timerange(current_date):

        active = get_active_ships(t, ship_trips)

        # collect the mmsi of all active ships at t
        active_ships_df = concat([
            active_ships_df,
            DataFrame(data={"t": [t], 
                            "active_ships": [np.array([a.mmsi for a in active])]
                            }).set_index("t")
        ])
        # save those as a column in s2s csv later

        ### iterate through active ships at time t ###
        for sample in active:

            active_id, active_trajectory = get_active_trajectory(t, sample)

            if active_trajectory is None:
                continue

            ### get own ship features ###
            data = active_trajectory.get_row_at(t)

            features = {}
            features["t"] = [t]    
            features["epoch"] = [data["epoch"]]
            features["status"] = [data["status"]]
            features["heading"] = [data["heading"]]
            features["course"] = [data["course"]]
            features["speed"] = [data["speed"]]
            features["turn"] = [data["turn"]]
            features["maneuver"] = [data["maneuver"]]
            
            # t is discrete time step
            # create time interval inter from t-1 to t, 
            # and extract the namuber of rows (i.e. AIS signals) in inter
            mask = active_trajectory.df.index.indexer_between_time(
                t_prev.time(),
                t.time(),
                include_start=True,
                include_end=True)

            roa = len(active_trajectory.df.iloc[mask].index)
            features["roa"] = [roa]

            ### 2. get interpolated values for position, speed etc.
            ### these are the calculated values for heading, speed and so on, as in the papers
            
            # interp. Position
            t_epoch = int(t.timestamp())
            inter_values = pchip_traj_interpolate_at(active_trajectory,
            # interpolated_pos = active_trajectory.interpolate_position_at(t)
                                                        t_epoch)
            features["inter_lat"] = inter_values["lat"]
            features["inter_lon"] = inter_values["lon"]
            features["inter_speed"] = inter_values["speed"]
            features["inter_turn"] = inter_values["turn"]

            ### trajectory point features ###

            # increasing id for each subtrajectory i: 0 <= i <= n
            features["traj_id"] = active_id
            
            df = DataFrame.from_dict(features, 
                                        orient='columns',
                                    #  dtype=None, 
                                    #  columns=None
                                    )
            df.set_index('t', inplace=True)


            ship_features[sample.mmsi].own = concat(
                [ship_features[sample.mmsi].own, df]
                )  
            
            # update t-1 time step
            t_prev = t

    return ship_features, active_ships_df


def _add_calculated_features(ship_list):

    ########################################
    ### add calculated features per mmsi ###
    ########################################
    for s_mmsi, s_features in ship_list.items():

        # add mmsi column
        s_features.own['mmsi']= s_mmsi

        # setup
        results = []
        s_features.own[["calc_speed", 
                        "direction", 
                        "angular_difference", 
                        "calc_acc"]] = np.NaN
        
        # Group by "traj_id" and create Trajectory objects
        by_group = s_features.own.groupby("traj_id")
        for traj_id, group in by_group:

            # base trajectory for mpd functions
            traj = Trajectory(group,
                            traj_id=traj_id,
                            obj_id=s_mmsi,
                            t="t", 
                            x="inter_lat",
                            y="inter_lon",
                            crs="epsg:4326")
            
            # calculated SOG
            traj.add_speed(overwrite=True,
                        name="calc_speed",
                        units=("nm", "h")
                        )
            
            # calculated COG
            traj.add_direction(overwrite=True,
                            name="direction"
                        )        
            
            # calculated ROT
            traj.add_angular_difference(overwrite=True)
            
            # calculated acceleration
            traj.add_acceleration(overwrite=True,
                                name="calc_acc",
                                units=("nm", "h", "h")
                                )

            # add interpolated positions            
            traj.df["inter_lat"] = traj.df.geometry.x
            traj.df["inter_lon"] = traj.df.geometry.y

            # buffer to be concatenated next
            results.append(traj.df)

        # collect the new data frames from grouping and overwrite
        s_features.own = concat(results)

    return ship_list


def add_within_waterways(gdf: GeoDataFrame,
                         geom: Polygon):
    ### working within_waterways feature ###
    gdf['in_waterways'] = gdf.geometry.apply(lambda x: x.within(geom)).astype(int)

    return gdf


def add_distance_shoreline(gdf: GeoDataFrame,
                           geom: Polygon):
    
    # get polygon's nearest point for each point in geometry
    n = gdf.geometry.apply(lambda x: nearest_points(geom, x)[0])
    n.columns = ["geometry"]


    pts = DataFrame(gdf.geometry)
    pts['n_pts'] = pts["geometry"].apply(
        lambda x: nearest_points(geom, x)[0])    

    # get geo distance returns in kilometer
    gdf["distance_shore"] = pts.apply(lambda x:
                        get_geo_distance(x["geometry"], 
                                         x["n_pts"]),
                        axis=1)

    return gdf


def dump_own_features(src, trg, ship_features, active_ships, dt):

    #####################################
    ### save the feature data to disk ###
    #####################################

    # > SVNBA
    # >   src
    # >   assets
    # >      csv
    # >         2022-03-24 (base_path)
    # >            2022-03-24_base_s2s.csv
    # >            2022-03-24_mmsi_own.csv
    # >            2022-03-24_mmsi_static.csv

    base_path = os.path.join(trg, str(dt))
    
    if not os.path.isdir(base_path):
        os.mkdir(base_path)

    ########################################
    ### static and own features per mmsi ###
    ########################################

    for sm, sf in ship_features.items():

        ship_suffix = str(dt) + "_" + str(sm)
        ship_path = os.path.join(base_path, ship_suffix)

        # static features
        static_df = concat([DataFrame(), 
                            DataFrame({k:[v] for k,v in sf.static.items()})])
        
        static_df.to_csv(ship_path + "_static.csv", index=True)

        # own fearures
        own_df = sf.own.drop(columns='geometry')
        own_df.to_csv(ship_path + "_own.csv", index=True)

    # s2s features (per full day)
    s2s_df = active_ships    
    s2s_df.to_csv(os.path.join(base_path, str(dt)) + "_s2s_base.csv", 
                  index=True)

    return 0


def calculate_own_features(ship_trips, 
                           src, 
                           trg, 
                           current_date,
                           waterways: Polygon = None,
                           shoreline: Polygon = None):
    
    ### create dictionary of ship features, indexed by mmsi
    ship_features = {}
    for trip in list(ship_trips):
        ship_features[trip.mmsi] = ShipFeatures(trip.ship_info)

    # calculate the base ais features (up to lat/lon interpol.)

    ship_features, active_ships = _calc_own_features(ship_trips, 
                                                     ship_features, 
                                                     current_date)

    # add the interpolated features from the mpd calculations
    ship_features = _add_calculated_features(ship_features)

    # add ship to geo features
    for gdf in ship_features.items():
        gdf = add_within_waterways(gdf, waterways)
        gdf = add_distance_shoreline(gdf, shoreline)

    # save the calculated features on disc
    rc = dump_own_features(src, trg, ship_features, active_ships, current_date)

    return 0


def calculate_s2s_metrics(s2s_df,
                          own_features,
                          current_date,
                          all_mmsis,
                          ITERATION_STEP_SIZE):
    
    ## big dataframes! 
    ## mmsi -> df (indexes t)
    s2s_dataframes_to_dump = {}
    for mmsi in all_mmsis:
        s2s_dataframes_to_dump[mmsi] = DataFrame()

    ### main analysis loop in discrete time steps t ###
    ################### s2s features ##################
    for t in timerange(current_date):

        # #TODO remove before parallel
        # if t > datetime.combine(current_date,
        #                         time(hour=0, minute=10, second=0)):
        #     break
        # pprint(str(t))

        active_ships = s2s_df.loc[t]['active_ships']

        #TODO fix the bandaid code
        # there are phantom active ships in s2s_base df!!!!!!!!!!!!!!!!
        for mmsi in active_ships:
            if own_features[mmsi][own_features[mmsi].index == t].empty:
                # remove erranously 'active' mmsis
                active_ships = np.delete(active_ships, 
                                         np.where(active_ships == mmsi)
                                         )
                continue

        # buffers the calculated features per mmsi 
        # (all combinations with mmsi_1 occurring)
        buffer = {}
        for a_mmsi in active_ships:
            buffer[a_mmsi] = []

        #TODO implement additional combinations loop to filter out NUM
        # nearest ships by distance first

        for mmsi_1, mmsi_2 in list(combinations(active_ships, 2)):
            # pprint("calculate s2s metrics for: ")
            # pprint("pair: ", mmsi_1, mmsi_2)

            ### get interpolated values ###
            lat1 = own_features[mmsi_1].loc[t]['inter_lat']
            lon1 = own_features[mmsi_1].loc[t]['inter_lon']

            lat2 = own_features[mmsi_2].loc[t]['inter_lat']
            lon2 = own_features[mmsi_2].loc[t]['inter_lon']

            # COG from interpolation
            cog1 = own_features[mmsi_1].loc[t]['direction']    
            cog2 = own_features[mmsi_2].loc[t]['direction']
            
            # speed from interpolation
            sog1 = own_features[mmsi_1].loc[t]['calc_speed']    
            sog2 = own_features[mmsi_2].loc[t]['calc_speed']
    
            ########################################
            ### calculate the s2s metrics values ###
            ########################################

            ### absolute bearings, distance ###
            # return {'abs_bearing_12':abs_bearing_12, 
            #         'abs_bearing_21': abs_bearing_21}
            r_dict = get_abs_bearings(lat1=lat1,
                                    lon1=lon1, 
                                    lat2=lat2, 
                                    lon2=lon2)
            
            abs_bearing_12 = r_dict["abs_bearing_12"]
            abs_bearing_21 = r_dict["abs_bearing_21"]


            ### relative bearings ###
            #     return {'rel_bearing_12': rel_bearing_12, 
            #             'rel_bearing_21': rel_bearing_21}
            r_dict = get_rel_bearings(lat1= lat1, 
                                      lon1= lon1, 
                                      heading1= cog1,   # interpolated cog
                                      lat2= lat2, 
                                      lon2= lon2, 
                                      heading2= cog2    # interpolated cog
                                    )
            
            rel_bearing_12 = r_dict["rel_bearing_12"]
            rel_bearing_21 = r_dict["rel_bearing_21"]
            
            ### CPA ###
            ship_1 = Ship(position=CAPTN_POINT(
                latitude=lat1,
                longitude=lon1),
                speed= sog1,
                course= cog1)

            ship_2 = Ship(position=CAPTN_POINT(
                latitude=lat2,
                longitude=lon2),
                speed=sog2,
                course=cog2)

            #TODO reduce 6h calculatoin max. depth
            cpa_obj, _ = itterative_cpa(_ship1=ship_1,
                                        _ship2=ship_2,
                                        geo_fence=None,
                                        time_step_size=ITERATION_STEP_SIZE)

            # the interaction that ships are in (converging/diverging)
            interaction = cpa_obj.interaction   

            tcpa1 = cpa_obj.ship1.tcpa
            dcpa1 = cpa_obj.ship1.dcpa
            c_lat1, c_lon1 = cpa_obj.ship1.postion.as_tuple() # crash position
            
            tcpa2 = cpa_obj.ship2.tcpa
            dcpa2 = cpa_obj.ship2.dcpa
            c_lat2, c_lon2 = cpa_obj.ship2.postion.as_tuple() # crash position


            ### distance ###
            
            # vicinity formula
            ships_distance = get_geo_distance(a= (lat1,lon1),
                                              b=(lat2, lon2),
                                              distance_unit="nm" 
                                              ) 

            ### rel. speed ###
            
            rel_speed = relative_speed(speed1=sog1,
                           course1=cog1,
                           speed2=sog2,
                           course2=cog2)

            ###########################################
            ### prepare the output per mmsi in pair ###
            ###########################################

            ## 1.
            ## per mmsi_1 /mmsi_2 
            ## 'data' dict
            data_1 = {}
            data_1["mmsi1"] = mmsi_1         # src ship
            data_1["mmsi2"] = mmsi_2         # relative ship
            data_1["lat"] = lat1
            data_1["lon"] = lon1
            data_1["cog"] = cog1
            data_1["sog"] = sog1
            data_1["abs_bearing"] = abs_bearing_12   # abs_bearing12
            data_1["rel_bearing"] = rel_bearing_12
            data_1["tcpa"] = tcpa1
            data_1["dcpa"] = dcpa1
            data_1["c_lat"] = c_lat1
            data_1["c_lon"] = c_lon1
            data_1["ships_distance"] = ships_distance
            data_1["rel_speed"] = rel_speed

            data_2 = {}
            data_2["mmsi1"] = mmsi_2         # src ship
            data_2["mmsi2"] = mmsi_1         # relative ship
            data_2["lat"] = lat2
            data_2["lon"] = lon2
            data_2["cog"] = cog2
            data_2["sog"] = sog2
            data_2["abs_bearing"] = abs_bearing_21   # abs_bearing21
            data_2["rel_bearing"] = rel_bearing_21
            data_2["tcpa"] = tcpa2
            data_2["dcpa"] = dcpa2
            data_2["c_lat"] = c_lat2
            data_2["c_lon"] = c_lon2
            data_2["ships_distance"] = ships_distance
            data_2["rel_speed"] = rel_speed
            
            ####################################################
            ### append to appropriate buffer (with mmsi key) ###
            ####################################################
            ## 2. append 'data's to buffer[mmsi_1] (int key)

            buffer[mmsi_1].append(data_1)
            buffer[mmsi_2].append(data_2)

        ### end combinations loop
        
        # calculate distances between nearest ships
        for mmsi, buffered_dicts in buffer.items():

            sorted_dicts = sorted(buffered_dicts, 
                             key=lambda d: d['ships_distance'])
            
            if len(sorted_dicts) > NUM_NEAREST_SHIPS:
                sorted_dicts = sorted_dicts[:NUM_NEAREST_SHIPS]

            ## prepare df for row at index t
            data_columns = {"t": [t],
                            "mmsi": [mmsi]}
            for i, d in enumerate(sorted_dicts):

                # d.key + num in sorted -> data_columns key
                for key, value in d.items():
                    # drop the 'own' identity mmsi1 columns
                    if key == "mmsi1":
                        continue
                    data_columns[key+"_"+str(i)] = [value]

            ## prepare row df
            row = DataFrame(data_columns)
            row.set_index("t", inplace=True)

            ## concat to 'big' mmsi_s2s dataframe for saving to disc
            # s2s_dataframes_to_dump = big dict
            s2s_dataframes_to_dump[mmsi] = concat(
                [s2s_dataframes_to_dump[mmsi], row],
                axis=0
                )
        ## end mmsi loop
    ### end time loop

    # exit calculation successfully
    return s2s_dataframes_to_dump