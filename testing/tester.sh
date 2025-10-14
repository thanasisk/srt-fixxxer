#!/usr/bin/env bash
set -eu
samples=(tiny_test.srt small_test.srt medium_test.srt)
languages=(il kr pt gg tv co)
tiny=tiny_test.srt  # 5 subtitles
small=small_test.srt # 58 subtitles
medium=medium_test.srt # 111 subtitles

cmd="../srt_fixxxer.py"

# pick a random language
rand=$[$RANDOM % ${#languages[@]}]
lang=${languages[$rand]}
# WORKS: serial mode
batch=1
parallel=1
echo $cmd -b $batch -p $parallel -i $tiny -e xai -l "$lang" -v
# WORKS parallel mode per single line
batch=1
parallel=6
echo $cmd -b $batch -p $parallel -i $tiny -e xai -l "$lang" -v
# single line / parallel mode
echo $cmd -i $tiny -e xai -p 12 -b 1 -l $lang -v
# 2 lines / parallel mode
echo $cmd -i $tiny -b 2 -p 2 -e xai -l "$lang" -v
# 2 lines / parallel mode consumes them all
echo $cmd -i $tiny -b 2 -p 10 -e xai -l "$lang" -v
# 5 lines / parallel mode - bigger file
$cmd -i $small -b 5 -p 10 -e xai -l "$lang" -v
echo indices out of order
./gaga.py
exit
languages=(il kr pt gg tv co)
for sample in ${samples[@]}; do
    for lang in ${languages[@]}; do
        ../srt_fixxxer.py -i "$sample" -e xai -l "$lang" -v
    done
done
