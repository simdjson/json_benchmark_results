import google_benchmark_json
import google_benchmark_graph
import os
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

#
# Benchmarks: comment out ones we don't want to show
#
compilers = [
    "clang10",
    "gcc10.2",
]


#
# Implementations: comment out ones we don't want to show
#
json_implementations = [
    "simdjson_ondemand",
    "simdjson_dom",
    "yyjson_insitu",
#     "yyjson",
    "sajson",
    "rapidjson_insitu",
#     "rapidjson",
    "nlohmann_json",
#     "rapidjson_lossless",
#     "simdjson_ondemand_unordered",
#     "simdjson_ondemand_forward_only",
]


#
# Comment out benchmarks we don't want shown
#
benchmark_names = [
    # "partial_tweets",
    "find_tweet",
    # "large_random",
    # "top_tweet",
    "kostya",
    # "distinct_user_id",
]

benchmarks = pd.concat([
    run.dataframe()
    for run in google_benchmark_json.list_runs(SCRIPT_DIR)
    if run.compiler_plus_version in compilers
])
benchmarks = benchmarks[benchmarks["benchmark_name"].isin(benchmark_names)]
benchmarks = benchmarks[benchmarks["json_implementation"].isin(json_implementations)]
for path,fig in google_benchmark_graph.graph_grouped_benchmarks(benchmarks):
    png_path = os.path.splitext(path)[0]+'.png'
    print(png_path)
    fig.write_image(png_path)
