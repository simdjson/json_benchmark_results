import os
import json
import re
import pprint
import itertools
import pandas as pd
from operator import attrgetter
from collections import OrderedDict

OLD_BENCHMARKS = {
    "PartialTweets": "partial_tweets",
    "LargeRandom": "large_random",
    "Kostya": "kostya",
    "FindTweet": "find_tweet",
}

OLD_IMPLEMENTATIONS = {
    "OnDemand": "simdjson_ondemand",
    "Dom": "simdjson_dom",
    "OnDemandUnordered": "simdjson_ondemand_unordered"
}

class GoogleBenchmarkRun:
    @classmethod
    def from_path(cls, root, folder, file):
        # Split up the path (relative to root) and extract the version
        path_parts = [x for x in os.path.split(os.path.relpath(folder, root))]
        if path_parts[0] == '.' or path_parts[0] == '': path_parts.pop(0)
        assert len(path_parts) <= 2

        #
        # Path can be either:
        # <base_version>/blah.json
        # <base_version>/<commits_past_version>/blah.json
        #
        # File is always:
        # <host>-<compiler><version>[-<variant>].json
        #
        match = re.fullmatch(r"(.+)-(clang|gcc)([^-]+)(-(.+))?.json", file)

        return GoogleBenchmarkRun(
            path = os.path.join(folder, file),
            base_version = path_parts[0],
            commits_past_version = int(path_parts[1]) if len(path_parts) == 2 else 0,
            host = match.group(1),
            compiler = match.group(2),
            compiler_version = match.group(3),
            variant = match.group(5)
        )
    
    def __init__(self, path, base_version, commits_past_version, host, compiler, compiler_version, variant):
        self.path = path
        self.base_version = base_version
        self.commits_past_version = commits_past_version
        self.host = host
        self.compiler = compiler
        self.compiler_version = compiler_version
        self.variant = variant
        self.deserialized_json = None

    @property
    def compiler_plus_version(self):
        return f"{self.compiler}{self.compiler_version}"

    @property
    def json(self):
        if not self.deserialized_json:
            print(self.path)
            with open(self.path) as f:
                self.deserialized_json = json.load(f)
        return self.deserialized_json
    
    @property
    def context(self):
        return {
            **self.json["context"],
            "path": self.path,
            "base_version": self.base_version,
            "commits_past_version": self.commits_past_version,
            "host": self.host,
            "compiler": self.compiler,
            "compiler_version": self.compiler_version,
            "compiler_plus_version": self.compiler_plus_version,
            "variant": self.variant,
        }

    @property
    def benchmarks(self):
        return [GoogleBenchmarkResult(self, benchmark) for benchmark in self.json["benchmarks"]]

    def __str__(self):
        result = f"simdjson v{self.base_version}{f'+{self.commits_past_version}' if self.commits_past_version > 0 else ''} compiled on {self.compiler} {self.compiler_plus_version}{f'- {self.variant}' if self.variant else ''}\n"
        # Order implementations by max throughput
        implementation_order = [benchmark.implementation for benchmark in sorted(self.benchmarks, key = attrgetter("throughput"), reverse = True)]
        implementation_order = list(OrderedDict.fromkeys(implementation_order))

        # Group benchmarks by name
        sorted_benchmarks = sorted(self.benchmarks, key = attrgetter("name"))
        for benchmark_name, benchmarks in itertools.groupby(sorted_benchmarks, key = attrgetter('name')):
            result += f"  {benchmark_name}:\n"
            # Sort benchmarks by implementation
            for benchmark in sorted(benchmarks, key = lambda b: implementation_order.index(b.implementation)):
                result += f"  - {benchmark.implementation}: {benchmark.benchmark_json['best_bytes_per_sec']}\n"
        return result

    def dataframe(self):
        return pd.DataFrame([benchmark.to_record() for benchmark in self.benchmarks])

class GoogleBenchmarkResult:
    def __init__(self, run, benchmark_json):
        self.run = run
        self.benchmark_json = benchmark_json

    @property
    def name(self):
        result = re.search(r'^(.+)<([^>]+)>', self.benchmark_json["name"])[1]
        return OLD_BENCHMARKS[result] if result in OLD_BENCHMARKS else result

    @property
    def implementation(self):
        result = re.search(r'^(.+)<([^>]+)>', self.benchmark_json["name"])[2]
        return OLD_IMPLEMENTATIONS[result] if result in OLD_IMPLEMENTATIONS else result
    
    @property
    def throughput(self):
        return self.benchmark_json["best_bytes_per_sec"]

    def to_record(self):
        return {
            **self.run.context,
            "benchmark_name": self.name,
            "json_implementation": self.implementation,
            **self.benchmark_json
        }

    def __str__(self):
        return f"{self.implementation()} - {self.throughput}"

def list_runs(path):
    return [
        GoogleBenchmarkRun.from_path(path, folder, file)
        for folder, subfolders, files in os.walk(path)
        for file in files
        if os.path.splitext(file)[1] == ".json"
    ]
