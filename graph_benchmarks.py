import google_benchmark_json
import google_benchmark_graph

import argparse
import os
import re
import pandas as pd

# For directory arguments
def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)

def parse_args():
    parser = argparse.ArgumentParser(description='Generate graphs for benchmark results.')

    parser.add_argument(
        '--benchmarks', '--benchmark',
        type=str, choices=google_benchmark_graph.BENCHMARKS.keys(), nargs='+', default=['find_tweet', 'kostya'],
        help='Only show results for the given benchmarks'
    )
    parser.add_argument(
        '--implementations', '--implementation',
        type=str, choices=google_benchmark_graph.JSON_IMPLEMENTATIONS.keys(), nargs='+', default=['simdjson_ondemand', 'simdjson_dom', 'yyjson_insitu', 'sajson', 'rapidjson_insitu', 'nlohmann_json'],
        help='Only show results for the given JSON implementations.'
    )
    parser.add_argument(
        '--versions', '--version',
        type=str, nargs='+', default=['.*'],
        help='Only generate results for the given versions.'
    )
    parser.add_argument(
        '--compilers', '--compiler',
        type=str, choices=google_benchmark_graph.COMPILERS.keys(), nargs='+', default=['.*'],
        help='Only show results for the given compilers'
    )
    parser.add_argument(
        '--variants', '--variant',
        type=str, choices=google_benchmark_graph.VARIANTS.keys(), nargs='+', default=['.*'],
        help='Only generate results for the given variants.'
    )
    parser.add_argument(
        '--root',
        type=str, default=os.path.dirname(os.path.realpath(__file__)),
        help='Root directory containing all json (containing v0.7.0, v0.8.0, etc.)'
    )
    parser.add_argument(
        '--force',
        default=False, action='store_true',        
        help='Force all matching graphs to be regenerated, even if they already exist.'
    )
    return parser.parse_args()

def match_any(regexes, value):
    if value == None:
        value = ''
    return any([re.fullmatch(regex, value) for regex in regexes])

args = parse_args()
args.variants = ['' if variant == 'release' else variant for variant in args.variants]

print("Listing benchmarks ...")
runs = google_benchmark_json.list_runs(args.root)
total_benchmarks = len(runs)
runs = [
    run for run in runs
    if args.force or not os.path.exists(f"{os.path.splitext(run.path)[0]}.png") or os.path.getmtime(f"{os.path.splitext(run.path)[0]}.json") > os.path.getmtime(f"{os.path.splitext(run.path)[0]}.png")
]
print(f"Repository contains {len(runs)} benchmarks that need graphs out of a total of {total_benchmarks}.")
if len(runs) == 0:
    print(f"All benchmarks already generated!")
    exit(0)
print(f"Loading and filtering benchmarks ...")
runs = [
    run.dataframe() for run in runs
    if match_any(args.compilers, run.compiler_plus_version)
    if match_any(args.variants, run.variant)
    if match_any(args.versions, run.version_path)
]
if len(runs) == 0:
    print("All matching benchmarks already have graphs!")
    exit(0)
benchmarks = pd.concat(runs)
benchmarks = benchmarks[benchmarks['benchmark_name'].apply(lambda benchmark_name: match_any(args.benchmarks, benchmark_name))]
benchmarks = benchmarks[benchmarks['json_implementation'].apply(lambda json_implementation: match_any(args.implementations, json_implementation))]
print(f"Generating graphs for {benchmarks.count()} matching benchmarks ...")
for path,fig in google_benchmark_graph.graph_grouped_benchmarks(benchmarks, "best_instructions", "Instructions", 1):
    png_path = os.path.splitext(path)[0]+'.png'
    print(png_path)
    fig.write_image(png_path)
