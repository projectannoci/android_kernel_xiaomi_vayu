import pathlib,sys
p=pathlib.Path(sys.argv[1]);c=dict(x.split('=',1) for x in p.read_text().splitlines() if x.startswith('CONFIG_') and '='in x)
required=['MODULES','MODVERSIONS','BPF','BPF_SYSCALL','BPF_JIT','BPF_JIT_ALWAYS_ON','CGROUP_BPF','BLK_DEV_DM','DM_CRYPT','DM_DEFAULT_KEY','DM_VERITY','F2FS_FS','F2FS_FS_ENCRYPTION','FS_ENCRYPTION','FS_ENCRYPTION_INLINE_CRYPT','SCSI_UFSHCD','SCSI_UFS_CRYPTO','SCSI_UFS_CRYPTO_QTI','SECURITY_SELINUX','CPU_FREQ_DEFAULT_GOV_PERFORMANCE','DEVFREQ_GOV_PERFORMANCE','KSU','KSU_MANUAL_HOOK','QPNP_FG_GEN4','QPNP_SMB5','CHARGER_LN8000','QCA_CLD_WLAN']
missing=[k for k in required if c.get('CONFIG_'+k)!='y'];print('Required dependencies missing:',missing);assert not missing
assert c['CONFIG_QCOM_ADRENO_DEFAULT_GOVERNOR']=='"performance"'
print('Boot dependencies and performance config: PASS')
