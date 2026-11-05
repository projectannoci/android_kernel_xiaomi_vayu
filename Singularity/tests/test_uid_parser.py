import pathlib,subprocess,tempfile,unittest,os
SRC=pathlib.Path(os.environ.get('SINGULARITY_KERNEL_SOURCE','boot-audit/crdroid')).resolve()/'drivers/kernelsu/throne_tracker.c'
def function(name):
 s=SRC.read_text()
 if name+'(' not in s:return None
 a=s.index(name+'(');a=s.rfind('\n',0,a)+1;i=s.index('{',a);n=1;j=i+1
 while n:
  n+=(s[j]=='{')-(s[j]=='}');j+=1
 return s[a:j]
class Parser(unittest.TestCase):
 def parse(self,line,package_first):
  body=function('parse_package_uid_line');self.assertIsNotNone(body,'No standard packages.list UID parser')
  code='''#define _GNU_SOURCE
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <stdio.h>
#include <errno.h>
#include <ctype.h>
#define KSU_MAX_PACKAGE_NAME 256
#define EINVAL 22
#define ENAMETOOLONG 36
typedef uint32_t u32;
static char *skip_spaces(char *s) {while(isspace((unsigned char)*s))s++;return s;}
static int kstrtou32(char *s,int base,u32 *v) {char *end;errno=0;unsigned long n=strtoul(s,&end,base);if(errno||!*s||*end||n>UINT32_MAX)return -1;*v=n;return 0;}
'''+body+'''\nint main(int argc,char **argv){char pkg[256]={0};u32 uid=0;int rc=parse_package_uid_line(argv[1],atoi(argv[2]),pkg,&uid);printf("%d:%s:%u",rc,pkg,uid);return 0;}'''
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);(p/'t.c').write_text(code);r=subprocess.run(['gcc','-Wall','-Werror',str(p/'t.c'),'-o',str(p/'t')],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);return subprocess.check_output([str(p/'t'),line,str(int(package_first))],text=True)
 def test_standard_android_package_record(self):self.assertEqual(self.parse('com.sukisu.ultra 10234 0 /data/user/0/com.sukisu.ultra default:targetSdkVersion=35 none 0',True),'0:com.sukisu.ultra:10234')
 def test_uid_whitelist_record(self):self.assertEqual(self.parse('10234 com.sukisu.ultra',False),'0:com.sukisu.ultra:10234')
 def test_whitespace(self):self.assertEqual(self.parse(' \tcom.sukisu.ultra\t10234\t0',True),'0:com.sukisu.ultra:10234')
 def test_bad_uid(self):self.assertTrue(self.parse('com.sukisu.ultra not-a-uid 0',True).startswith('-'))
 def test_missing_uid(self):self.assertTrue(self.parse('com.sukisu.ultra',True).startswith('-'))
 def test_uid_overflow(self):self.assertTrue(self.parse('com.sukisu.ultra 4294967296',True).startswith('-'))
 def test_oversize_package(self):self.assertTrue(self.parse('a'*256+' 10234',True).startswith('-'))
if __name__=='__main__':unittest.main()
