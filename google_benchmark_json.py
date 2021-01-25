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
        #
        # Path can be either:
        # <base_version>/blah.json
        # <base_version>/<commits_past_version>/blah.json
        #
        # File is always:
        # <host>-<compiler><version>[-<variant>].json
        #
        match = re.fullmatch(r"(.+)-(clang|gcc)([^-]+)(-(.+))?.json", file)
        if match == None:
            return None

        return GoogleBenchmarkRun(
            root = root,
            path = os.path.join(folder, file),
            host = match.group(1),
            compiler = match.group(2),
            compiler_version = match.group(3),
            variant = match.group(5)
        )
    
    def __init__(self, root, path, host, compiler, compiler_version, variant):
        self.root = root
        self.path = path
        self.host = host
        self.compiler = compiler
        self.compiler_version = compiler_version
        self.variant = variant
        self.deserialized_json = None
    
    @property
    def version_path(self):
        return os.path.dirname(os.path.relpath(self.path, self.root))

    @property
    def version_parts(self):
        version_parts = [x for x in os.path.split(self.version_path)]
        if version_parts[0] == '.' or version_parts[0] == '': version_parts.pop(0)
        if len(version_parts) == 1:
            version_parts = [ version_parts[0], '0' ]
        if len(version_parts) == 2:
            if len(version_parts[1]) == len('3a1c065104e5efd9afc30ca051984731929bdfcd'):
                version_parts = [ version_parts[0], '0', version_parts[1] ]
            else:
                version_parts = [ version_parts[0], version_parts[1], None ]
        
        assert len(version_parts) <= 3
        return version_parts

    @property
    def base_version(self):
        return self.version_parts[0]

    @property    
    def commits_past_version(self):
        return int(self.version_parts[1])

    @property 
    def dev_commit(self):
        return self.version_parts[2]

    @property
    def compiler_plus_version(self):
        return f"{self.compiler}{self.compiler_version}"

    @property
    def json(self):
        if not self.deserialized_json:
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
            "dev_commit": self.dev_commit,
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
    results = [
        GoogleBenchmarkRun.from_path(path, folder, file)
        for folder, subfolders, files in os.walk(path)
        for file in files
        if os.path.splitext(file)[1] == ".json"
    ]
    return [result for result in results if result != None]
