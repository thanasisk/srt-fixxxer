# srt-fixxxer
A tool to process .srt files.
## Use Case
Kodi supports offsets up to 60 seconds, what if more is needed?
What if your language is not supported?
What if you want to batch process a ton of SRTs?
## Usage
- `"-o"` or `"--offset"` specify the time offset (granularity of seconds) to shift subtitle offset. Positive numbers introduce delay, negative move them ahead.
- `"-i"` or `"--input"` specifies the .srt file to process - this is required.
- `"-l"` or `"--language"` specifies the language - keep in mind, it does not follow the ISO standard and currently is geared towards Greek dialects.
- `"-b"` or `"--batch"` specifies the batch size - connecting to an API introduces latency so we try to minimize as much as possible. Defaults to 20.
- `"-p"` or `"--parallel"` specifies how many batches to process in parallel.
- `"-h"` or  `"--help"` shows a bit of help and exists
- `"-e"` or `"--engine"` ENGINE   AI provider - `nullAI` for debugging
- `"-v"` or `"--verbose"` be more verbose - it also  creates debugging pickles
- `"-q"` or `"--quiet"` reduce verbosity - only logging.CRITICAL are displayed

## Installation
`pip -r requirements.txt`

`python-dateutil` is a massive timesaver.

`xai-sdk` requires Python 3.10 or newer.
## "Languages" supported and what's up with country codes? Them ain't no ISO_3166-1 codes
Given that my use case is using this with [Kodi](https://kodi.tv/), I decided to override some [ISO_3166-1](https://en.wikipedia.org/wiki/ISO_3166-1) codes.

Below is the "language" reference:
```
        "el": "regular modern Greek",
        "il": "colloquial Greek from South-West Peloponesse region of Ilia",
        "kr": "Cretan dialect of Greek",
        "pt": "Pontic form of Greek",
        "bn": "βλαχικα form of Greek",
        "cl": "Katharevousa form of Greek",
        "re": "redneck US English",
        "gg": "late 80s/early 90s gangsta rap English",
        "tv": "80s Greek slang, made infamous from VHS of the era",
        "co": "modern corporate US English",
```

I follow standard `.srt` naming conventions so `foo.en.srt` translated to Pontic Greek becomes `foo.xai.pt.srt`

Coming soon(TM): load it dynamically from storage.

## Security? I downloaded an .srt and is now attacking the provider?!?
Your responsibility

## Hints and Tips
Different runs provide different results. Feel free to do multiple runs per language and cherry pick.

## License
GPLv3
