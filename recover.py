#!/usr/bin/env python
import pprint
import pickle

fname = 'translations.pcl'
srt = 'Destroy All Monsters - 1968.xai.clen.srt'
traws = ""
with open(fname,"rb") as ifile:
    traws = pickle.load(ifile)
    print(type(traws))
    print(type(traws[0]))
    print(traws[0])

print(len(traws))
with open(srt,"w") as ofile:
    for raw in traws:
        ofile.write(f"{raw['idx']}\n")
        ofile.write(f"{raw['ts']}\n")
        ofile.write(f"{raw['msg']}\n\n")

