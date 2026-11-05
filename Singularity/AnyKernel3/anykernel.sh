### Singularity v1 @ProjectNoci
### AnyKernel3 by osm0sis @ xda-developers
properties() { '
kernel.string=Singularity v1 @ProjectNoci
do.devicecheck=1
do.modules=0
do.systemless=0
do.cleanup=1
do.cleanuponabort=0
device.name1=vayu
device.name2=bhima
supported.versions=13 - 16
supported.patchlevels=
supported.vendorpatchlevels=
'; }
BLOCK=boot;
IS_SLOT_DEVICE=0;
RAMDISK_COMPRESSION=auto;
PATCH_VBMETA_FLAG=auto;
. tools/ak3-core.sh;
ui_print " " "Singularity v1 @ProjectNoci" "POCO X3 Pro | vayu / bhima";
sha256sum -c SHA256SUMS >/dev/null 2>&1 || abort "Payload integrity check failed.";
split_boot;
# Supply raw Image; MagiskBoot preserves the target kernel compression.
# Header v0 carries appended DTB; v2 stores the paired DTB separately.
if [ ! -f "$SPLITIMG/dtb" ]; then
  cp -f "$AKHOME/dtb" "$SPLITIMG/kernel_dtb" || abort "Kernel DTB staging failed.";
  rm -f "$AKHOME/dtb";
fi;
flash_boot;
flash_generic dtbo;
ui_print "Singularity installed.";
