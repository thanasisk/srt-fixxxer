#!/usr/bin/env bash
languages=(il kr pt gg tv co)
for l in ${languages[@]}; do
    ./srt_fixxxer.py -i small_test.srt -e xai -l "$l" -v
done
