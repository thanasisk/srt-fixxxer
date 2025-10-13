#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Athanasios Kostopoulos"
__copyright__ = "Copyright 2025, Athanasios Kostopoulos"
__license__ = "MIT"
__version__ = "0.4"
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
from functools import wraps # This convenience func preserves name and docstring

from dateutil import parser

#import xai_sdk
from xai_sdk import AsyncClient
from xai_sdk.chat import user, system

TIMESTAMP_RE = re.compile(r"\d\d:\d\d:\d\d,\d\d\d --> \d\d:\d\d:\d\d,\d\d\d")
logger = logging.getLogger(__name__)

class nullAI:
    def __init__(self, chat):
        self.chat = chat

class ChatResponse:
    def __init__(self, content):
        self.content = content
    def append(self, extra):
        self.content += str(extra)
    async def sample(self):
        return self.content

class chat:
    def __init__(self):
        self.response = ChatResponse("FIXED RESPONSE")  # Now it's properly initialized

    def create(self,model,messages,temperature):
        return self.response

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
    argparser.add_argument("-l", "--language", type=str, default="el")
    argparser.add_argument(
        "-b", "--batch", type=int, default=20, help="batch size to speed up things"
    )
    argparser.add_argument(
        "-p", "--parallel", type=int, default=10, help="parallel batch processors"
    )
    argparser.add_argument("-a", "--ai", type=str, default="nullAI", help="AI provider")
    argparser.add_argument("-v", "--verbose", action="store_true", help="be more verbose\ncreates pickles")
    argparser.add_argument("-q", "--quiet", action="store_true", help="reduce verbosity")
    args = argparser.parse_args()
    # TODO: make it conditional
    if args.verbose: 
        logging.basicConfig(filename="fixxxer.log", level=logging.DEBUG)
    elif args.quiet:
        logging.basicConfig(filename="fixxxer.log", level=logging.CRITICAL)
    else:
        logging.basicConfig(filename="fixxxer.log", level=logging.INFO)
    logger.info("Started")
    if args.offset:
        # TODO: currently uses tee(1) - make the change in place?
        adjust_timestamp(args.input.name, args.offset)
    if args.language:
        logger.info("[*] Translating")
    asyncio.run(
            translate_srt(
                args.input.name, args.language, args.batch, args.parallel, args.ai)
        )


def check_srt_filename(candidate: str) -> bool:
    checkee = candidate.split(".")
    if len(checkee) < 3:
        logger.error(f"filename {candidate} is not well formatted as *.lang.srt")
        return False
    return True


# entry point for .srt translation
async def translate_srt(
    input_file, lang: str, batch_sz: int, conns: int, ai: str
) -> None:
    translations = []
    subtitles = parse_srt(input_file)
    logger.debug("[*] Sending lines for translation")
    translations_raw = await translate_lines(
        subtitles, batch_size=batch_sz, lang=lang, conns=conns, ai=ai
    )
    assert len(translations_raw) > 0, "[*] translations_raw are empty!"
    for t_raw in translations_raw:
        translations.append(t_raw.result())
    # list_dict = [ { “num” =3, “name” = “A”}, {“num” = 1, “country” = “Europe”}]
    # sort_num = sorted(list_dict, key = lambda x : x[“num”])
    # FIXME: translation[0] only gives partial results
    translations = sorted(translations, key=lambda translation: translation[0]["idx"])
    with open("translate_srt_translate.pcl", "w") as picklefile:
        picklefile.write(pickle.dumps(translations))
    assert len(translations) > 0, "[*] translations(sorted) are empty!"
    # translated_subtitles = [(index, timestamp, trans) for (index, timestamp, _), trans in zip(subtitles, translations)]
    # Combine subtitles with translations
    # some sanity checks about filename format - we expect it to be W/E.lang.srt
    if check_srt_filename(input_file) is False:
        logger.error(
            f"invalid input filename: {input_file} - defaulting to output.{ai}.{lang}.srt"
        )
        output_fname = f"output.{ai}.{lang}.srt"
    else:
        stem = "".join(input_file.split(".")[:-2])
        output_fname = f"{stem}.{ai}.{lang}.srt"
    with open(output_fname, "w") as ofile:
        logger.info("saving new srt at {output_fname}")
        for idx, translation in translations:
            # TODO: make it conditional
            with open(f"translation-{idx}.pcl", "wb") as picklefile:
                picklefile.write(pickle.dumps(translation))
            for cand in translation:
                ofile.write(cand["idx"])
                ofile.write("\n")
                logger.debug(cand["idx"])
                ofile.write(cand["ts"])
                ofile.write("\n")
                logger.debug(cand["ts"])
                ofile.write(cand["msg"].lstrip().rstrip())
                ofile.write("\n")
                ofile.write("\n")
                logger.debug(cand["msg"].lstrip().rstrip())

def mock_create():
    pass
def mock_sample():
    pass
def mock_append():
    pass
# Process lines in batches asynchronously
async def translate_lines(lines: list, batch_size: int, lang: str, conns: int, ai: str) -> list:
    assert conns > 0, "parallel is less than 1"
    assert batch_size > 0, "batch_size is less than 1"
    # allowed_AIs = ["xAI", "openAI", "nullAI"]
    #match ai.decode('utf-8').lower():
    match ai.lower():
        case "xai":
            client = AsyncClient(
            api_key=os.getenv("XAI"),
            timeout=3600, # Override default timeout with longer timeout for reasoning models
            )
            pass
        case "nullai":
            client = nullAI(chat=chat())
        case _:
            logger.critical(f"{ai} is NOT supported - Exiting!")
            sys.exit(1)
    translations = []
    logger.debug("[*] Split lines into batches")
    batches = [lines[i : i + batch_size] for i in range(0, len(lines), batch_size)]
    logger.debug(f"[*] {len(batches)} batches created")
    semaphore = asyncio.Semaphore(
        conns
    )  # Limit concurrent requests to avoid rate limits

    # FIXME Bug candidate
    async def process_batch(batch: list):
        async with semaphore:
            return await translate_batch(client, batch, lang)

    # Run batches concurrently
    logger.debug("[*] Creating tasks")
    tasks = [process_batch(batch) for batch in batches]
    logger.debug(f"[*] Created tasks:{len(tasks)}")
    results = []
    async with asyncio.TaskGroup() as tg:
        for task in tasks:
            results.append(tg.create_task(task))
    logger.debug("[*] Tasks completed")
    assert len(results) > 0, "translate_lines: results is less than 1"
    logger.debug(f"[*] Results: {len(results)}")
    for batch_result in results:
        if isinstance(batch_result, Exception):
            logger.error(f"[*] Error in batch: {batch_result}")
        else:
            # woz: extend
            # perhaps here is the bug ...
            translations.extend(batch_result)
    translations_pickle = "translations.pcl"
    with open(f"{translations_pickle}","w") as picklefile:
        picklefile.write(pickle.dumps(translations))
        logger.debug(f"picklefile written: {translations_pickle}")
    assert len(translations) > 0, "Translations in translate_lines are less than 1"
    logger.debug(f"[*] Translations in translate_lines: {len(translations)}")
    return translations


async def translate_batch(
    client, lines: list, lang: str
) -> list:
    languages = {
        "el": "regular modern Greek",
        "il": "colloquial Greek from South-West Peloponesse region of Ilia",
        "kr": "Cretan dialect of Greek",
        "pt": "Ponti formc Greek",
        "bn": "βλαχικα form of Greek",
        "cl": "Katharevousa form of Greek",
        "re": "redneck US English",
        "gg": "late 80s/early 90s gangsta rap English",
        "tv": "80s Greek slang, made infamous from VHS of the era",
        "co": "modern corporate US English",
    }
    # TODO: error checking
    language = languages[lang]
    logger.debug(f"[*] translating batch of {len(lines)} to {language}")
    logger.debug("[*] creating chat")
    chat = client.chat.create(
        model="grok-4",
        messages=[
            system(
                f"please translate to {language}, keeping text concise for subtitles so it can be copied and pasted"
            )
        ],
        temperature=0.3,  # Low temperature for precise translations
    )
    translated = []
    for line in lines:
        logger.debug(f"[*] Translating {line['msg']}")
        # FIXME: bug candidate
        chat.append(user(line["msg"]))
        response = await chat.sample()
        logger.debug(f"[GREPMEOUT] {line} -> {response.content}")
        line["msg"] = response.content
        # bug candidate
        translated.append(line)
    logger.debug(f"[*] Batch translated: {len(translated)}")
    return translated


def parse_srt(fname: str) -> list:
    logger.debug(f"[*] Parsing {fname}")
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
                idx = line
            elif line == "":
                # this serves as our construct object-ish block
                msgs.append("")
                # possible bug in join - should it be "\n" or ""
                translations.append({"ts": ts, "idx": idx, "msg": "\n".join(msgs)})
                msgs = []
                continue
            else:
                msgs.append(line)
    logger.debug(f"[*] srt parsed: {fname}")
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
