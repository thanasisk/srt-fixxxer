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

Languages are loaded dynamically from `languages.json` - it is your responsibility to make sure it is valid JSON and nothing funky or malicious is there.
This file is your responsibility to create, as everyone has their own needs and is ignored by `git`.

Below is an example "language" reference.
```
{
"el": "Standard Modern Greek",
"il": "colloquial Ilia (SW Peloponnese) Greek dialect: rural 'redneck' style with tsitsakism  vowel shifts, Turkish loanse, earthy swears, villager and farmer proverbs. Guttural, village taverna banter about land/feuds—slow & blunt, definitealy not urban. Monotonic Greek",
"kr": "Cretan dialect of Greek",
"pt": "Pontic form of Greek",
"bn": "βΔαχικα form of Greek",
"cl": "Katharevousa form of Greek",
"ag": "Ancient Greek, Attic dialect",
"me": "Medieval Greek",
"ae": "Archaic English",
"ap": "Appalachian Vernacular English",
"re": "Southern White Vernacular English preference for Deep South dialect",
"gg": "urban West Coast AAVE,like  late 80s/early 90s Compton",
"jv": "1930s-1940s jive talk",
"av": "AAVE",
"tv": "1980s Greek direct-to-video comedy dialect, like Stathis Psaltis films (Lisa kai o Adam era) Exaggerated, hilarious, blue-collar Athenian. Monotonic Greek",
"co": "Corporate US English: passive voice, buzzwords, motivational jargon, and hedged phrasing. Professional, optimistic, Dilbert-style office memo vibe—vague yet 'actionable. Passive-aggressive and Silicon Valley agile"
}
```

I follow standard `.srt` naming conventions so `foo.en.srt` translated to Pontic Greek becomes `foo.xai.pt.srt`

## Security? I downloaded an .srt and is now attacking the provider?!?
Your responsibility

## Hints and Tips
Different runs provide different results. Feel free to do multiple runs per language and cherry pick.

## License
GPLv3
