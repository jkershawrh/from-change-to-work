#!/bin/bash
set -euo pipefail
mkdir -p /work/home /work/toolchain /work/build-log
cd /work/input
for archive in rust/*.tar.xz; do
  tar -xf "$archive" -C /work
  component=$(basename "$archive" .tar.xz)
  /bin/bash "/work/$component/install.sh" --prefix=/work/toolchain --disable-ldconfig >> /work/build-log/toolchain.log 2>&1
done
export PATH=/work/toolchain/bin:/usr/bin:/bin
export CARGO_HOME=/work/cargo-home
export CARGO_NET_OFFLINE=true
export CARGO_BUILD_JOBS=3
export CARGO_INCREMENTAL=0
export RUSTFLAGS='-C target-cpu=x86-64'
export OMP_NUM_THREADS=1
cd /work/input/repo
/work/toolchain/bin/rustc -Vv > /work/build-log/rustc.txt
/work/toolchain/bin/cargo build --release --locked --offline --manifest-path crates/aeris-skill-transfer/Cargo.toml > /work/build-log/cargo-build.log 2>&1
/work/toolchain/bin/cargo test --locked --offline --manifest-path crates/aeris-skill-transfer/Cargo.toml > /work/build-log/cargo-test.log 2>&1
sha256sum crates/aeris-skill-transfer/target/release/aeris-skill-transfer > /work/build-log/binary.sha256
printf 'BUILD_COMPLETE\n'
