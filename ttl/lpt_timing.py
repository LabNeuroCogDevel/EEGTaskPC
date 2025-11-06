#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "mne", "numpy"
# ]
# ///
"""
Read in bdf file and calculate time between triggers.

BioSemi Status channel correction from /Volumes/Hera/Projects/Habit/task/results/LoeffEEGPhotoTiming
"""

import os, os.path
import re
import sys
import mne
import numpy as np
import ttlconfig

def add_stim_corrected(raw):
    raw.load_data(verbose=False)
    stim_raw = raw.pick(["Status"]).get_data(verbose=False)
    info = mne.create_info(["StatusCorrected"], raw.info["sfreq"], ["stim"], verbose=False)
    stim_vals = correct_ttl(stim_raw[0]).reshape(stim_raw.shape)
    stim = mne.io.RawArray(stim_vals, info, verbose=False)
    raw.add_channels([stim], force_update_info=True)

def read_events(bdf):
    "read events by making a new channel"
    ## read in eeg and get separate stim channel info
    eeg = mne.io.read_raw_bdf(bdf, verbose=False)
    # eeg.describe() # 247808 (484.0 s) == 512Hz

    # events = mne.find_events(eeg, shortest_event=2)
    add_stim_corrected(eeg)
    events = mne.find_events(eeg, stim_channel="StatusCorrected", shortest_event=2, verbose=False)
    return (events, eeg.info)

def correct_ttl(x):
    """mne expects 8bit channel. biosemi has 24 bit. go down to 16 and adjust
    >>> correct_ttl(np.array([16128],dtype='int64')) # first stim ch val
    np.array([0],dtype='int16')
    """
    return x.astype(np.int32) - 127**2 + 1
    v = x - 16128  #  np.log2(16128+256)==14
    v[v == 65536] = 0  # 65536==2**16
    return v

def load_config(path):
    """
    Load file containing python code to config task ttl
    """

    import importlib
    modname = "config"
    spec = importlib.util.spec_from_file_location(modname, path)
    config = importlib.util.module_from_spec(spec)
    sys.modules[modname] = config
    spec.loader.exec_module(config)

    if not hasattr(config, "ttl_convert") or not callable(config.ttl_convert):
        raise AttributeError(f"{path} does not define a callable `ttl_convert`")

    return config

def between(events, a, b, verb=False):
    """
    Count samples between two events/status channel values. 
    """
    start = 0
    diff = [] 
    for (i,o,v) in events:
        if v == a:
            if verb and start != 0:
                print(f"Warning: {a} @ {start} and again at {i} w/o {b} in between")
            start = i
        elif v == b:
            if start == 0:
                if verb:
                    print(f"Warning: pair end {b} @ {i} before a pair start {a}")
                continue
            diff.append(i - start)
            start = 0
    if verb and start != 0 and len(diff)>0:
        print(f"Warning: opening {a} @ {start} but never closing {b} pair")
    return np.array(diff)

def name_disbatch(fname):
    pat_set = {'habit':   {'patt': r'habit',           'conf': ttlconfig.Habit},
               'switch': {'patt': r'switch',          'conf': ttlconfig.Switch},
               'rest':   {'patt': r'rest',            'conf': ttlconfig.Rest},
               'cal':    {'patt': r'eyecal',          'conf': ttlconfig.EyeCal},
               'dr':     {'patt': r'dr|dollarreward', 'conf': ttlconfig.DollarReward},
               'anti':   {'patt': r'_anti',           'conf': ttlconfig.VGSAnti},
               'vgs':    {'patt': r'_vgs',           'conf': ttlconfig.VGSAnti},
               'ss':     {'patt': r'(steadystate|ss)([234])0', 'conf': ttlconfig.SteadyState},
               }
    for task, d in pat_set.items():
        if m := re.search(d['patt'], fname, flags=re.IGNORECASE):
            config = d['conf']
            # kludge. ss trigger chanes based on freq 20Hz=2, 30Hz=3, 40Hz=4
            if task == 'ss':
                config.betweens[0]['a'] = int(m.group(2))
            return config
        # NB different than --verbose. to see why a file didn't match
        if os.environ.get("DEBUG"):
            print(f"no match for pattern {d['patt']} against file {fname}")

    raise Exception(f"Error: {fname} doesn't match known task")


if  __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Process one or more input files with an optional TTL value."
    )

    parser.add_argument(
        "-v", "--verbose",
        action='store_true',
        default=False,
        help="verbose output (all triggers count, show warings)"
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Input file(s) to process. 'newest' to run on all new in Raw/EEG"
    )

    args = parser.parse_args()

    if len(args.files) == 1 and args.files[0] == "newest":
        import subprocess
        args.files = subprocess.run("""find \
                        /Volumes/Hera/Raw/EEG/ -maxdepth 2 -mindepth 2 -mtime -1  -type d -print0 |
                       xargs -0I{} find {} -iname '*bdf' -print0""",
                                    capture_output=True,shell=True).stdout.decode()[:-1].split('\0')

    # 12184_20251105_anti2.bdf        VGSAnti:trial   n=41    0.0020  1.500-1.498 (1.500s)    [ttl  10 to 254]
    print("file\tconf\tn\tmaxdiff\trange(mean)\tbtwn ttl")
    for bdf in args.files:
        try:
            config = name_disbatch(bdf)
        except Exception as e:
            print(e)
            continue

        if args.verbose:
            print(f"# {bdf}")
        events, info = read_events(bdf)
        #print(info)
        if args.verbose:
            print(np.array(np.unique(events[:,2], return_counts=True)))
        events[:,2] = np.array([config.ttl_convert(x) for x in events[:,2]])

        for this_between in config.betweens:
            a = this_between['a']
            b = this_between['b']
            lab = this_between['label']
            if b is None:
                time_between_pulse = np.diff(events[events[:,2] == a, 0])
                b=a # for display later
            else:
                time_between_pulse = between(events, a, b, args.verbose)

            time_between_pulse = time_between_pulse / info['sfreq']
            if args.verbose:
                print(f"between adjusted {a} and {b}: {','.join(['%.4f'%x for x in time_between_pulse])}")
            n = len(time_between_pulse)
            if n == 0:
                print(f"ERROR: No value for {a} {b if b else ''} in {bdf}")
                continue
            goodtimes = config.discard(time_between_pulse, config.maxdiff)
            mean = np.mean(goodtimes)
            mn = np.min(goodtimes)
            mx = np.max(goodtimes)
            bname = os.path.basename(bdf)

            print(f"{bname}\t{config.__name__}:{lab:<4}\tn={n+1}\t{mx-mn:.04f}\t{mx:.03f}-{mn:.03f} ({mean:.03f}s)\t{a:>3} to {b:>3}")
        #print(time_between_pulse)

