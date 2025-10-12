#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Athanasios Kostopoulos"
__copyright__ = "Copyright 2025, Athanasios Kostopoulos"
__license__ = "MIT"
__version__ = "0.3"
__maintainer__ = "Athanasios Kostopoulos"
__email__ = "athanasios@akostopoulos.com"

import os
import sys
import argparse
import re
import codecs
import datetime
import asyncio

from dateutil import parser

from xai_sdk import AsyncClient
from xai_sdk.chat import user, system

TIMESTAMP_RE = re.compile(r'\d\d:\d\d:\d\d,\d\d\d --> \d\d:\d\d:\d\d,\d\d\d')

def main() -> None:
    """
    Does what says in the tin
    """
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-o","--offset", help="positive or negative offset in seconds",type=int)
    argparser.add_argument("-i","--input", help=".srt file to process",
                           type=argparse.FileType("r", encoding="utf-8"))
    argparser.add_argument("-l","--language",type=str,default='el')
    argparser.add_argument("-b","--batch",type=int,default=20,help='batch size to speed up things')
    argparser.add_argument("-p","--parallel",type=int,default=10,help="parallel batch processors")
    args = argparser.parse_args()
    if args.offset:
        adjust_timestamp(args.input.name, args.offset)
    if args.language:
        print('[*] Translating')
        asyncio.run(translate_srt(args.input.name,args.language, args.batch, args.parallel))

# entry point for .srt translation
async def translate_srt(input_file, lang: str, batch_sz: int, conns: int) -> None:
    translations = []
    subtitles = parse_srt(input_file)
    print('[*] Sending lines for translation')
    translations_raw = await translate_lines(subtitles, batch_size=batch_sz, lang=lang, conns=conns)
    assert len(translations_raw) > 0, "[*] translations are empty!"
    for t_raw in translations_raw:
        translations.append(t_raw.result())
    # list_dict = [ { “num” =3, “name” = “A”}, {“num” = 1, “country” = “Europe”}]
    # sort_num = sorted(list_dict, key = lambda x : x[“num”])
    # FIXME: translation[0] only gives partial results
    translations = sorted(translations, key=lambda translation: translation[0]['idx'])
    assert len(translations) > 0, "[*] translations(sorted) are empty!"
    # translated_subtitles = [(index, timestamp, trans) for (index, timestamp, _), trans in zip(subtitles, translations)]
    # Combine subtitles with translations
    output_fname = f"output.{lang}.srt"
    with open(output_fname,'w') as ofile:
        for translation in translations:
            for cand in translation:
                ofile.write(cand['idx'])
                ofile.write("\n")
                print(cand['idx'])
                ofile.write(cand['ts'])
                ofile.write("\n")
                print(cand['ts'])
                ofile.write(cand['msg'].lstrip().rstrip())
                ofile.write("\n")
                ofile.write("\n")
                print(cand['msg'].lstrip().rstrip())


# Process lines in batches asynchronously
async def translate_lines(lines: list, batch_size: int, lang: str, conns: int) -> list:
    assert conns > 0, "parallel is less than 1"
    assert batch_size > 0, "batch_size is less than 1"
    client = AsyncClient(
        api_key=os.getenv("XAI"),
        timeout=3600,
    )
    translations = []
    print('[*] Split lines into batches')
    batches = [lines[i:i + batch_size] for i in range(0, len(lines), batch_size)]
    print(f'[*] {len(batches)} batches created')
    semaphore = asyncio.Semaphore(conns)  # Limit concurrent requests to avoid rate limits
    # FIXME Bug candidate
    async def process_batch(batch: list):
        async with semaphore:
            return await translate_batch(client, batch, lang)

    # Run batches concurrently
    print('[*] Creating tasks')
    tasks = [process_batch(batch) for batch in batches]
    print(f"[*] Created tasks:{len(tasks)}")
    results = []
    async with asyncio.TaskGroup() as tg:
        for task in tasks:
            results.append(tg.create_task(task))
    print("[*] Tasks completed")
    assert len(results) > 0, "translate_lines: results is less than 1"
    print(f"[*] Results: {len(results)}")
    for batch_result in results:
        if isinstance(batch_result, Exception):
            print(f"[*] Error in batch: {batch_result}")
        else:
            # woz: extend
            # perhaps here is the bug ...
            translations.extend(batch_result)
    assert len(translations) > 0, "Translations in translate_lines are less than 1"
    print(f"[*] Translations in translate_lines: {len(translations)}")
    return translations

async def translate_batch(client: xai_sdk.aio.client.Client, lines: list, lang: str) -> list:
    print(f'[*] translating batch of {len(lines)}')
    print("[*] creating chat")
    languages = {
        "el": "colloquial Greek from South-West Peloponesse region",
        "kr": "Cretan dialect of Greek",
        "pt": "Ponti formc Greek",
        "bn": "βλαχικα form of Greek",
        "cl": "Katharevousa form of Greek",
        "re": "redneck US English",
        "gg": "late 80s/early 90s gangsta rap English",
        "tv": "80s Greek slang, made infamous from VHS of the era",
        "co": "modern corporate US English"
            }
    # TODO: error checking
    language = languages[lang]
    chat = client.chat.create(
        model="grok-4",
        messages=[system(f"Translate to {language}, keeping text concise for subtitles so it can be copied and pasted")],
        temperature=0.3  # Low temperature for precise translations
    )
    translated = []
    for line in lines:
        print(f"[*] Translating {line['msg']}")
        chat.append(user(line['msg']))
        response = await chat.sample()
        print(f"[GREPMEOUT] {line} -> {response.content}")
        line['msg'] = response.content
        translated.append(line)
    print('[*] Batch translated')
    return translated

def parse_srt(fname: str) -> list:
    print(f'[*] Parsing {fname}')
    translations = []
    with open(fname,"r") as ifile:
        ts = ""
        idx = ""
        msg = ""
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
                translations.append({'ts': ts, 'idx': idx, 'msg': "\n".join(msgs)})
                msgs = []
                continue
            else:
                msgs.append(line)
    print('[*] srt parsed')
    return translations

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
    duration = datetime.timedelta(seconds = 3)
    printable_start = (t_start + delta).strftime("%H:%M:%S,%f")
    printable_end = (t_start + delta + duration).strftime("%H:%M:%S,%f")
    return f"{printable_start[:-3]} --> {printable_end[:-3]}"

if __name__ == '__main__':
    sys.exit(main())
