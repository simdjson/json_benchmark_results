set -x

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

function bench_results() {
    host=$1
    compiler=$2
    base_version=$3
    commit=$4
    variant=$5

    case $compiler in
        clang6)
            export CXX=clang++-6.0 CC=clang-6.0
            ;;
        clang9)
            export CXX=clang++-7 CC=clang-7
            ;;
        clang9)
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

    case $variant in
        default)
            suffix=""
            ;;
        native)
            suffix="-native"
            ;;
        *)
            echo "Unknown variant $variant"
            exit 1
            ;;
    esac

    # Update the remote and figure out # of commits past version
    cd $SCRIPT_DIR/simdjson
    git remote update

    # Set up the home for the JSON file
    commits_past_version=$(git rev-list --count --first-parent $base_version...$commit)
    base_dir=$SCRIPT_DIR/$base_version
    if [ "$commits_past_version" -ne "0" ]; then
        base_dir=$base_dir/$commits_past_version
    fi
    mkdir -p $base_dir
    json_file=$base_dir/$host-$compiler$suffix.json

    # Build
    git reset --hard $commit
    mkdir -p build
    cd build
    cmake -DCMAKE_CXX_FLAGS=-march=native ..
    make bench_ondemand

    # Run the benchmark
    benchmark/bench_ondemand --benchmark_counters_tabular=true --benchmark_out=$json_file --benchmark_out_format=json

    echo
    echo $json_file
    echo
}

host=$1
base_version=$2
commits=${3:-"$base_version"}
compilers=${4:-"clang11 gcc10.2"}
variants=${5:-default}

for compiler in $compilers; do
    for variant in $variants; do
        rm -rf $SCRIPT_DIR/simdjson/build
        for commit in $commits; do
            bench_results $host $compiler $base_version $commit $variant
        done
    done
done 
