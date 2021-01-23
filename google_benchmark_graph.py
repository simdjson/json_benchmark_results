import plotly.express as px
import pandas as pd

#
# Benchmarks: comment out ones we don't want to show
#
COMPILERS = {
    "clang6": "Clang 6",
    "clang7": "Clang 7",
    "clang8": "Clang 8",
    "clang9": "Clang 9",
    "clang10": "Clang 10",
    "clang11": "Clang 11",
    "gcc7": "g++ 7",
    "gcc8": "g++ 8",
    "gcc9": "g++ 9",
    "gcc10.2": "g++ 10.2",
}

#
# Implementations: comment out ones we don't want to show
#
JSON_IMPLEMENTATIONS = {
    "simdjson_ondemand": "simdjson (On Demand)",
    "simdjson_dom": "simdjson (DOM)",
    "yyjson_insitu": "yyjson (insitu)",
    "yyjson": "yyjson",
    "sajson": "sajson",
    "rapidjson_insitu": "RapidJson (insitu)",
    "rapidjson": "RapidJson",
    "nlohmann_json": "nlohman::json",
    "rapidjson_lossless": "RapidJson (lossless)",
    "simdjson_ondemand_unordered": "simdjson (On Demand unordered)",
    "simdjson_ondemand_forward_only": "simdjson (On Demand forward-only)",
}


#
# Comment out benchmarks we don't want shown
#
BENCHMARKS = {
    "partial_tweets": "Read All Tweets",
    "find_tweet": "Find Tweet",
    "large_random": "Read Points",
    "top_tweet": "Top Tweet",
    "kostya": "Read Points (Kostya)",
    "distinct_user_id": "Tweet User IDs",
}

#
# Highlight one implementation
#
HIGHLIGHT_COLOR = 'firebrick'
OFF_COLOR = 'steelblue'
JSON_IMPLEMENTATION_COLORS = dict([(value,OFF_COLOR) for value in JSON_IMPLEMENTATIONS.values()])
JSON_IMPLEMENTATION_COLORS['simdjson (On Demand)'] = HIGHLIGHT_COLOR

def graph_benchmarks(name, benchmarks, y, y_label, y_scale):
    actual_implementations = pd.unique(benchmarks["json_implementation"])
    actual_implementations = list([v for v in JSON_IMPLEMENTATIONS.values() if v in actual_implementations])
    actual_benchmarks = pd.unique(benchmarks["benchmark_name"])
    actual_benchmarks = list([v for v in BENCHMARKS.values() if v in actual_benchmarks])
    fig = px.bar(benchmarks,
                 barmode="group",
                 title=name,
                 x="json_implementation",
                 y=y,
                 labels={y: y_label},
                 facet_col="benchmark_name",
                 facet_col_wrap=2,
                 category_orders={
                    "json_implementation": actual_implementations,
                    "benchmark_name": actual_benchmarks,
                 }
                )

    # Set y axis to show "n GB/s"
    # axis_values = [ 0, 1, 2, 3, 4, 5, 6 ]
    fig.update_xaxes(dict(title = None))
    # fig.update_yaxes(dict(
    #         tickmode = 'array',
    #         tickvals = [ tick*y_scale for tick in axis_values ],
    #         ticktext = [ f"{round(tick)} GB/s" for tick in axis_values ]
    #     ))
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))
    fig.for_each_trace(lambda a:
        a.update(
            text=[round(throughput, 1) for throughput in a.y],
            marker_color=[JSON_IMPLEMENTATION_COLORS[impl] for impl in a.x],
        )
    )
    return fig

def create_name(row):
    result = f"{row['host']} {row['compiler_plus_version']}"
    result += (f" - {row['variant']}" if row['variant'] else "")
    result += f" ("
    result += f"simdjson {row['base_version']}"
    result += (f"+{row['commits_past_version']}" if row['commits_past_version'] > 0 else "")
    result += f")"
    return result

def graph_grouped_benchmarks(benchmarks, y="best_bytes_per_sec", y_label="Throughput (GB/s)", y_scale=1000000000):
    benchmarks[y] = benchmarks[y].apply(lambda y: y/y_scale)
    benchmarks["benchmark_name"] = benchmarks["benchmark_name"].apply(lambda name: BENCHMARKS[name])
    benchmarks["compiler_plus_version"] = benchmarks["compiler_plus_version"].apply(lambda compiler: COMPILERS[compiler])
    benchmarks["json_implementation"] = benchmarks["json_implementation"].apply(lambda implementation: JSON_IMPLEMENTATIONS[implementation])
    benchmarks["run"] = benchmarks.apply(create_name, axis = 'columns')
    return [
        (path,graph_benchmarks(name, group, y, y_label, y_scale))
        for (name,path),group
        in benchmarks.groupby(["run","path"])
    ]
