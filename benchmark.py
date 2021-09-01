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
import json
import os
import subprocess
import timeit

import numpy as np
import pandas as pd
from pandas import DataFrame
from talib import abstract as ta


def do_loc(dataframe: pd.DataFrame) -> pd.DataFrame:
    for period in range(10, 115):
        dataframe.loc[:, f"sma_{period}"] = ta.SMA(dataframe, timeperiod=period)
    return dataframe.copy()


def do_no_workaround(dataframe: pd.DataFrame) -> pd.DataFrame:
    for period in range(10, 115):
        dataframe[f"sma_{period}"] = ta.SMA(dataframe, timeperiod=period)
    return dataframe.copy()


def do_workaround(dataframe: pd.DataFrame) -> pd.DataFrame:
    frames = [dataframe]
    for period in range(10, 115):
        frames.append(DataFrame({
            f"sma_{period}": ta.SMA(dataframe, timeperiod=period)
        }))
    return pd.concat(frames, axis=1)


def do_other_workaround(dataframe: pd.DataFrame) -> pd.DataFrame:
    frame = None
    for period in range(10, 115):
        p_frame = DataFrame({f"sma_{period}": ta.SMA(dataframe, timeperiod=period)})
        if frame is not None:
            frame = pd.concat([frame, p_frame], axis=1)
        else:
            frame = p_frame
    return frame


def get_cpu_info():
    # Pass empty env to use default language (English) in output
    stdout = subprocess.run(["lscpu", "--json"], stdout=subprocess.PIPE, env={}).stdout
    info = {d["field"].replace(":", ""): d["data"] for d in json.loads(stdout)["lscpu"]}
    return info


def main():
    # cur_path = Path(__file__)
    # print(get_cpu_info())

    # dataframe = load_pair_history("AAVE/BTC", "5m", (cur_path.parent / "user_data/data/binance"))
    dataframe = DataFrame(dict(close=np.random.randn(300_000)))
    print(f"len dataframe {len(dataframe)}")
    count = 1000

    print("do_loc")
    time = timeit.timeit(lambda: do_loc(dataframe.copy()), number=count)
    print(f"len dataframe {len(dataframe)}")
    print(f"Seconds to run {count} times: {time} (per run {time / count})")

    print("\ndo_no_workaround")
    count = 1000
    time = timeit.timeit(lambda: do_no_workaround(dataframe.copy()), number=count)
    print(f"Seconds to run {count} times: {time} (per run {time / count})")

    print("\ndo_workaround")
    time = timeit.timeit(lambda: do_workaround(dataframe.copy()), number=count)
    print(f"Seconds to run {count} times: {time} (per run {time / count})")

    # print("\ndo_other_workaround")
    # time = timeit.timeit(lambda: do_other_workaround(dataframe.copy()), number=count)
    # print(f"Seconds to run {count} times: {time} (per run {time / count})")


if __name__ == '__main__':
    main()
