import pathlib,subprocess,tempfile,unittest,os
CORE=pathlib.Path(os.environ.get('SINGULARITY_CORE', str(pathlib.Path(__file__).resolve().parents[1]/'AnyKernel3/tools/ak3-core.sh'))).resolve()
class SplitBootStatus(unittest.TestCase):
 def run_case(self,status):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);(root/'partition').write_bytes(b'ANDROID!fixture')
   (root/'tools').mkdir()
   (root/'core.sh').write_text(CORE.read_text().rsplit('\nsetup_ak;',1)[0]+'\n')
   # Source the real installer core. Only boot unpacking and UI are replaced.
   s='''set +e
OUTFD=1
AKHOME="$PWD"
. "$PWD/core.sh"
BLOCK="$PWD/partition"
abort() { echo "ABORT:$*"; exit 99; }
magiskboot() { echo "unpack executed"; touch kernel ramdisk.cpio; return '''+str(status)+'''; }
split_boot
rc=$?
echo "SPLIT_RC:$rc"
[ -f "$SPLITIMG/kernel" ] || exit 88
exit "$rc"
'''
   return subprocess.run(['bash','-c',s],cwd=root,capture_output=True,text=True)
 def test_successful_unpack_is_accepted(self):
  r=self.run_case(0);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
 def test_chromeos_unpack_code_two_is_accepted(self):
  r=self.run_case(2);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
 def test_unpack_failure_is_rejected(self):
  r=self.run_case(1);self.assertEqual(r.returncode,99,r.stdout+r.stderr)
 def test_vendor_boot_code_three_is_accepted(self):
  r=self.run_case(3);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
 def test_missing_tool_is_rejected(self):
  r=self.run_case(127);self.assertEqual(r.returncode,99,r.stdout+r.stderr)
if __name__=='__main__':unittest.main()
