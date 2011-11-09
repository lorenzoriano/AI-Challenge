#!/usr/bin/env python
 
from distutils.core import setup
from distutils.extension import Extension
import numpy as np

setup(name="libastart",
    ext_modules=[
        Extension("libastar", ["astar.cpp", "micropather.cpp"],
        libraries = ["boost_python"],
        include_dirs = [np.get_include()+"/numpy"],
        )
    ])


