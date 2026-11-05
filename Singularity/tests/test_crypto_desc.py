import pathlib,os,tempfile,subprocess,unittest
ROOT=pathlib.Path(os.environ.get('SINGULARITY_KERNEL_SOURCE','boot-audit/crdroid')).resolve()
class CryptoDesc(unittest.TestCase):
 def test_legacy_shash_flags_are_initialized(self):
  s=(ROOT/'drivers/kernelsu/apk_sign.c').read_text();a=s.index('static struct sdesc *init_sdesc(');b=s.index('\nstatic int calc_hash',a);body=s[a:b]
  code='''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define GFP_KERNEL 0
#define ERR_PTR(e) NULL
#define ENOMEM 12
struct crypto_shash {int unused;};
struct shash_desc {struct crypto_shash *tfm;unsigned int flags;};
struct sdesc {struct shash_desc shash;char ctx[];};
static unsigned long crypto_shash_descsize(struct crypto_shash *alg) {return 64;}
void *kmalloc(unsigned long n,int f) {void *p=malloc(n);memset(p,0xa5,n);return p;}
void *kzalloc(unsigned long n,int f) {return calloc(1,n);}
'''+body+'''\nint main(void){struct crypto_shash alg;struct sdesc *d=init_sdesc(&alg);printf("%u",d->shash.flags);free(d);return 0;}'''
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);(p/'t.c').write_text(code);subprocess.run(['gcc','-Wall','-Werror',str(p/'t.c'),'-o',str(p/'t')],check=True);self.assertEqual(subprocess.check_output([str(p/'t')],text=True),'0')
if __name__=='__main__':unittest.main()
