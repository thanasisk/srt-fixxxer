#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# srt_fixxer - srt subtitle multi-tool for the "AI ERA" :-{ 
# Copyright (C) 2025 Athanasios Kostopoulos

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__author__ = "Athanasios Kostopoulos"
__copyright__ = "Copyright 2025, Athanasios Kostopoulos"
__license__ = "GPLv3"
__version__ = "0.5"
__maintainer__ = "Athanasios Kostopoulos"
__email__ = "athanasios@akostopoulos.com"

import os
import sys
import argparse
import re
import codecs
import datetime
import asyncio
import pickle
import logging
import json
from functools import wraps # This convenience func preserves name and docstring

from dateutil import parser

from openai import OpenAI
import ai_imports

TIMESTAMP_RE = re.compile(r"\d\d:\d\d:\d\d,\d\d\d --> \d\d:\d\d:\d\d,\d\d\d")
logger = logging.getLogger(__name__)

def main() -> None:
    """
    Does what says in the tin
    """
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "-o", "--offset", help="positive or negative offset in seconds", type=int
    )
    argparser.add_argument(
        "-i",
        "--input",
        help=".srt file to process",
        required=True,
        type=argparse.FileType("r", encoding="utf-8"),
    )
    argparser.add_argument("-l", "--language", type=str, help="enters translate mode - selects language")
    argparser.add_argument(
        "-b", "--batch", type=int, default=20, help="batch size to speed up things"
    )
    argparser.add_argument(
        "-p", "--parallel", type=int, default=10, help="parallel batch processors"
    )
    argparser.add_argument("-e", "--engine", type=str, help="AI provider")
    argparser.add_argument("-v", "--verbose", action="store_true", help="be more verbose\ncreates pickles")
    argparser.add_argument("-q", "--quiet", action="store_true", help="reduce verbosity")
    argparser.add_argument("-r", "--recover", action="store_true",help="attempts a recovery from a pickled object")
    args = argparser.parse_args()
    lvl = logging.INFO
    if args.verbose:
        lvl = logging.DEBUG
    elif args.quiet:
        logging.CRITICAL
    logging.basicConfig(filename="fixxxer.log", filemode="w",level=lvl)
    console_handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(console_handler)
    logger.info("λ Started")
    if args.recover:
        # enter recover mode
        logger.info(f"λ Initiating recovery of {args.input.name}")
        if recover(args.input.name):
            logger.info(f"λ {args.input.name} recovered")
        else:
            logger.error(f"ε {args.input.name} failed to be recovered")
        sys.exit(0)
    if args.offset:
        # TODO: consider in place - for now let's drink some tee(1)
        adjust_timestamp(args.input.name, args.offset)
    if args.engine and args.language:
        ai_imports.load_ai_engine(args.engine)
        logger.info(f"λ Translating to {args.language} using {args.engine}")
    asyncio.run(
            translate_srt(
                args.input.name, args.language, args.batch, args.parallel, args.engine)
        )


def recover(srt_file: str) -> bool:
    success = False
    rec_file = 'translations.pcl'
    srt = (f"{'.'.join(srt_file.split(".")[:-1])}.rec.srt")
    with open(rec_file,"rb") as ifile:
        try:
            traws = pickle.load(ifile)
        except pickle.UnpicklingError:
            logger.error(f"ε {rec_file} appears to be corrupted")
            return False
        except FileNotFoundError:
            logger.error(f"ε {rec_file} is missing?")
            return false
        except PermissionError:
            logger.error(f"ε {rec_file} - you do not have pemrissions")
            return false
        with open(srt,"w") as ofile:
            for raw in traws:
                ofile.write(f"{raw['idx']}\n")
                ofile.write(f"{raw['ts']}\n")
                ofile.write(f"{raw['msg']}\n\n")
        success = True
    return success

def check_srt_filename(candidate: str) -> bool:
    checkee = candidate.split(".")
    if len(checkee) < 3:
        logger.warning(f"filename {candidate} is not well formatted as *.lang.srt")
        return False
    return True


# entry point for .srt translation
async def translate_srt(
    input_file, lang: str, batch_sz: int, conns: int, ai: str
) -> None:
    translations = []
    subtitles = parse_srt(input_file)
    logger.debug("Δ Sending lines for translation")
    logger.debug(f"subtitles {subtitles}")
    translations_raw = await translate_lines(
        subtitles, batch_size=batch_sz, lang=lang, conns=conns, ai=ai
    )

    #translations_raw = set(translations_raw)
    assert len(translations_raw) > 0, "Δ translations_raw are empty!"
    for t_raw in translations_raw:
        translations.append(t_raw)
    logger.debug(f"Δ translations_raw / translations: {len(translations_raw)} {translations_raw} / {len(translations)} {translations}")
    if logger.getEffectiveLevel() == logging.DEBUG:
        with open("translate_srt_translate_unsorted.pcl", "wb") as picklefile:
            pickle.dump(translations, picklefile)
    translations = sorted(translations, key=lambda translation: int(translation["idx"]))
    if logger.getEffectiveLevel() == logging.DEBUG:
        with open("translate_srt_translate.pcl", "wb") as picklefile:
            pickle.dump(translations, picklefile)
    assert len(translations) > 0, "Δ translations(sorted) are empty!"
    if check_srt_filename(input_file) is False:
        logger.error(
            f"invalid input filename: {input_file} - defaulting to output.{ai}.{lang}.srt"
        )
        output_fname = f"output.{ai}.{lang}.srt"
    else:
        stem = "".join(input_file.split(".")[:-2])
        output_fname = f"{stem}.{ai}.{lang}.srt"
        logger.info(f"Δ saving new srt at {output_fname}")
    with open(output_fname, "w") as ofile:
        for idx, translation in enumerate(translations):
            logger.debug(f"{idx} {translation}")
            if logger.getEffectiveLevel() == logging.DEBUG:
                with open(f"translation-{idx}.pcl", "wb") as picklefile:
                    picklefile.write(pickle.dumps(translation))
            cand = translation
            ofile.write(cand["idx"])
            ofile.write("\n")
            logger.debug(cand["idx"])
            ofile.write(cand["ts"])
            ofile.write("\n")
            logger.debug(cand["ts"])
            ofile.write(cand["msg"].lstrip().rstrip())
            logger.debug(cand["msg"].lstrip().rstrip())
            ofile.write("\n\n")

# Process lines in batches asynchronously
async def translate_lines(lines: list, batch_size: int, lang: str, conns: int, ai: str) -> list:
    assert conns > 0, "parallel is less than 1"
    assert batch_size > 0, "batch_size is less than 1"
    # allowed_AIs = ["xAI", "openAI", "nullAI"]
    #match ai.decode('utf-8').lower():
    match ai.lower():
        case "xai":
            client = openai.AsyncClient(
            api_key=os.getenv("XAI"),
            base_url="https://api.x.ai/v1",
            timeout=httpx.Timeout(3600.0), # Override default timeout with longer timeout for reasoning models
            )
        case "openai":
            client = openai.AsyncClient(
            api_key=os.getenv("OPENAI")
            # baseURL is already included
            timeout=httpx.Timeout(3600.0)
                    )
        case "deepseek":
            client = openai.AsyncClient(
            api_key=os.getenv("DEEPSEEK")
            base_url="https://api.deepseek.com"
            timeout=httpx.Timeout(3600.0)
                    )
        case "nullai":
            client = ai_imports.nullAI()
        case _:
            logger.critical(f"{ai} is NOT supported - Exiting!")
            sys.exit(1)
    translations = []
    logger.debug("Δ Split lines into batches")
    batches = [lines[i : i + batch_size] for i in range(0, len(lines), batch_size)]
    logger.debug(f"Δ {len(batches)} batches created")
    logger.debug(f"batches = {batches}")
    for b in batches:
        logger.debug(f"b = {b}")
    semaphore = asyncio.Semaphore(
        conns
    )  # Limit concurrent requests to avoid rate limits

    async def process_batch(batch: list):
        async with semaphore:
            return await translate_batch(client, batch, lang)

    # Run batches concurrently
    logger.debug("Δ Creating tasks")
    tasks = [process_batch(batch) for batch in batches]
    logger.debug(f"Δ Created tasks:{len(tasks)}")
    results = []
    async with asyncio.TaskGroup() as tg:
        for task in tasks:
            results.append(tg.create_task(task))
    logger.debug("Δ Tasks completed")
    assert len(results) > 0, "translate_lines: results is less than 1"
    logger.debug(f"Δ Results: {len(results)}")
    for batch_result in results:
        # TODO: consider rewriting with exception(
        if isinstance(batch_result, Exception):
            logger.error(f"Δ Error in batch: {batch_result}")
        else:
            # _asyncio.Task check?
            logger.debug(f"batch_result type: {type(batch_result)}")
            # woz: extend
            logger.debug(f"batch_result.result(): {batch_result.result()}")
            logger.debug(f"BUG: translations before append/extend: {translations}")
            translations.extend(batch_result.result())
            logger.debug(f"BUG: translations after append/extend: {translations}")
            # trying: append
            # translations.append(batch_result.result())
    logger.debug(f"translations = {translations}")
    translations_pickle = "translations.pcl"
    if logger.getEffectiveLevel() == logging.DEBUG:
        with open(f"{translations_pickle}","wb") as picklefile:
            pickle.dump(translations, picklefile)
            logger.debug(f"picklefile written: {translations_pickle}")
    assert len(translations) > 0, "Translations in translate_lines are less than 1"
    logger.debug(f"Δ Translations in translate_lines: {len(translations)}")
    return translations


async def translate_batch(
    client, lines: list, lang: str
) -> list:
    # TODO: error checking file stuff + json.decoder.JSONDecodeError:
    languages  = {}
    with open('languages.json', 'r') as lang_file:
        languages =  json.load(lang_file)
    language = languages[lang]
    logger.debug(f"Δ translating batch of {len(lines)} to {language}")
    logger.debug("Δ creating chat")
    translated = []
    for line in lines:
        chat = client.chat.create(
            model="grok-4",
            messages=[
                ai_imports.system(
                    f"Rewrite in {language}. Keep text as consice as needed so it can be used for subtitles \"as-is\""
                )
            ],
            temperature=0.3,  # Low temperature for precise translations
        )
        logger.debug(f"Δ Translating {line['msg']}")
        # 1st attempt: moving create outside the loop (which should be more efficient)
        # appends messages to be translated - I had a look into the docs AND asked Grok
        # looks like for the time being I am stuck with this
        chat.append(ai_imports.user(line["msg"]))
        response = await chat.sample()
        logger.debug(f"[GREPMEOUT] {line} -> {response.content}")
        line["msg"] = response.content
        # bug candidate
        translated.append(line)
    logger.debug(f"Δ Batch translated: {len(translated)}")
    return translated


def parse_srt(fname: str) -> list:
    logger.debug(f"Δ Parsing {fname}")
    translations = []
    with open(fname, "r") as ifile:
        ts = ""
        idx = ""
        msgs = []
        for line in ifile:
            line = line.rstrip().lstrip()
            m = TIMESTAMP_RE.match(line)
            if m:
                ts = line
            elif line.isdigit():
                idx = line # possible bug if say character in a move says 42!
            elif line == "":
                # this serves as our construct object-ish block
                # possible bug in join - should it be "\n" or ""
                translate_me = {"ts": ts, "idx": idx, "msg": " ".join(msgs)}
                logger.debug(f"translate_me: {translate_me}")
                translations.append(translate_me)
                msgs = []
                continue
            else:
                msgs.append(line)
    logger.debug(f"Δ srt parsed: {fname}")
    return translations


def adjust_timestamp(fname: str, offset: int) -> None:
    """
    Our entrypoint to timestamp processing.
    If line is a timestamp, it sends it further down the trough for processing
    If line is not, it gets printed "as-is"
    """
    with codecs.open(fname, "r", "utf-8") as ifile:
        for line in ifile:
            m = TIMESTAMP_RE.match(line)
            if not m:
                print(line.rstrip().lstrip())
            else:
                print(process_ts(m.group(0), offset))


def extract_timestamp(raw_ts_line: str, re_obj: re.Pattern) -> datetime.datetime:
    """
    Extracts a timestamp line, covertis it to a datetime object and sends it
    for further processing
    """
    line = raw_ts_line.rstrip().lstrip()
    time_raw = re_obj.search(line).group(0)
    p_time = parser.parse(time_raw, ignoretz=True)
    return p_time


def process_ts(initial: datetime.datetime, offset: int) -> str:
    """
    Returns an SRT compatible timestamp, adjusting the current one with offset
    """
    tformat_start_re = re.compile(r"^\d\d:\d\d:\d\d,\d\d\d")
    t_start = extract_timestamp(initial, tformat_start_re)
    delta = datetime.timedelta(seconds=offset)
    duration = datetime.timedelta(seconds=3)
    printable_start = (t_start + delta).strftime("%H:%M:%S,%f")
    printable_end = (t_start + delta + duration).strftime("%H:%M:%S,%f")
    return f"{printable_start[:-3]} --> {printable_end[:-3]}"

def add_method(cls):
    def decorator(func):
        @wraps(func) 
        def wrapper(self, *args, **kwargs): 
            return func(*args, **kwargs)
        setattr(cls, func.__name__, wrapper)
        return func # returning func means func can still be used normally
    return decorator


if __name__ == "__main__":
    sys.exit(main())
