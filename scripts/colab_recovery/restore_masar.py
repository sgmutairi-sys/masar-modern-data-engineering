"""Restore Sultan's saved workspace and prepare the course's quality runtime."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import zipfile

BUNDLE = Path(__file__).resolve().parent
ROOT = Path('/content/masar-modern-data-engineering')
VENV = Path('/content/masar-course-py311')
PYTHON = VENV / 'bin/python'
COMMIT = 'a08f7c92f1929ea2b7b2f73842a00b8bfa30628a'
ARCHIVE_SHA256 = '861ecbd7c0fc665d42c2b1749f693353b214ba32636151c17b31811472575bef'
VERIFIED_ARCHIVES = {
    ARCHIVE_SHA256: 'day05_handoff.zip',
    '93c80093b3838ff962bd302c635789164b3765928891a6ce9898fccb979dd950':
        'day04_quality_recovery_20260916T180618912333Z.zip',
}


def run(args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, **kwargs)


def restore_outputs(archive, root, expected_sha256=ARCHIVE_SHA256):
    """Check every member and all conflicts before creating any output file."""
    if (expected_sha256 not in VERIFIED_ARCHIVES
            or hashlib.sha256(archive.read_bytes()).hexdigest() != expected_sha256):
        raise RuntimeError('ملف المخرجات مختلف عن نسختك التي تحققنا منها.')
    root = root.resolve()
    plan = []
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise RuntimeError('ملف المخرجات تالف.')
        names = set()
        for info in z.infolist():
            rel = PurePosixPath(info.filename)
            if (rel.is_absolute() or '..' in rel.parts or not rel.parts
                    or rel.parts[0] != 'outputs' or '\\' in info.filename
                    or stat.S_ISLNK(info.external_attr >> 16)
                    or info.filename in names):
                raise RuntimeError('مسار غير متوقع داخل ملف الاستعادة.')
            names.add(info.filename)
            target = root.joinpath(*rel.parts)
            for parent in [target, *target.parents]:
                if parent == root:
                    break
                if parent.is_symlink():
                    raise RuntimeError('توجد وصلة ملفات في مسار الاستعادة: ' + str(parent))
            if info.is_dir():
                continue
            payload = z.read(info)
            if target.exists():
                if not target.is_file() or target.read_bytes() != payload:
                    raise RuntimeError(
                        'توجد مخرجات مختلفة؛ أوقفت الاستعادة للحفاظ عليها: ' + str(target)
                    )
            else:
                if any(p.exists() and not p.is_dir() for p in target.parents):
                    raise RuntimeError('مجلد الاستعادة يحتوي ملفًا متعارضًا.')
                plan.append((target, payload))
        for target, payload in plan:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as f:
                f.write(payload)
    return len(plan)


def java17():
    candidates = list(Path('/usr/lib/jvm').glob('*17*'))
    for candidate in candidates:
        command = candidate / 'bin/java'
        if command.is_file():
            result = subprocess.run([str(command), '-version'], capture_output=True, text=True)
            if result.returncode == 0 and re.search(r'version\s+"17[.\"]', result.stderr + result.stdout):
                return str(candidate.resolve())
    return None


def main(archive_path=None, check_day05=False):
    if not Path('/content').is_dir():
        raise RuntimeError('شغّل هذه الخلية داخل Google Colab.')

    archive = Path(archive_path).resolve() if archive_path else BUNDLE / 'day05_handoff.zip'
    if not archive.is_file():
        raise RuntimeError('ارفع ملف المخرجات الذي حددناه أولًا، ثم أعد تشغيل الخلية.')
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    if archive_sha not in VERIFIED_ARCHIVES:
        raise RuntimeError('الملف المرفوع ليس إحدى نسختي المخرجات اللتين تحققنا منهما.')
    if check_day05 and not (BUNDLE / 'check_day05_setup.py').is_file():
        raise RuntimeError('سكربت فحص اليوم الخامس غير موجود. انسخ خلية الاستعادة كاملة.')
    print('الأرشيف المعتمد:', VERIFIED_ARCHIVES[archive_sha], flush=True)

    print('1/4 تنزيل كود مشروعك من GitHub...', flush=True)
    if not ROOT.exists():
        run(['git', 'clone', '--quiet', '--branch', 'develop',
             'https://github.com/sgmutairi-sys/masar-modern-data-engineering.git', ROOT])
        run(['git', '-C', ROOT, 'checkout', '--quiet', '--detach', COMMIT])
    if not (ROOT / 'src/masar/quality_gate.py').is_file():
        raise RuntimeError('مجلد المشروع موجود لكنه غير مكتمل. أرسل هذه الرسالة قبل المتابعة.')
    head = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    if head != COMMIT:
        raise RuntimeError('توجد نسخة أخرى من المشروع. أوقفت الاستعادة للحفاظ على تعديلاتك.')

    print('2/4 استعادة مخرجاتك السابقة...', flush=True)
    count = restore_outputs(archive, ROOT, expected_sha256=archive_sha)
    print('الملفات المستعادة:', count, flush=True)

    print('3/4 تجهيز Python 3.11 وJava 17 ومتطلبات فحص الجودة...', flush=True)
    if not PYTHON.is_file():
        if VENV.exists():
            raise RuntimeError('بيئة Python موجودة لكنها غير مكتملة. أرسل هذه الرسالة.')
        uv_dir = Path('/content/masar-uv-tool')
        uv = uv_dir / 'bin/uv'
        if not uv.is_file():
            run([sys.executable, '-m', 'pip', 'install', '--quiet', '--target', uv_dir, 'uv'])
        run([uv, 'venv', '--python', '3.11', '--seed', VENV])
    version = subprocess.check_output([str(PYTHON), '-c',
        'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'], text=True).strip()
    if version != '3.11':
        raise RuntimeError('إصدار بيئة المشروع ليس Python 3.11.')
    java_home = java17()
    if java_home is None:
        if os.geteuid() != 0 or not shutil.which('apt-get'):
            raise RuntimeError('Java 17 غير متاح. أرسل هذه الرسالة.')
        run(['apt-get', 'update', '-qq'])
        run(['apt-get', 'install', '-y', '-qq', 'openjdk-17-jre-headless'])
        java_home = java17()
    if java_home is None:
        raise RuntimeError('لم يكتمل تجهيز Java 17.')
    env = os.environ.copy()
    env['JAVA_HOME'] = java_home
    for key in ('PYTHONPATH', 'PYTHONHOME', 'PYSPARK_GATEWAY_PORT', 'PYSPARK_GATEWAY_SECRET', 'PYSPARK_SUBMIT_ARGS'):
        env.pop(key, None)
    run([PYTHON, '-m', 'pip', 'install', '--quiet', '-r', ROOT / 'requirements-day04.txt'], env=env)
    run([PYTHON, '-m', 'pip', 'check'], env=env)

    print('4/4 التحقق من البيانات ومخرجات اليوم الثالث...', flush=True)
    check = '''
from pathlib import Path
import json, sys
root = Path(sys.argv[1])
sys.path.insert(0, str(root / 'src'))
from masar.workspace import completed_bronze_workspace, require_fixed_dataset
from masar.runtime import require_environment
from masar.quality_gate import quality_preflight
require_fixed_dataset(root / 'data/masar-small-v1')
work = completed_bronze_workspace(root)
require_environment()
issues = quality_preflight()['issues']
if issues:
    raise RuntimeError('; '.join(issues))
report = work / 'reports/day03_transactions.json'
table = work / 'mini_lakehouse/silver/trips'
if not report.is_file() or not (table / '_delta_log').is_dir() or not any(table.rglob('*.parquet')):
    raise RuntimeError('مخرجات اليوم الثالث غير مكتملة')
print(json.dumps({'root': str(root), 'work': str(work), 'python': sys.version.split()[0]}))
'''
    result = subprocess.check_output([str(PYTHON), '-c', check, str(ROOT)], env=env, text=True)
    state = json.loads(result.strip())
    state.update({'python_executable': str(PYTHON), 'java_home': java_home,
                  'source_commit': COMMIT, 'restored_archive_sha256': archive_sha,
                  'restored_archive_filename': VERIFIED_ARCHIVES[archive_sha],
                  'scope': 'RESTORED_WORKSPACE_AND_DEPENDENCIES_ONLY_ENGINE_NOT_RUN'})
    (BUNDLE / 'runtime.json').write_text(json.dumps(state, indent=2) + '\n')
    print('Python:', state['python'], flush=True)
    print('مساحة العمل:', state['work'], flush=True)
    if check_day05:
        print('تمت الاستعادة؛ جارٍ فحص تهيئة اليوم الخامس...', flush=True)
        run([PYTHON, '-u', BUNDLE / 'check_day05_setup.py'], env=env)
    else:
        print('✅ تمت الاستعادة والتهيئة.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, help='A previously verified saved-workspace ZIP.')
    parser.add_argument('--day05', action='store_true', help='Run the read-only current Day 5 setup check after restoration.')
    args = parser.parse_args()
    main(archive_path=args.archive, check_day05=args.day05)
