import pathlib,tempfile,subprocess,unittest,os
ROOT=pathlib.Path(os.environ.get('SINGULARITY_KERNEL_SOURCE','boot-audit/crdroid')).resolve()
def function(name):
 s=(ROOT/'drivers/kernelsu/ksud.c').read_text()
 if name+'(' not in s:return None
 a=s.index(name+'(');a=s.rfind('\n',0,a)+1;i=s.index('{',a);d=1;j=i+1
 while d:
  d+=(s[j]=='{')-(s[j]=='}');j+=1
 return s[a:j]
class InitExec(unittest.TestCase):
 def test_new_exec_arguments_drive_policy_and_data_scan(self):
  hook=function('ksu_handle_init_exec');self.assertIsNotNone(hook,'No init hook for the actual exec arguments')
  code='''#include <stdbool.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#define __user
#define likely(x) (x)
#define pr_info(...) ((void)0)
#define IS_ERR_OR_NULL(x) (!(x))
#define strstarts(s,p) (!strncmp((s),(p),strlen(p)))
static bool ksu_execveat_hook=true;
static int policies,post_data,namespaces;
struct uid {int val;};
static struct uid current_uid(void) {struct uid u={0};return u;}
static long strncpy_from_user(char *d,const char *s,unsigned long n) {strncpy(d,s,n);return strlen(s);}
static void apply_kernelsu_rules(void) {policies++;}
static void ksu_android_ns_fs_check(void) {namespaces++;}
static void on_post_fs_data(void) {post_data++;}
static void stop_execve_hook(void) {ksu_execveat_hook=false;}
'''+function('ksu_handle_bprm_ksud')+'\n'+hook+'''\nint main(void){ksu_handle_init_exec("/system/bin/init","second_stage");ksu_handle_init_exec("/system/bin/init","second_stage");ksu_handle_init_exec("/system/bin/app_process64",NULL);printf("%d:%d:%d",policies,post_data,namespaces);return 0;}'''
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);(p/'t.c').write_text(code);r=subprocess.run(['gcc','-Wall','-Werror',str(p/'t.c'),'-o',str(p/'t')],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(subprocess.check_output([str(p/'t')],text=True),'1:1:1')
if __name__=='__main__':unittest.main()
