"""Compatibility CLI for the shared source-validated assembly-data pipeline."""
import argparse
from pathlib import Path
from native_data_layouts import contracts, recipe
from native_assembly_data import emit_reviewed


def convert(source):
    original='asm/vs_recorder_data.o'
    blocks=recipe(source.parent.parent,original)
    counts={key:0 for key in ('numeric','callbacks','configs','relocations')}
    for category in contracts()[original]['categories'].values(): counts[category]+=1
    counts['relocations']=sum(len(b['pointers']) for b in blocks)
    return emit_reviewed(blocks),len(blocks),counts


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    text,total,counts=convert(a.game/'asm/vs_recorder_data.s')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(text)
    print(total,counts)
