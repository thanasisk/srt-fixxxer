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

## Installation
`pip -r requirements.txt`

`python-dateutil` is a massive timesaver.

`xai-sdk` requires Python 3.10 or newer.
## License
MIT
