# Benchmarks

Benchmark results (and graphing thereof) for simdjson

## Structure

### Versions and Commits

Each top-level directory (`v0.7.0`, `v0.8.0`, ...) represents a version of simdjson. Benchmark results directly underneath represent benchmarks against that version.

Subdirectories (`v0.7.0/3`, etc.) represent a development commit--commit to master *after* that version. `v0.7.0/3` is the change 3 commits after v0.7.0 was released. Only merges are counted.

### Benchmark Files

Each benchmark contains two main files: `<host>-<compiler>[-<variant>].json`, and `<host>-<compiler>[-<variant>].out`. The JSON file is the actual Google Benchmark results (unmodified), and the .out file is the output of cmake, make, etc. so that we can be sure we're running what we think we're running.

## Running Benchmarks

To collect a set of results, we go to the top-level directory of this repository and run:

```bash
git clone https://github.com/simdjson/simdjson
./run_benchmark_official.sh <host> <simdjson version> [<git commit>] [<compilers>] [<variants>]
```

(The git clone only needs to be run the first time.)

The parameters:

* `<host>` is the name of the host for identification purposes--e.g. `skylake`, `skylake-x`, `ampere`. This is freeform and can contain any value.
* `<simdjson version>` is the version of simdjson the commit is based off of, e.g. `v0.7.0`. It should match the actual git tag of the simdjson version.
* `<git commits>` is the set of commits you want to test, separated by spaces. For example, `"v0.8.0~1 v0.8.0~2"` will test the two commits just before v0.8.0. The script will calculate how many commits they are from the simdjson version. If this is not specified or is empty, it defaults to the simdjson version (e.g. `<v0.8.0>`).
* `<compilers>` is the set of compilers you want to run, separated by spaces. Valid values are clang6, clang7, clang8, clang9, clang10, clang11 gcc7, gcc8, gcc9 and gcc10.2. If this is not specified or is empty, it defaults to `"clang11 gcc10.2"`.
* `<variants>` are variants of simdjson you want to test, separated by spaces. If this is not specified or is empty, it defaults to `"default"`. Valid values are:
  - `default`: compile without any extra flags (just -O3).
  - `native`: compile with `-march=native`.
  - `fallback`: compile with only the fallback kernel.

The output files will automatically be collected in the right places.

The v0.7.0 and v0.8.0 benchmarks on skylake were collected by running:

```
host=skylake
./run_benchmark_official.sh $host v0.8.0 "" "clang10 clang11 gcc10.2" "default native fallback"
./run_benchmark_official.sh $host v0.7.0 "" "clang10 clang11 gcc10.2" "default native fallback"
./run_benchmark_official.sh $host v0.7.0 "v0.8.0~1 v0.8.0~5 v0.8.0~10 v0.8.0~15 v0.8.0~20 v0.8.0~25 v0.8.0~30 v0.8.0~35" "" "default native"
```

## Generating .pngs

When all the new .out and .json files are in the directory, you can run graph_benchmarks.py to generate pngs. You will need several libraries first.

```bash
pip3 install pandas plotly kaleido
python graph_benchmarks.py
```

### Python Notebook

`simdjson_perf.ipynb` is a Jupyter notebook that lets you preview the graphs. Install jupyter (`pip3 install jupyter pandas plotly kaleido`) and open it in Jupyter or Visual Studio Code.
