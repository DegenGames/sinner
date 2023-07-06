#!/usr/bin/env python3
import signal
import sys

from sinner.Benchmark import Benchmark
from sinner.core import Core
from sinner.parameters import Parameters
from sinner.utilities import limit_resources

if __name__ == '__main__':
    if sys.version_info < (3, 10):
        raise Exception('Python version is not supported - please upgrade to 3.10 or higher.')
    signal.signal(signal.SIGINT, lambda signal_number, frame: quit())

    params = Parameters()
    if params.benchmark is not None:
        Benchmark(params.benchmark, params.execution_providers, params.source_path, params.target_path)
    else:
        limit_resources(params.max_memory)
        core = Core(params=params)
        core.run()
