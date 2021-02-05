#!/usr/bin/bash
set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
SIMDJSON_DIR=$SCRIPT_DIR/simdjson
if [ ! -d $SIMDJSON_DIR ]; then
    cd $(dirname $SIMDJSON_DIR)
    git clone https://github.com/simdjson/simdjson
fi

function bench_results() {
    host=$1
    compiler=$2
    base_version=$3
    commit=$4
    variant=$5
    benchmarks=$6

    case $compiler in
        clang6)
            export CXX=clang++-6.0 CC=clang-6.0
            ;;
        clang7)
            export CXX=clang++-7 CC=clang-7
            ;;
        clang8)
            export CXX=clang++-8 CC=clang-8
            ;;
        clang9)
            export CXX=clang++-9 CC=clang-9
            ;;
        clang10)
            export CXX=clang++-10 CC=clang-10
            ;;
        clang11)
            export CXX=clang++-11 CC=clang-11
            ;;
        gcc7)
            export CXX=g++-7 CC=gcc-7
            ;;
        gcc8)
            export CXX=g++-8 CC=gcc-8
            ;;
        gcc9)
            export CXX=g++-9 CC=gcc-9
            ;;
        gcc10.2)
            export CXX=g++-10 CC=gcc-10
            ;;
        *)
            echo "Unknown compiler $compiler"
            exit 1
            ;;
    esac

    suffix="-$variant"
    cmake_flags="-DCMAKE_BUILD_TYPE=Release"            
    case $variant in
        production)
            suffix=""
            cmake_flags="$cmake_flags -DSIMDJSON_PRODUCTION=ON"
            ;;
        development)
            # This is a basic default release build with development aids
            ;;
        debug)
            cmake_flags="-DCMAKE_BUILD_TYPE=Debug"
            ;;
        native)
            cmake_flags="$cmake_flags -DCMAKE_CXX_FLAGS=-march=native -DSIMDJSON_PRODUCTION=ON"
            ;;
        fallback)
            cmake_flags="$cmake_flags -DSIMDJSON_IMPLEMENTATION=fallback -DSIMDJSON_PRODUCTION=ON"
            ;;
        westmere)
            cmake_flags="$cmake_flags -DSIMDJSON_EXCLUDE_IMPLEMENTATION=haswell -DSIMDJSON_PRODUCTION=ON"
            ;;
        *)
            echo "Unknown variant $variant"
            exit 1
            ;;
    esac

    #
    # Create base directory file will live in
    #
    base_dir=$SCRIPT_DIR/$base_version

    # Figure out # of commits past version
    cd $SCRIPT_DIR/simdjson
    fork_commit=$(git merge-base $base_version $commit)
    commits_past_version=$(git rev-list --count --first-parent $base_version...$fork_commit)
    if [ "$commits_past_version" -ne "0" ]; then
        base_dir="$base_dir/$commits_past_version"
    fi

    # Figure out if commit is unmerged
    actual_commit=$(git rev-list -n 1 $commit)
    if [ "$fork_commit" != "$actual_commit" ]; then
        base_dir="$base_dir/$actual_commit"
    fi

    mkdir -p $base_dir

    #
    # Run benchmark (unless it's already been run)
    #
    file_base=$base_dir/$host-$compiler$suffix
    json_file=$file_base.json

    if [ -f $json_file ] && [ "$FORCE" = "" ]; then
        echo $json_file already generated
    else
        echo run_benchmark $commit $json_file \"$cmake_flags\" \"$benchmarks\" \> $file_base.out 2\>\&1
        run_benchmark $commit $json_file "$cmake_flags" "$benchmarks" > $file_base.out 2>&1

        echo
        echo $json_file
        echo
    fi
}

function run_benchmark() {
    commit=$1
    json_file=$2
    cmake_flags=$3
    benchmarks=$4

    echo "run_benchmark: $commit $json_file \"$cmake_flags\" \"$benchmarks\""

    # Build
    echo git reset --hard $commit
    git reset --hard $commit
    mkdir -p build
    cd build
    cmake_flags="$cmake_flags -DCMAKE_RULE_MESSAGES:BOOL=OFF -DCMAKE_VERBOSE_MAKEFILE:BOOL=ON"
    echo cmake $cmake_flags ..
    cmake $cmake_flags ..
    echo make --no-print-directory bench_ondemand
    make --no-print-directory bench_ondemand

    # Run the benchmark
    echo benchmark/bench_ondemand --benchmark_counters_tabular=true --benchmark_out=$json_file --benchmark_out_format=json --benchmark_filter="$benchmarks"
    benchmark/bench_ondemand --benchmark_counters_tabular=true --benchmark_out=$json_file --benchmark_out_format=json --benchmark_filter="$benchmarks"
}

host=$1
base_version=$2
commits=${3:-"$base_version"}
compilers=${4:-clang11}
variants=${5:-production}
benchmarks=${6:-simdjson}

cd $SCRIPT_DIR/simdjson
git remote update

for compiler in $compilers; do
    for variant in $variants; do
        rm -rf $SCRIPT_DIR/simdjson/build
        for commit in $commits; do
            bench_results $host $compiler $base_version $commit $variant "$benchmarks"
        done
    done
done 
