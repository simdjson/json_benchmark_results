set -ex
rsync -avh --exclude skylake-x* --exclude ampere* skylake.licef.ca:simdjson_benchmark_results/v* .
rsync -avh --exclude skylake-g* --exclude skylake-c* --exclude ampere* skylake-x.licef.ca:simdjson_benchmark_results/v* .
# rsync -avh --exclude skylake* ampere.licef.ca:simdjson_benchmark_results/v* .
