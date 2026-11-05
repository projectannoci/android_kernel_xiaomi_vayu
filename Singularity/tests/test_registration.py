import os,pathlib,subprocess,tempfile,unittest
ROOT=pathlib.Path(os.environ.get('SINGULARITY_KERNEL_SOURCE','boot-audit/crdroid')).resolve()
SRC=ROOT/'drivers/kernelsu'
def function(file,name):
 s=(SRC/file).read_text();a=s.index(name+'(');a=s.rfind('\n',0,a)+1;i=s.index('{',a);depth=1;j=i+1
 while depth:
  if s[j]=='{':depth+=1
  elif s[j]=='}':depth-=1
  j+=1
 return s[a:j]
def ctest(code,args=()):
 with tempfile.TemporaryDirectory() as d:
  p=pathlib.Path(d);(p/'test.c').write_text(code);r=subprocess.run(['gcc','-std=gnu11','-Wall','-Werror',str(p/'test.c'),'-o',str(p/'test')],capture_output=True,text=True);assert r.returncode==0,r.stderr
  return subprocess.run([str(p/'test'),*args],capture_output=True,text=True)
class Registration(unittest.TestCase):
 def test_android_random_suffix_with_hyphens(self):
  code='#include <string.h>\n#include <stdio.h>\n#define KSU_MAX_PACKAGE_NAME 256\n'+function('throne_tracker.c','get_pkg_from_apk_path')+'''\nint main(int argc,char **argv) { char pkg[256]={0};int r=get_pkg_from_apk_path(pkg,argv[1]);printf("%d:%s",r,pkg);return 0;}'''
  for path in ['/data/app/~~T-Token/com.sukisu.ultra-Abc-Def==/base.apk','/data/app/com.sukisu.ultra-1/base.apk','/data/app/~~T/com.sukisu.ultra-a_b==/base.apk']:
   with self.subTest(path=path):self.assertEqual(ctest(code,[path]).stdout,'0:com.sukisu.ultra')
 def test_package_notification_queues_scan(self):
  code='''#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#define pr_info(...) ((void)0)
#define pr_err(...) ((void)0)
#define IS_ERR(p) false
struct dentry {char *d_iname;};
static struct {void *mm;} task={ (void *)1 };
#define current (&task)
static struct {int val;} uid={1000};
#define current_uid() uid
static int queued,inline_scans;
void track_throne(void) {inline_scans++;}
void ksu_schedule_manager_scan(void) {queued++;}
void ksu_request_userspace_scan(void) {}
char *dentry_path_raw(struct dentry *d,char *buf,unsigned long n) {return "/data/system/packages.list";}
'''+function('core_hook.c','ksu_handle_rename')+'''\nint main(void){struct dentry old={"packages.list.tmp"},new={"packages.list"};ksu_handle_rename(&old,&new);uid.val=2000;ksu_handle_rename(&old,&new);printf("%d:%d",queued,inline_scans);return 0;}'''
  self.assertEqual(ctest(code).stdout,'1:0')
 def test_data_ready_requests_initial_scan(self):
  code='''#include <stdbool.h>
#include <stdio.h>
typedef unsigned int u32;
#define pr_info(...) ((void)0)
static bool is_boot_phase=true;
static u32 ksu_devpts_sid;
static int scans;
void ksu_schedule_manager_scan(void) { scans++; }
void ksu_load_allow_list(void) {}
void stop_input_hook(void) {}
u32 ksu_get_devpts_sid(void) {return 1;}
'''+function('ksud.c','on_post_fs_data')+'''\nint main(void) {on_post_fs_data();on_post_fs_data();printf("%d",scans);return 0;}'''
  self.assertEqual(ctest(code).stdout,'1')
if __name__=='__main__':unittest.main()
