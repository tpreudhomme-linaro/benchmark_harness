#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    Benchmark Harness Controller
    This class is the main controller of the Benchmark Harness Application
    behaviour. It centralizes and distributes all calls to the different parts
    of the application. This is the entry point of the application as well.

    Usage: benchmark_controller.py --usage
"""

import os
import argparse
import subprocess
import re
import importlib
import yaml
import logging
import coloredlogs
from pathlib import Path
from helper.compiler_factory import CompilerFactory
from helper.model_loader import ModelLoader
from helper.benchmark_logger import BenchmarkLogger
from models.compilers.compiler_model import CompilerModel
from models.benchmarks.benchmark_model import BenchmarkModel
from models.machines.machine_model import MachineModel
from executor.execute import run
from executor.linux_perf import *


class BenchmarkController(object):
    """Point of entry of the benchmark harness application"""

    def __init__(self, argparse_parser, argparse_args):
        self.parser = argparse_parser
        self.args = argparse_args
        self.root_path = os.getcwd()
        self.logger = BenchmarkLogger(logging.getLogger(__name__), self.parser,
                                      self.args.verbose)


    def _make_unique_name(self):
        """Unique name for the binary and results files"""
        identity = str(
            self.args.name +
            '_' +
            (self.args.toolchain.rsplit('/', 1)[-1])[:24] +
            '_' +
            self.args.compiler_flags.replace(
                " ",
                "") +
            '_' +
            self.args.machine_type +
            '_' +
            self.args.benchmark_options.replace(
                " ",
                ""))
        self.binary_name = re.sub("[^a-zA-Z0-9_]+", "", identity).lower()
        self.report_name = identity

    def _build_complete_flags(self, mode='DEFAULT'):
        if self.compiler_model is not None and self.benchmark_model is not None \
                and self.machine_model is not None:
            complete_build_flags, complete_link_flags = self.compiler_model.main(
                mode)
            m_complete_build_flags, m_complete_link_flags = self.machine_model.main()
            b_complete_build_flags, b_complete_link_flags = self.benchmark_model.fetch_flags()

            complete_build_flags = complete_build_flags + ' ' + m_complete_build_flags + \
                ' ' + b_complete_build_flags + ' ' + self.args.compiler_flags

            complete_link_flags = complete_link_flags + ' ' + m_complete_link_flags + \
                ' ' + b_complete_link_flags + ' ' + self.args.link_flags

            complete_build_flags, complete_link_flags = self.compiler_model.validate_flags(
                complete_build_flags, complete_link_flags)

            self.complete_build_flags = complete_build_flags
            self.complete_link_flags = complete_link_flags

    def _output_logs(self, stdout, perf_results):
        if stdout and not isinstance(stdout, str) and not isinstance(stdout, dict):
            raise TypeError('stdout should be a string of bytes or a dictionary')
        if perf_results and not isinstance(perf_results, dict):
            raise TypeError('perf_results should be a dictionary')
        if not os.path.isdir(self.results_path):
            raise TypeError('%s should be a directory' % self.results_path)

        if isinstance(stdout, dict):
            with open(self.results_path + '/' + self.report_name + '_stdout_parser_results.report', 'w') as stdout_d:
                yaml.dump(stdout, stdout_d, default_flow_style=False)
        else:
            with open(self.results_path + '/' + self.report_name + '_stdout.report', 'w') as stdout_d:
                stdout_d.write(stdout)

        if isinstance(perf_results, dict):
            with open(self.results_path + '/' + self.report_name + '_perf_parser_results.report', 'w') as perf_res_d:
                yaml.dump(perf_results, perf_res_d, default_flow_style=False)
        else:
            with open(self.results_path + '/' + self.report_name + '_perf_parser_results.report', 'w') as perf_res_d:
                perf_res_d.write(perf_results)

    def _make_dirs(self):
        """This function creates the directory at the supplied benchmark root
        where it will put the benchmark code and binaries, compiler binaries
        and results"""
        self._make_unique_name()

        self.unique_root_path = os.path.join(self.args.benchmark_root,
                                        self.binary_name)
        self.compiler_path = os.path.join(self.unique_root_path, 'compiler/')
        self.benchmark_path = os.path.join(self.unique_root_path, 'benchmark/')
        self.results_path = os.path.join(self.unique_root_path, 'results/')

        os.mkdir(self.unique_root_path)
        os.mkdir(self.compiler_path)
        os.mkdir(self.benchmark_path)
        os.mkdir(self.results_path)
        self.logger.info('Made dirs')

    def _load_models(self):
        """This function fetches the appropriate models depending on the
        supplied options """
        compiler_factory = CompilerFactory(self.args.toolchain,
                                           self.compiler_path)
        try:
            self.benchmark_model = ModelLoader(
                self.args.name + '_model.py', 'benchmark', self.root_path).load()
            self.benchmark_model.set_path(os.path.abspath(self.benchmark_path))
            self.logger.info('Fetched Benchmark')
            self.machine_model = ModelLoader(
                self.args.machine_type + '_model.py', 'machine', self.root_path).load()
            self.logger.info('Fetched Machine')
            self.compiler_model = compiler_factory.getCompiler()
            self.logger.info('Fetched Compiler')
        except ImportError as err:
            self.logger.error(err, True)

        self._build_complete_flags()


    def _post_run(self, stdout, perf_results):
        """This function executes after the benchmark has been run"""
        self.logger.debug(stdout)
        self.logger.debug(perf_results)
        self._output_logs(stdout, perf_results)
        self.logger.info('The truth is out there')

    def _run_all(self, list_of_commands, perf=False):
        """This function executes the command required for the benchmark
        prebuild, build, postbuild, prerun and run. When perf needs to be ran,
        and output needs to be returned, set  perf to True"""
        for cmd in list_of_commands:
            if cmd != []:
                self.logger.debug('Running command : ' + str(cmd))
                if perf:
                    perf_parser = LinuxPerf(cmd, self.benchmark_model.get_plugin())
                    # stderr <=> perf_results
                    stdout, stderr = perf_parser.stat()
                else:
                    stdout, stderr = run(cmd)

                self.logger.info(stdout)

                if stderr != '' and perf == False:
                    self.logger.error(stderr)

                self.logger.debug('Command ran')

        if perf:
            return stdout, stderr

    def main(self):
        """This is where all the logic plays, as you would expect from a
        main function"""

        self._make_dirs()

        self._load_models()

        #prepare_build
        self._run_all(self.benchmark_model.prepare_build_benchmark(self.args.benchmark_build_deps))

        #build
        self._run_all(self.benchmark_model.build_benchmark(self.compiler_model.getDictCompilers(),
                                                              self.complete_build_flags,
                                                              self.complete_link_flags,
                                                              self.binary_name,
                                                              self.args.benchmark_build_vars))
        #post_build

        #pre_run
        self._run_all(self.benchmark_model.prepare_run_benchmark(self.args.benchmark_run_deps,
                                                                 self.compiler_model.getDictCompilers()))

        #run
        stdout, perf_result = self._run_all(self.benchmark_model.run_benchmark(self.binary_name,
                                                                               self.args.benchmark_options), perf=True)

        self._post_run(stdout, perf_result)

        return 0


if __name__ == '__main__':
    """This is the point of entry of our application, not much logic here"""
    parser = argparse.ArgumentParser(description='Run some benchmark.')
    parser.add_argument('name', metavar='benchmark_name', type=str,
                        help='The name of the benchmark to be run')
    parser.add_argument('machine_type', type=str,
                        help='The type of the machine to run the benchmark on')
    parser.add_argument('toolchain', type=str,
                        help='The url or local of the toolchain with which to compile the benchmark')
    parser.add_argument('--compiler-flags', type=str, default='',
                        help='The extra compiler flags to use with compiler')
    parser.add_argument('--link-flags', type=str, default='',
                        help='The extra link flags to use with the benchmark building')
    parser.add_argument('--benchmark-build-vars', type=str, default='',
                        help='The extra values the benchmark build needs (e.g. MODEL for Himeno')
    parser.add_argument('--benchmark-options', type=str, default='',
                        help='The benchmark options to use with the benchmark')
    parser.add_argument('--benchmark-build-deps', type=str, default='',
                        help='The benchmark specific extra dependencies for the build')
    parser.add_argument('--benchmark-run-deps', type=str, default='',
                        help='The benchmark specific extra dependencies for the run')
    parser.add_argument('--benchmark-root', type=str,
                        help='The benchmark root directory where things will be \
                        extracted and created')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='The verbosity of logging output')
    args = parser.parse_args()

    controller = BenchmarkController(parser, args)
    controller.main()
