import os
from glob import glob
from typing import List, Tuple
from datetime import datetime

from pyais import decode
from pyais.exceptions import (InvalidNMEAMessageException,
                              MissingMultipartMessageException,
                              NonPrintableCharacterException,
                              TooManyMessagesException,
                              UnknownMessageException)

import sys
sys.path.append("../")
from src.macros.macros import POS_REP_MSG_TYPES, VOY_REL_MSG_TYPES, EQU_POS_MSG_TYPES


def decode_file_data(data: List[str], delimeter="-") -> List[dict]:
    """Decode ais messages from string buffer.
    args
        data: 
        Array of strings, each containing a timestamp in unix epoch format and an individual ais message.

        delimeter:
        The delimeter separating the timestamp and message.

        example:
        1697122974.811436-!AIVDO,1,1,,,13:4m15000PfQ=pO5IcR4Qcd0000,0*7A

    returns
        Array of dictionaties with 'timestamp' containing the float value of the unix epoch time the message was recorded, and the values of the decoded messages, passed down from pyais.
    """
    data_buffer=[]

    # internal array and indexing to store parts of multi-line messages before they can be decoded
    #   key: see slot, 
    #   values: list of strings holding the message sentences
    nmea_buffer: dict[tuple[str, int], list[str | bytes | None]] = {}
    # tuple of channel 'A' or 'B' and frag_count, together form unique identifier
    slot: tuple[str, int]

    for line in data:
        ts, msg = line.split("-")

        # extract fragment count and sequential fragment number
        parts = msg.split(',')
        if len(parts) < 7:
            # valid position reports and voyage data have seven message parts
            continue

        (sentence_type, frag_c, frag_n, _ , channel, _, _) = parts
        frag_count = int(frag_c)
        frag_num = int(frag_n)

        # message channel ('A' or 'B') and fragment count constitute a unique identifier the messages
        # if a multiline message M on channel X is being sent, X will be blocked for other transeivers until the last part of M is received
        slot = (channel,frag_count)
        
        if slot not in nmea_buffer:
            nmea_buffer[slot] = [None, ] * frag_count
            
        # in case of missing fragments, overwrite the bufferd (not to be completed) message fragments
        nmea_buffer[slot][frag_num - 1] = msg

        # if all fragments of current message are present, decode the message and buffer the result for processing with its timestamp in the next step
        if None not in nmea_buffer[slot]:                        
            try:
                decoded=decode(*nmea_buffer[slot]).asdict()

            except (InvalidNMEAMessageException, 
                    MissingMultipartMessageException,
                    NonPrintableCharacterException,
                    TooManyMessagesException,
                    UnknownMessageException) as err:
                print(f"Error in decoding by pyais, error msg: {err}")
                continue

            data_buffer.append(dict({"epoch": float(ts)}, **decoded))
            del nmea_buffer[slot]

    return data_buffer


#TODO annotate return
def split_by_message_type(data: List[dict]) -> Tuple[List[dict], List[dict], List[dict]]:
    """Split array of dicts containing parsed ais information into distinct types.
    """

    pos_rep_buffer=[]
    voy_rel_buffer=[]
    equ_pos_buffer=[]   # optional: not implemented

    for d in data:
        if d['msg_type'] in POS_REP_MSG_TYPES:
            pos_rep_buffer.append(d)

        elif d['msg_type'] in VOY_REL_MSG_TYPES:
            voy_rel_buffer.append(d)

        elif d['msg_type'] in EQU_POS_MSG_TYPES:
            equ_pos_buffer.append(d)
        
    return (pos_rep_buffer, voy_rel_buffer, equ_pos_buffer)