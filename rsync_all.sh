set -ex
rsync -avht --exclude skylake-x* --exclude ampere* skylake.licef.ca:simdjson_benchmark_results/v* .
rsync -avht --exclude skylake-g* --exclude skylake-c* --exclude ampere* skylake-x.licef.ca:simdjson_benchmark_results/v* .
rsync -avht --exclude skylake* ampere.licef.ca:simdjson_benchmark_results/v* .
