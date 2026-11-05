import pathlib,stat,sys,zipfile
stage=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2])
assert (stage/'Image').read_bytes()[56:60]==b'ARM\x64'
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(stage.rglob('*')):
  if not p.is_file():continue
  n=p.relative_to(stage).as_posix();i=zipfile.ZipInfo(n);i.create_system=3;i.compress_type=zipfile.ZIP_DEFLATED
  mode=0o755 if n=='anykernel.sh' or n=='META-INF/com/google/android/update-binary' or n.startswith('tools/') else 0o644
  i.external_attr=(stat.S_IFREG|mode)<<16;z.writestr(i,p.read_bytes())
with zipfile.ZipFile(out) as z:assert z.testzip() is None
print(out)
