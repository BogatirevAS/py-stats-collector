# Statistics Collector

Statistics collector for displaying it in the console as a table

-----

## Table of Contents

- [Installation](#installation)
- [Notes](#notes)
- [Examples](#examples)

## Installation

- console
```console
pip install git+https://github.com/BogatirevAS/py-stats-collector.git@master
```
```console
pip install git+https://github.com/BogatirevAS/py-stats-collector.git@0.8.0
```

- requirements.txt
```requirements
stats-collector @ git+https://github.com/BogatirevAS/py-stats-collector.git@master
```
```requirements
stats-collector @ git+https://github.com/BogatirevAS/py-stats-collector.git@0.8.0
```

## Notes

- When used in Windows, it is recommended to use with ResetTableMode.TERMINAL_CHANGE, because when changing 
the size of the terminal, hyphenating large lines divides them into several small ones,
preventing the terminal from being properly cleaned, in Linux in this case the line is still considered one;
- There should be no other messages during the output of the table, important messages can be added to the sub-table
using the special "info" key as in Example 3. If this method of use is not suitable, try Example 5.

## Examples
1.
```python
from stats_collector import StatsCollector
import time


stats = StatsCollector(["h1", "h2", "h3", "h4", "h5"])
data = [
    {"h1": 1, "h2": 1, "h3": 1, "h4": 1, "h5": 1},
    {"h1": 2, "h2": 20, "h3": 200, "h4": 2000, "h5": 20000},
    {"h1": 3, "h2": 300, "h3": 3000, "h4": 30000, "h5": 300000}
]
for stat in data:
    stats.add(stat)
    time.sleep(1)
# first stat
# --------------
# | STATISTICS |
# --------------------------
# | h1 | h2 | h3 | h4 | h5 |
# --------------------------
# | 1  | 1  | 1  | 1  | 1  |
# --------------------------
#               ||
#               \/
# --------------
# | STATISTICS |
# ------------------------------------
# | h1 | h2  | h3   | h4    | h5     |
# ------------------------------------
# | 3  | 300 | 3000 | 30000 | 300000 |
# ------------------------------------
stats.get_table(should_show_table=True)
# --------------
# | STATISTICS |
# ------------------------------------
# | h1 | h2  | h3   | h4    | h5     |
# ------------------------------------
# | 1  | 1   | 1    | 1     | 1      |
# ------------------------------------
# | 2  | 20  | 200  | 2000  | 20000  |
# ------------------------------------
# | 3  | 300 | 3000 | 30000 | 300000 |
# ------------------------------------
```
2.
```python
from stats_collector import StatsCollector


# You can immediately set more detailed headers
stats = StatsCollector({"h1": "Header1", "h2": "Header2", "h3": "Header3", "h4": "Header4", "h5": "Header5"})
# or rename them later
stats.rename_headers({"h2": "Header22"})
# The table is automatically enlarged to fit the data,
# but it is often more convenient to display the table at once in the maximum size
temp_stat = {"h1": 100, "h2": 1000, "h3": 10000, "h4": 100000, "h5": 1000000000000}
stats.resize_table_by_stat(temp_stat)
stats.add({"h1": 1, "h2": 1, "h3": 1, "h4": 1, "h5": 1})
# --------------
# | STATISTICS |
# ----------------------------------------------------------
# | Header1 | Header22 | Header3 | Header4 | Header5       |
# ----------------------------------------------------------
# | 1       | 1        | 1       | 1       | 1             |
# ----------------------------------------------------------
```
3.
```python
from stats_collector import StatsCollector
import time


# consistent updates
stats = StatsCollector(["h1", "h2", "h3"])
count1 = 0
count2 = 0
count3 = 0
for i in range(3):
    count1 += 1
    # first of all, you need to add a dictionary with all the meanings
    stats.add({"h1": count1, "h2": count2, "h3": count3})
    time.sleep(1)
    count2 += 10
    # then it's enough to update only the necessary keys
    stats.update({"h2": count2})
    time.sleep(1)
    # additional information that will be displayed under the table can be added using a special "info" key
    stats.update({"info": "test info 1"})
    time.sleep(1)
    count3 += 100
    stats.update({"h3": count3})
    time.sleep(1)
    stats.update({"info": "test info 2"})
    time.sleep(1)
```
4.
```python
from stats_collector import StatsCollector
import time


# Added the ability to make references to the properties of various objects so that the code
# does not become too cumbersome due to the constant transfer of dictionaries in functions
stats = StatsCollector(["h1", "h2", "h3"])
count1 = 0
class Counts:
    count2 = 0
counts = {"count3": 0}
stats.create_reference("h1", globals(), "count1")
stats.create_reference("h2", Counts, "count2")
stats.create_reference("h3", counts, "count3")
# Now, after each add or update, data will be collected from the specified references
for i in range(3):
    count1 += 1
    stats.add()
    time.sleep(1)
    Counts.count2 += 10
    counts["count3"] += 100
    stats.update()
    time.sleep(1)
counts2 = [1000]
# to overwrite an existing reference
stats.create_reference("h1", counts2, 0, force=True)
stats.update()
stats.get_table(should_show_table=True)
```
5.
```python
# To use it correctly with different logging tools, you need to disable the standard table print,
# get the latest stats in the form of a table and add it to your logger
from stats_collector import StatsCollector
import time
import logging


logging_config = {
    "level": logging.INFO,
    "format": "%(asctime)s [%(name)s] %(levelname)s - %(message)s",
}
logging.basicConfig(**logging_config)
stats = StatsCollector(["h1", "h2"], can_print_title=False, can_print_stats=False)
count1 = 0
count2 = 0
stats.create_reference("h1", globals(), "count1")
stats.create_reference("h2", globals(), "count2")
for i in range(3):
    count1 += 1
    stats.add()
    count2 += 10
    stats.update()
    time.sleep(1)
    logging.info(f"{stats.title}\n{stats.get_table(is_last_stat=True)}")
```