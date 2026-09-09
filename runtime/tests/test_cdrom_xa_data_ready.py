"""Compile the production CD controller and exercise mixed-sector delivery."""
from pathlib import Path
import argparse,os,shutil,subprocess,tempfile

ROOT=Path(__file__).resolve().parents[2]
cc=os.environ.get('CC') or shutil.which('gcc') or shutil.which('cc')
parser=argparse.ArgumentParser()
parser.add_argument('--source',type=Path,help='Alternate cdrom.c for before/after regression verification')
args=parser.parse_args()
if not cc:
    raise SystemExit('A C compiler is required for the executable CD/XA regression')
with tempfile.TemporaryDirectory(prefix='cdrom-xa-') as temp:
    exe=Path(temp)/'test.exe'
    extra=[]
    if args.source:
        extra=['-DCDROM_TEST_SOURCE="'+args.source.resolve().as_posix()+'"']
    subprocess.run([cc,'-std=c11','-O2','-ffunction-sections','-fdata-sections',
                    '-DPSX_NO_DEBUG_TOOLS','-I'+str(ROOT/'runtime/include'),
                    '-I'+str(ROOT/'runtime/src'),*extra,
                    str(ROOT/'runtime/tests/test_cdrom_xa_data_ready.c'),
                    '-Wl,--gc-sections','-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True,timeout=20)
