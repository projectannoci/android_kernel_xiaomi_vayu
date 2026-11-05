# Singularity v1 @ProjectNoci — vayu / bhima

Base: crDroid sm8150 `13.0`, commit `4e83886b5de9184008167d14d1b29b6f12feeca3`, Linux4.14.336. Clang/LLD18.1.3. Source changes and final effective config are included. The kernel release is `4.14.336-Singularity-v1-ProjectNoci`; the installer name is `Singularity v1 @ProjectNoci`.

## Performance changes

- CPU performance default; 120ms input boost at 1785600/2419200/2956800kHz for CPUs0-3/4-6/7. Existing cpu-boost code expires the request. Scheduler boost mode1 is active only for the input boost interval. WALT remains the source scheduler.
- GPU performance default. GPU OPP/voltage tables, DTB and DTBO remain the source-built pair used by the boot-confirmed R2 base; no NGK voltage table is included.
- New Singularity bus driver raises DDR/LLCC bandwidth for 64ms on touch/display commits and to the supported maximum for 1000ms on screen wake. Its floors are3879/4577 in the existing devbw driver's units. It uses the existing governor and maximum clamp, unregisters device pointers before removal, expires votes and clears them on screen-off. No public struct devfreq fields were added. This is inspired by the prior NGK/Sultan event boost mechanism, implemented with a separate registry and freezable workqueue.
- HZ250; schedstats disabled. Deadline I/O is the default, with soft read/write expiry100/1000ms. UFS sequential readahead defaults to256KiB. Existing LZ4 zram is retained. No process-kill or periodic RAM flush loop.
- Debug information and embedded kheaders are disabled. BPF JIT, encryption/filesystem boot drivers, module support and MODVERSIONS remain enabled. These are implementation changes, not measured FPS gains. ROM policies can override governor, I/O and readahead defaults. Hardware thermal shutdown and storage integrity protections remain.

## Root changes

SukiSU3.2.0 /13375 uses manual hooks and the official Manager certificate. R2 boot was confirmed by the user, but Manager3.2.0 displayed unsupported. Source audit found that its boot helper read argv from the old process image instead of the new exec arguments, and no initial manager scan ran at data-ready. This build passes the actual init argv[1] through the existing4.14 exec ABI, requests a data-ready scan, queues package rename scans outside the VFS callback, and reads Android's root-owned /data/system/packages.list before optional custom UID metadata. The legacy4.14 crypto descriptor is zero-initialized before certificate hashing. APK certificate checks and root/Manager authorization remain enforced. No fake Manager status or unauthenticated root shortcut is used.

The full root upstream project is under SukiSU; drivers/kernelsu is the exact compiled subtree and contains the same kernel changes. Use the supplied official SukiSU3.2.0 Manager APK. Physical activation of root on this final build still needs tester confirmation. KCAL and KPM are not included.

## Compatibility and installer

Targets vayu/bhima OSS-vendor Android13-16. Android version alone does not establish every vendor-module ABI. Vendor partitions/modules were not supplied, so full external module ABI remains unknown. WLAN is built in; charger options are translated from the reference config to this source. The reference boot was DerpFestA13(2023-10-03), kernel4.14.326-Derp, header2/page4096/raw Image/gzip ramdisk; no user ROM image or ramdisk is redistributed.

The ZIP repacks each installed ROM's boot and replaces kernel and its paired DTB/DTBO. It retains the current boot's ramdisk, cmdline, addresses, OS metadata and raw/gzip kernel format. Header0 uses a separate kernel_dtb input so the DTB stays outside gzip; header2 uses its DTB field. The unpack status bug from the original installer remains fixed. Flash final over the working R2 through recovery. If still using the old failed NGK package, restore the original ROM boot before installing.

## Build and verification

Install LLVM/Clang/LLD18.1.3, gcc host compiler, make, flex, bison, bc, OpenSSL/libelf development headers, cpio, xz, gzip and Python3. Put LLVM binaries on PATH or set TOOLCHAIN_DIR to its installation root. Run `bash build-singularity.sh`; the final ZIP is generated in dist without requiring Git history or online root-version lookups.

Run `SINGULARITY_KERNEL_SOURCE="$PWD" python3 -m unittest discover -s Singularity/tests -v`. Tests compile the actual C parser/boot/boost function bodies with narrow host API adapters. For ARM repack tests, set SINGULARITY_PACKAGE_DIR to an extracted final ZIP, SINGULARITY_QEMU_ARM to qemu-arm-static and SINGULARITY_REFERENCE_BOOT to a working vayu boot image, then run `python3 Singularity/test_repack.py`. The harness intercepts every flash operation into regular files. It never accesses physical block devices. The reference case is skipped without a supplied boot image.

See validation.json for final build/payload/host-test evidence. R2 boot confirmation does not verify the final root runtime or gaming performance.
