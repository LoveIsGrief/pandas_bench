"""
pandas_benchmark
Copyright (C) 2021 LoveIsGrief

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import argparse
import csv
import json
import subprocess
import timeit
from io import TextIOBase

import numpy as np
import pandas as pd
from pandas import DataFrame
from talib import abstract as ta

START = 10
STOP = 115


def with_loc(dataframe: pd.DataFrame) -> pd.DataFrame:
    for period in range(START, STOP):
        dataframe.loc[:, f"sma_{period}"] = ta.SMA(dataframe, timeperiod=period)
    return dataframe.copy()


def no_workaround(dataframe: pd.DataFrame) -> pd.DataFrame:
    for period in range(START, STOP):
        dataframe[f"sma_{period}"] = ta.SMA(dataframe, timeperiod=period)
    return dataframe.copy()


def with_workaround(dataframe: pd.DataFrame) -> pd.DataFrame:
    frames = [dataframe]
    for period in range(START, STOP):
        frames.append(DataFrame({
            f"sma_{period}": ta.SMA(dataframe, timeperiod=period)
        }))
    return pd.concat(frames, axis=1)


def with_list_comp(dataframe: pd.DataFrame) -> pd.DataFrame:
    frame = pd.concat([
        DataFrame({f"sma_{period}": ta.SMA(dataframe, timeperiod=period)})
        for period in range(START, STOP)]
    )
    result = pd.concat([dataframe, frame.copy()], axis=1)
    print(".", end="", flush=True)
    return result


def get_cpu_info():
    # Pass empty env to use default language (English) in output
    stdout = subprocess.run(["lscpu", "--json"], stdout=subprocess.PIPE, env={}).stdout
    info = {d["field"].replace(":", ""): d["data"] for d in json.loads(stdout)["lscpu"]}
    return info


BENCHMARKS = {bench.__name__: bench for bench in [
    no_workaround,
    with_list_comp,
    with_loc,
    with_workaround,
]}

CSV_HEADERS = [
    "benchmark",
    "frame size",
    "repetitions",
    "time",
    "CPU model",
    "CPU arch",
    "CPU count",
]


def main(csv_file: TextIOBase, bench_names: list, framesize: int, repetitions: int):
    if csv_file:
        # Check if we're writing to a new CSV file
        csv_file.seek(0)
        new_csv = len(csv_file.read()) == 0
    else:
        new_csv = False

    cpu_info = get_cpu_info()
    print("Model name: {Model name}\n"
          "Architecture: {Architecture}\n"
          "CPU(s): {CPU(s)}\n".format(**cpu_info), flush=True)

    # Generate our random samples
    dataframe = DataFrame(dict(close=np.random.randn(framesize)))
    print(f"len dataframe {len(dataframe)}")

    # Run the selected benchmarks
    for bench_name in bench_names:
        bench_func = BENCHMARKS[bench_name]
        print(f"\n{bench_name}", flush=True)
        time = timeit.timeit(lambda: bench_func(dataframe.copy()), number=repetitions)
        print(f"Seconds to run {repetitions} times: {time} (per run {time / repetitions})",
              flush=True)

        if not csv_file:
            continue
        csv_writer = csv.writer(csv_file)
        if new_csv:
            csv_writer.writerow(CSV_HEADERS)
            new_csv = False
        csv_writer.writerow([
            # benchmark
            bench_name,
            # frame size
            framesize,
            # repetitions
            repetitions,
            # time
            time,
            # CPU model
            cpu_info["Model name"],
            # CPU arch
            cpu_info["Architecture"],
            # CPU count
            cpu_info["CPU(s)"],
        ])


if __name__ == '__main__':
    benchmark_names = sorted(BENCHMARKS.keys())

    parser = argparse.ArgumentParser(
        description="Benchmark workarounds to pandas' PerformanceWarning"
    )
    parser.add_argument("-r", "--repetitions", type=int, default=100,
                        help="How many times to run each benchmark on the dataset")
    parser.add_argument("-f", "--frame-size", type=int, default=300_000,
                        help="How many rows to add to the dataset")
    parser.add_argument("-b", "--benchmark", action="append", choices=benchmark_names,
                        help="Select which benchmark to run. Can be added multiple times")
    parser.add_argument("-c", "--csv", type=argparse.FileType(mode="a+"),
                        help="Where to store the results")

    args = parser.parse_args()
    benchmarks = args.benchmark or benchmark_names
    main(args.csv, sorted(list(set(benchmarks))), args.frame_size, args.repetitions)
