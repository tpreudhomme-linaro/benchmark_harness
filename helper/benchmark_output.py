#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    Benchmark Output Structure
    This class serves as a data structure to contain the parsed (or not)
    results of the benchmark, the dictionary of parsed perf results of running
    the benchmark, and the metadata associated to this run of the benchmark

"""


class BenchmarkOutput(object):
    def __init__(self):
        self.stdout_list = []
        self.perf_results = []
        self.metadata_list = []

    def add(self, stdout, perf_result, metadata):
        self.stdout_list += [stdout]
        self.perf_results += [perf_result]
        self.metadata_list += [metadata]

    def get(self, index):
        return self.stdout_list[index], self.perf_results[index], self.metadata_list[index]

    def len(self):
        return len(self.metadata_list)
