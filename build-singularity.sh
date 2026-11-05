#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
export KBUILD_BUILD_USER=ProjectNoci KBUILD_BUILD_HOST=Singularity
export KBUILD_BUILD_VERSION=2
export KBUILD_BUILD_TIMESTAMP="${KBUILD_BUILD_TIMESTAMP:-Fri Oct 30 17:00:00 UTC 2026}"
if [ -n "${TOOLCHAIN_DIR:-}" ]; then export PATH="$TOOLCHAIN_DIR/bin:$PATH"; fi
out_dir="${OUT_DIR:-out}"
make_args=(O="$out_dir" ARCH=arm64 CC=clang HOSTCC=gcc CROSS_COMPILE=aarch64-linux-gnu-
 CLANG_TRIPLE=aarch64-linux-gnu- CROSS_COMPILE_ARM32=arm-linux-gnueabi- LLVM_IAS=1
 LD=ld.lld AR=llvm-ar NM=llvm-nm OBJCOPY=llvm-objcopy OBJDUMP=llvm-objdump
 READELF=llvm-readelf STRIP=llvm-strip)
make "${make_args[@]}" singularity_defconfig
python3 Singularity/check-config.py "$out_dir/.config"
make -j"${JOBS:-8}" "${make_args[@]}" Image.gz-dtb dtbo.img
stage_dir=$(mktemp -d)
trap 'rm -rf -- "$stage_dir"' EXIT
cp -a Singularity/AnyKernel3/. "$stage_dir/"
cp "$out_dir/arch/arm64/boot/Image" "$stage_dir/Image"
cp "$out_dir/arch/arm64/boot/dtbo.img" "$stage_dir/dtbo.img"
cat "$out_dir/arch/arm64/boot/dts/qcom/sm8150-v2.dtb" \
 "$out_dir/arch/arm64/boot/dts/qcom/sm8150.dtb" \
 "$out_dir/arch/arm64/boot/dts/qcom/sm8150p-v2.dtb" \
 "$out_dir/arch/arm64/boot/dts/qcom/sm8150p.dtb" > "$stage_dir/dtb"
(cd "$stage_dir"; sha256sum Image dtb dtbo.img > SHA256SUMS)
mkdir -p dist
python3 Singularity/package.py "$stage_dir" "$PWD/dist/Singularity_v1_ProjectNoci_vayu_OSS_SukiSU_FINAL.zip"
