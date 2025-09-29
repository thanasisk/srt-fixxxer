#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Athanasios Kostopoulos"
__copyright__ = "Copyright 2025, Athanasios Kostopoulos"
__license__ = "MIT"
__version__ = "0.2"
__maintainer__ = "Athanasios Kostopoulos"
__email__ = "athanasios@akostopoulos.com"

import sys
import argparse
import re
import codecs
import datetime
from dateutil import parser

TIMESTAMP_RE = re.compile(r'\d\d:\d\d:\d\d,\d\d\d --> \d\d:\d\d:\d\d,\d\d\d')

def main() -> None:
    """
    Does what says in the tin
    """
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-o","--offset", help="positive or negative offset in seconds",type=int)
    argparser.add_argument("-s","--subtitle", help=".srt file to process",
                           type=argparse.FileType("r", encoding="utf-8"))
    args = argparser.parse_args()

    adjust_timestamp(args.subtitle.name, args.offset)

def adjust_timestamp(fname:str, offset:int) -> None:
    """
    Our entrypoint to timestamp processing.
    If line is a timestamp, it sends it further down the trough for processing
    If line is not, it gets printed "as-is"
    """
    with codecs.open(fname,"r",'utf-8') as ifile:
        for line in ifile:
            m = TIMESTAMP_RE.match(line)
            if not m:
                print(line.rstrip().lstrip())
            else:
                print(process_ts(m.group(0), offset))


def extract_timestamp(raw_ts_line:str , re_obj: re.Pattern) -> datetime.datetime:
    """
    Extracts a timestamp line, covertis it to a datetime object and sends it 
    for further processing
    """
    line = raw_ts_line.rstrip().lstrip()
    time_raw = re_obj.search(line).group(0)
    p_time = parser.parse(time_raw, ignoretz=True)
    return p_time

def process_ts(initial: datetime.datetime, offset:int ) -> str:
    """
    Returns an SRT compatible timestamp, adjusting the current one with offset 
    """
    tformat_start_re = re.compile(r'^\d\d:\d\d:\d\d,\d\d\d')
    tformat_end_re = re.compile(r'\d\d:\d\d:\d\d,\d\d\d$')
    t_start = extract_timestamp(initial, tformat_start_re)
    t_end = extract_timestamp(initial, tformat_end_re)
    delta = datetime.timedelta(seconds = offset)
    return f"{t_start + delta} --> {t_end + delta}"

if __name__ == '__main__':
    sys.exit(main())
