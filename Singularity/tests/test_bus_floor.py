import pathlib,subprocess,tempfile,ctypes,unittest,os
SRC=pathlib.Path(os.environ.get('SINGULARITY_KERNEL_SOURCE','boot-audit/crdroid')).resolve()/'drivers/devfreq/singularity_boost.c'
class BusFloor(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.fn=None
  if not SRC.exists():return
  s=SRC.read_text();a=s.index('static unsigned long singularity_floor_value(');i=s.index('{',a);d=1;j=i+1
  while d:
   d+=(s[j]=='{')-(s[j]=='}');j+=1
  code='#include <stdbool.h>\n#include <limits.h>\n#define time_before(a,b) ((long)((a)-(b))<0)\n'+s[a:j].replace('static unsigned long','unsigned long',1)
  p=pathlib.Path(cls.temp.name);(p/'t.c').write_text(code);subprocess.run(['gcc','-shared','-fPIC','-Wall','-Werror',str(p/'t.c'),'-o',str(p/'t.so')],check=True);cls.lib=ctypes.CDLL(str(p/'t.so'));cls.fn=cls.lib.singularity_floor_value;cls.fn.restype=ctypes.c_ulong;cls.fn.argtypes=[ctypes.c_ulong,ctypes.c_bool,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong]
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def value(self,*args):self.assertIsNotNone(self.fn,'Bus boost implementation absent');return self.fn(*args)
 def test_off_clears_both_votes(self):self.assertEqual(self.value(100,False,200,300,3879),0)
 def test_input_floor(self):self.assertEqual(self.value(100,True,120,0,3879),3879)
 def test_wake_peak(self):self.assertEqual(self.value(100,True,120,200,3879),ctypes.c_ulong(-1).value)
 def test_expired(self):self.assertEqual(self.value(200,True,120,199,3879),0)
 def test_exact_expiry(self):self.assertEqual(self.value(120,True,120,0,3879),0)
 def test_initial_zero(self):self.assertEqual(self.value(ctypes.c_ulong(-100).value,True,0,0,3879),0)
 def test_wraparound(self):self.assertEqual(self.value(ctypes.c_ulong(-5).value,True,5,0,4577),4577)
if __name__=='__main__':unittest.main()
