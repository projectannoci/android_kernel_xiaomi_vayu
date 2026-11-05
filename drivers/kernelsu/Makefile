kernelsu-objs := ksu.o
kernelsu-objs += allowlist.o
kernelsu-objs += dynamic_manager.o
kernelsu-objs += apk_sign.o
kernelsu-objs += sucompat.o
kernelsu-objs += throne_tracker.o
kernelsu-objs += core_hook.o
kernelsu-objs += ksud.o
kernelsu-objs += embed_ksud.o
kernelsu-objs += kernel_compat.o
kernelsu-objs += throne_comm.o

ifeq ($(CONFIG_KSU_TRACEPOINT_HOOK), y)
kernelsu-objs += ksu_trace.o
endif

kernelsu-objs += selinux/selinux.o
kernelsu-objs += selinux/sepolicy.o
kernelsu-objs += selinux/rules.o
ccflags-y += -I$(srctree)/security/selinux -I$(srctree)/security/selinux/include
ccflags-y += -I$(objtree)/security/selinux -include $(srctree)/include/uapi/asm-generic/errno.h

obj-$(CONFIG_KSU) += kernelsu.o
obj-$(CONFIG_KSU_TRACEPOINT_HOOK) += ksu_trace_export.o

obj-$(CONFIG_KPM) += kpm/


REPO_OWNER := SukiSU-Ultra
REPO_NAME := SukiSU-Ultra
REPO_BRANCH := main
KSU_VERSION_API := 3.2.0

GIT_BIN := /usr/bin/env PATH="$$PATH":/usr/bin:/usr/local/bin git
CURL_BIN := /usr/bin/env PATH="$$PATH":/usr/bin:/usr/local/bin curl

# Pinned official v3.2.0: 10000 + 2675 commits + 700.
KSU_VERSION := 13375
KSU_VERSION_FULL := v3.2.0-0af1ab28@v3.2.0
$(info -- SukiSU version: $(KSU_VERSION_FULL) [$(KSU_VERSION)])

ccflags-y += -DKSU_VERSION=$(KSU_VERSION)
ccflags-y += -DKSU_VERSION_FULL=\"$(KSU_VERSION_FULL)\"

# Custom Signs
ifdef KSU_EXPECTED_SIZE
ccflags-y += -DEXPECTED_SIZE=$(KSU_EXPECTED_SIZE)
$(info -- Custom KernelSU Manager signature size: $(KSU_EXPECTED_SIZE))
endif

ifdef KSU_EXPECTED_HASH
ccflags-y += -DEXPECTED_HASH=\"$(KSU_EXPECTED_HASH)\"
$(info -- Custom KernelSU Manager signature hash: $(KSU_EXPECTED_HASH))
endif

ifdef KSU_MANAGER_PACKAGE
ccflags-y += -DKSU_MANAGER_PACKAGE=\"$(KSU_MANAGER_PACKAGE)\"
$(info -- SukiSU Manager package name: $(KSU_MANAGER_PACKAGE))
endif

$(info -- Supported Unofficial Manager: 5ec1cff (GKI) ShirkNeko udochina (GKI and KPM))

ifeq ($(CONFIG_KSU_KPROBES_HOOK), y)
$(info -- SukiSU: CONFIG_KSU_KPROBES_HOOK)
else ifeq ($(CONFIG_KSU_TRACEPOINT_HOOK), y)
$(info -- SukiSU: CONFIG_KSU_TRACEPOINT_HOOK)
else ifeq ($(CONFIG_KSU_MANUAL_HOOK), y)
$(info -- SukiSU: CONFIG_KSU_MANUAL_HOOK)
endif

KERNEL_VERSION := $(VERSION).$(PATCHLEVEL)
KERNEL_TYPE := Non-GKI
# Check for GKI 2.0 (5.10+ or 6.x+)
ifneq ($(shell test \( $(VERSION) -ge 5 -a $(PATCHLEVEL) -ge 10 \) -o $(VERSION) -ge 6; echo $$?),0)
# Check for GKI 1.0 (5.4)
ifeq ($(shell test $(VERSION)-$(PATCHLEVEL) = 5-4; echo $$?),0)
KERNEL_TYPE := GKI 1.0
endif
else
KERNEL_TYPE := GKI 2.0
endif
$(info -- KERNEL_VERSION: $(KERNEL_VERSION))
$(info -- KERNEL_TYPE: $(KERNEL_TYPE))

$(info -- KERNEL_VERSION: $(KERNEL_VERSION))
ifeq ($(CONFIG_KPM), y)
$(info -- KPM is enabled)
else
$(info -- KPM is disabled)
endif

ccflags-y += -Wno-implicit-function-declaration -Wno-strict-prototypes -Wno-int-conversion -Wno-gcc-compat
ccflags-y += -Wno-declaration-after-statement -Wno-unused-function

# Keep a new line here!! Because someone may append config

# This CAF tree backports current_sid() with its SELinux state API.
ccflags-y += -DKSU_COMPAT_HAS_CURRENT_SID
