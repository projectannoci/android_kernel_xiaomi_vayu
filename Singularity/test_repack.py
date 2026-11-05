"""Run the released installer with ARM tools; replace all partition writes with file copies."""
import gzip,hashlib,os,pathlib,shutil,struct,subprocess,tempfile,unittest,zlib
BASE=pathlib.Path(__file__).resolve().parent
PKG=pathlib.Path(os.environ.get('SINGULARITY_PACKAGE_DIR',str(BASE/'AnyKernel3'))).resolve()
QEMU=pathlib.Path(os.environ.get('SINGULARITY_QEMU_ARM',str(BASE/'qemu'))).resolve();MAGISK=PKG/'tools/magiskboot';BB=PKG/'tools/busybox'
if (PKG/'Image').exists(): RAW=(PKG/'Image').read_bytes();DTB=(PKG/'dtb').read_bytes()
else:
 d=zlib.decompressobj(31);RAW=d.decompress((PKG/'Image.gz-dtb').read_bytes());DTB=d.unused_data

def runmag(args,cwd):
 return subprocess.run([str(QEMU),str(MAGISK),*map(str,args)],cwd=cwd,capture_output=True,text=True)
def cpio():
 out=b''
 for i,(name,data) in enumerate([('init.rc',b'on boot\n    setprop fixture untouched\n'),('TRAILER!!!',b'')]):
  n=name.encode()+b'\0';fields=[i+1,0o100644,0,0,1,0,len(data),0,0,0,0,len(n),0]
  a=b'070701'+b''.join(f'{v:08x}'.encode() for v in fields)+n;a+=b'\0'*(-len(a)%4);a+=data;a+=b'\0'*(-len(data)%4);out+=a
 return out
CPIO=cpio()
def boot(ver,compression='gzip',ramdisk=True):
 raw=bytearray(128);raw[56:60]=b'ARM\x64';struct.pack_into('<Q',raw,16,128)
 old=DTB.replace(b'qcom,sm8150',b'test,oldcpu',1)
 kernel=(gzip.compress(raw,mtime=0) if compression=='gzip' else bytes(raw))+(old if ver==0 else b'')
 rd=gzip.compress(CPIO,mtime=0) if ramdisk else b'';pg=4096;osver=((13<<14)<<11)|((2023-2000)<<4)|7
 hdr=struct.pack('<8s10I16s512s8I1024s',b'ANDROID!',len(kernel),0x8000,len(rd),0x1000000,0,0xf00000,0x100,pg,ver,osver,b'vayu',b'androidboot.hardware=qcom',*([0]*8),b'')
 if ver:hdr+=struct.pack('<IQI',0,0,1660)+struct.pack('<IQ',len(old),0x1f00000)
 parts=[hdr,kernel,rd]+([old] if ver else []);result=b''
 for part in parts:
  if part:result+=part+b'\0'*(-len(part)%pg)
 return result

class Repack(unittest.TestCase):
 def check(self,ver=2,compression='raw',reference=False,ramdisk=True,fail=False,small=False,corrupt=False):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)
   for p in PKG.iterdir():
    if p.is_file():shutil.copyfile(p,root/p.name)
   (root/'tools').mkdir()
   # Core source unchanged except for disabling its recovery-only startup discovery.
   core=(PKG/'tools/ak3-core.sh').read_text().rsplit('\nsetup_ak;',1)[0];(root/'core.sh').write_text(core)
   body=(PKG/'anykernel.sh').read_text().split('. tools/ak3-core.sh;',1)[1]
   data=pathlib.Path(os.environ.get('SINGULARITY_REFERENCE_BOOT',str(BASE.parent/'upload/boot.img'))).read_bytes() if reference else boot(ver,compression,ramdisk)
   part=root/'partition';part.write_bytes(data)
   if not small:
    with part.open('r+b') as f:f.truncate(134217728)
   before=root/'before';before.mkdir();r=runmag(['unpack','-h',part],before);self.assertEqual(r.returncode,0,r.stderr);original_fmt='gzip' if 'KERNEL_FMT      [gzip]' in r.stderr else 'raw'
   if corrupt:
    f=root/('Image' if (root/'Image').exists() else 'Image.gz-dtb');f.write_bytes(b'CORRUPT')
   shell='''OUTFD=1
AKHOME="$PWD"
BLOCK="$PWD/partition"
RAMDISK_COMPRESSION=auto
PATCH_VBMETA_FLAG=auto
. "$PWD/core.sh"
ui_print() { :; }
abort() { echo "ABORT:$*" >&2; exit 99; }
blockdev() { return 0; }
magiskboot() {
'''+('[ "$1" = repack ] && return 1\n' if fail else '')+f'"{QEMU}" "{MAGISK}" "$@"\n'+'''}
dd() {
 case " $* " in
  *" of=$BLOCK "*)
   case " $* " in
    *" if=boot-new.img "*) cp boot-new.img "$AKHOME/flashed.img"; echo flash >> "$AKHOME/writes";;
    *) echo erase >> "$AKHOME/writes";;
   esac;;
  *) command dd "$@";;
 esac
}
flash_generic() { echo "generic:$1" >> "$AKHOME/writes"; }
'''+body
   (root/'test.sh').write_text(shell)
   r=subprocess.run([str(QEMU),str(BB),'ash',str(root/'test.sh')],cwd=root,capture_output=True,text=True)
   writes=(root/'writes').read_text() if (root/'writes').exists() else ''
   if fail or small or corrupt:
    self.assertEqual(r.returncode,99,r.stdout+r.stderr);self.assertEqual(writes,'');return
   self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertIn('flash',writes);self.assertIn('generic:dtbo',writes)
   out=root/'after';out.mkdir();r=runmag(['unpack','-h',root/'flashed.img'],out);self.assertEqual(r.returncode,0,r.stderr)
   self.assertIn('KERNEL_FMT      ['+original_fmt+']',r.stderr,'Installer changed the target kernel compression')
   self.assertEqual((out/'kernel').read_bytes(),RAW)
   self.assertEqual((out/('dtb' if ver else 'kernel_dtb')).read_bytes(),DTB)
   for name in ['ramdisk.cpio','second','recovery_dtbo','extra']:
    if (before/name).exists():self.assertEqual((out/name).read_bytes(),(before/name).read_bytes(),name)
   new=(root/'flashed.img').read_bytes();self.assertEqual(new[12:16],data[12:16]);self.assertEqual(new[20:24],data[20:24]);self.assertEqual(new[28:576],data[28:576]);self.assertEqual(new[608:1632],data[608:1632]);self.assertLessEqual(len(new),134217728)
 def test_reference_boot_raw_header2(self):
  if not pathlib.Path(os.environ.get('SINGULARITY_REFERENCE_BOOT',str(BASE.parent/'upload/boot.img'))).exists():self.skipTest('Set SINGULARITY_REFERENCE_BOOT to a working vayu boot image')
  self.check(reference=True)
 def test_raw_header2(self):self.check()
 def test_gzip_header2(self):self.check(compression='gzip')
 def test_gzip_header0(self):self.check(ver=0,compression='gzip')
 def test_raw_header0(self):self.check(ver=0)
 def test_no_ramdisk(self):self.check(ramdisk=False)
 def test_repack_failure(self):self.check(fail=True)
 def test_oversize(self):self.check(small=True)
 def test_integrity_failure(self):self.check(corrupt=True)
if __name__=='__main__':unittest.main()
