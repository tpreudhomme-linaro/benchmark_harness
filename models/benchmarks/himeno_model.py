#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    This class is an implementation of the BenchmarkModel interface
    (a python way of doing it, without decorations)

    It implements the actions necessary to prepare for the build, build,
    prepare for the run and run Dr. Ryutaro Himeno's benchmark.

"""

from models.benchmarks.benchmark_model import BenchmarkModel
from executor.execute import *
import os


class HimenoParser(OutputParser):
    """All data generated by himeno as well as external dictionary"""

    def __init__(self):
        super().__init__()
        self.fields = {
            'mimax': r'\bmimax\b\s+=\s+(\d+)',
            'mjmax': r'\bmjmax\b\s+=\s+(\d+)',
            'mkmax': r'\bmkmax\b\s+=\s+(\d+)',
            'imax': r'\bimax\b\s+=\s+(\d+)',
            'jmax': r'\bjmax\b\s+=\s+(\d+)',
            'kmax': r'\bkmax\b\s+=(\d+)',
            'cpu': r'cpu\s+:\s+(\d+[^\s]*)',
            'gosa': r'Gosa\s+:\s+(\d+[^\s]*)',
            'MFLOPS': r'MFLOPS measured\s+:\s+(\d+.\d+)',
            'score': r'Score based on MMX Pentium 200MHz\s+:\s+(\d+.\d+)'
        }


class ModelImplementation(BenchmarkModel):
    """This class is an implementation of the BenchmarkModel for LULESH"""

    def __init__(self):
        super().__init__()
        self.name = 'himeno'
        self.base_runflags = ''
        self.base_compileflags = ''
        self.base_linkflags = '-O3'
        self.base_build_deps = ''
        self.base_run_deps = ''
        self.benchmark_url = 'http://accc.riken.jp/en/wp-content/uploads/sites/2/2015/07/himenobmt.c.zip'

    def prepare_build_benchmark(self, extra_deps):
        """Prepares Environment for building and running the benchmark
        This entitles : installing dependencies, fetching benchmark code
        Can use Ansible to do this platform independantly and idempotently"""
        self.build_root = os.path.join(self.benchmark_rootpath, self.name)
        prepare_cmds = []
        prepare_cmds.append(['mkdir', self.build_root])
        prepare_cmds.append(
            ['wget', '-P', self.build_root, self.benchmark_url])
        prepare_cmds.append(['unzip', os.path.join(self.build_root,
                                                   'himenobmt.c.zip'), '-d', self.build_root])
        prepare_cmds.append(['lhasa', '-xw=' + self.build_root,
                             os.path.join(self.build_root, 'himenobmt.c.lzh')])
        return prepare_cmds

    def prepare_run_benchmark(self, extra_deps, compilers_dict):
        """Prepares envrionment for running the benchmark
        This entitles : fetching the benchmark and preparing
        for running it"""
        prepare_cmds = [[]]
        os.environ['LD_LIBRARY_PATH'] += compilers_dict['lib']
        return prepare_cmds

    def build_benchmark(self, compilers_dict, complete_compile_flags,
                        complete_link_flags, binary_name, benchmark_build_vars):
        """Builds the benchmark using the base + extra flags"""
        if benchmark_build_vars == '':
            benchmark_build_vars = 'MODEL=SMALL'
        build_cmd = []
        make_cmd = []
        make_cmd.append('make')
        make_cmd.append('-C')
        make_cmd.append(self.build_root)
        make_cmd.append('CXX=' + compilers_dict['cxx'])
        make_cmd.append('CC=' + compilers_dict['cc'])
        make_cmd.append('FC=' + compilers_dict['fortran'])
        make_cmd.append('CFLAGS=' + complete_compile_flags)
        make_cmd.append('LDFLAGS=' + complete_link_flags)
        make_cmd.append(benchmark_build_vars)
        build_cmd.append(make_cmd)
        return build_cmd

    def run_benchmark(self, binary_name, extra_runflags):
        """Runs the benchmarks using the base + extra flags"""
        binary_name = 'bmt'
        binary_path = os.path.join(self.benchmark_rootpath, self.name, binary_name)
        run_cmds = []
        run_args = self.parse_run_args(extra_runflags)
        if (run_args.iterations).isdigit():
            for i in range(0, int(run_args.iterations)):
                run_cmd=[]
                run_cmd.append(binary_path)
                run_cmds.append(run_cmd)

        return run_cmds

    def get_plugin(self):
        """Returns the plugin to parse the results"""
        return HimenoParser()
