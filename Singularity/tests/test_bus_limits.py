import pathlib,tempfile,subprocess,ctypes,unittest,os
ROOT=pathlib.Path(os.environ.get('SINGULARITY_KERNEL_SOURCE','boot-audit/crdroid')).resolve()
class Limits(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  s=(ROOT/'drivers/devfreq/devfreq.c').read_text();a=s.index('\t{\n\t\tunsigned long floor = singularity_devfreq_floor');b=s.index('\n\tif (devfreq->profile->get_cur_freq)',a);block=s[a:b]
  cls.tmp=tempfile.TemporaryDirectory();p=pathlib.Path(cls.tmp.name);code='''struct devfreq {unsigned long min_freq,max_freq;};
#define DEVFREQ_FLAG_LEAST_UPPER_BOUND 1
static unsigned long requested_floor;
static unsigned long singularity_devfreq_floor(struct devfreq *df) {return requested_floor;}
unsigned long select_frequency(unsigned long freq,unsigned long low,unsigned long high,unsigned long floor){struct devfreq dev={low,high},*devfreq=&dev;unsigned int flags=0;requested_floor=floor;
'''+block+'\n(void)flags;return freq;}';(p/'t.c').write_text(code);subprocess.run(['gcc','-shared','-fPIC','-Wall','-Werror',str(p/'t.c'),'-o',str(p/'t.so')],check=True);cls.lib=ctypes.CDLL(str(p/'t.so'));cls.fn=cls.lib.select_frequency;cls.fn.restype=ctypes.c_ulong;cls.fn.argtypes=[ctypes.c_ulong]*4
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_input_does_not_bypass_maximum(self):self.assertEqual(self.fn(100,0,3000,3879),3000)
 def test_wake_does_not_bypass_maximum(self):self.assertEqual(self.fn(100,0,8000,ctypes.c_ulong(-1).value),8000)
 def test_existing_minimum_preserved(self):self.assertEqual(self.fn(100,5000,8000,3879),5000)
 def test_unboosted_governor_preserved(self):self.assertEqual(self.fn(200,0,8000,0),200)
 def test_upper_limit_has_priority(self):self.assertEqual(self.fn(100,9000,8000,3879),8000)
if __name__=='__main__':unittest.main()
