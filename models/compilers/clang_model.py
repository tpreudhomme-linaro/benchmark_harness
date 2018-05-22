#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from models.compilers.compiler_model import CompilerModel

class ModelImplementation(CompilerModel):
    def __init__(self):
        super().__init__()
        self.version=''
        self.cc_name='clang'
        self.cxx_name='clang++'
        self.fortran_name='flang'
        self.default_compiler_flags='-O3 -ffast-math -ffp-contract=on'
        self.default_link_flags='-L'+os.path.join(self.sysroot_path, 'lib')
        self.default_dependencies=[]
