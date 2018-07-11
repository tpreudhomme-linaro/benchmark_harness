#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 Linux Tools' Perf wrapper for Execute

 Usage:
  app = LinuxPerf(['myapp', '-flag', 'etc'], outp=Plugin)
  out, err = app.stat()

 Plugin: parses the output of a specific benchmark, returns a dictionary
         stderr is parsed by Perf's own local parser. If benchmark also
         prints to stderr, make sure they get combined in stdout before
         calling this wrapper, or use Execute directly, passing two output
         parsers.
"""

from executor.Execute import *
from pathlib import Path
import os
import shutil

class LinuxPerfParser(OutputParser):
    """All data generated by perf as well as external dictionary"""
    def __init__(self):
        super().__init__()
        self.fields = {
            'instructions' : r'([\d,]+)\s+instructions',
            'cycles' : r'([\d,]+)\s+cycles',
            'cpu-migrations' : r'([\d,]+)\s+cpu-migrations',
            'context-switches' : r'([\d,]+)\s+context-switches',
            'page-faults' : r'([\d,]+)\s+page-faults',
            'branches' : r'([\d,]+)\s+branches',
            'branch-misses' : r'([\d,]+)\s+branch-misses',
            'elapsed' : r'(\d+\.\d+)\s+seconds time elapsed'
        }

class LinuxPerf(Execute):
    """Overrides Executor to run commands using Linux perf"""

    def __init__(self, program=None, plugin=None, perf=None):
        if program and not isinstance(program, list):
            raise TypeError("Program needs to be a list of arguments")
        if not program:
            raise ValueError("Need program arguments to run perf")
        if plugin and not isinstance(plugin, OutputParser):
            raise TypeError("Output parser needs to derive from OutputParser")

        super(LinuxPerf, self).__init__(None, plugin, LinuxPerfParser())

        # Program to run, to be wrapped with perf stat
        self.program = program
        # list of events
        self.events = list()
        # additional stat arguments
        self.stat_args = list()
        # Validate perf and permissions
        self._validate(perf)

    def _validate(self, perf):
        # Verify that perf is actually installed
        self.perf = perf
        if self.perf is None:
            self.perf = shutil.which('perf')
        else:
            self.perf = os.path.abspath(perf)
        if not Path(self.perf).exists():
            raise RuntimeError("Perf '" + self.perf + "' not available")

        # Check that you have permissions to do anything
        CAP_SYS_ADMIN = Path('/proc/sys/kernel/perf_event_paranoid').read_text()
        if int(CAP_SYS_ADMIN) >= 3:
            raise RuntimeError("Can't run perf with CAP_SYS_ADMIN higher than 2")

    def setStat(self, repeat=1, events=None):
        """Set extra stat arguments"""

        if repeat and not isinstance(repeat, int):
            raise TypeError("Repeat number must be an integer")
        if events and not isinstance(events, list):
            raise TypeError("Events needs to be a list")
        # Repeat the run N times, reports stdev
        if repeat > 1:
            self.stat_args.extend(['-r', repeat])

        # Collects only a few events (empty = all)
        if events:
            self.stat_args.append('-e')
            ev_str = ''
            for event in self.events:
                ev_str += event
                ev_str += ','
            ev_str.pop()
            self.stat_args.append(ev_str)


    def run(self):
        """Runs perf stat on the process, saving the output"""

        # Perf itself
        call = [self.perf, 'stat']

        # Stat arguments, if any
        if self.stat_args:
            call.extend(self.stat_args)

        # Adding program to perf
        call.extend(self.program)

        # Replaces program with perf call
        self.program = call

        # Call and collect output
        return super().run()
