SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

function bench_results() {
    host=$1
    compiler=$2
    base_version=$3
    commit=$4

    case $compiler in
        clang10)
            export CXX=clang++-10 CC=clang-10
            ;;
        clang11)
            export CXX=clang++-11 CC=clang-11
            ;;
        gcc10.2)
            export CXX=g++-10 CC=gcc-10
            ;;
        *)
            echo "Unknown compiler $compiler"
            exit 1
            ;;
    esac

    # Update the remote and figure out # of commits past version
    cd $SCRIPT_DIR/simdjson
    git remote update

    # Set up the home for the JSON file
    commits_past_version=$(git rev-list --count --first-parent v$base_version.0...$commit)
    base_dir=$SCRIPT_DIR/$base_version
    if [ "$commits_past_version" -ne "0" ]; then
        base_dir=$base_dir/$commits_past_version
    fi
    mkdir -p $base_dir
    json_file=$base_dir/$host-$compiler.json

    # Build
    git reset --hard $COMMIT
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
compilers=$2
base_version=$3
commits=$4

for compiler in $compilers; do
    rm -rf $SCRIPT_DIR/simdjson/build
    for commit in $commits; do
        bench_results $host $compiler $base_version $commit
    done
done 
