"""Run a NEW quality attempt against the restored, real Day 3 Delta table."""
from pathlib import Path
import datetime
import json
import os
import sys
import zipfile

BUNDLE = Path(__file__).resolve().parent
state = json.loads((BUNDLE / 'runtime.json').read_text())
ROOT = Path(state['root'])
WORK = Path(state['work'])
SOURCE = ROOT / 'data/masar-small-v1'
os.environ['JAVA_HOME'] = state['java_home']
for key in ('PYSPARK_GATEWAY_PORT', 'PYSPARK_GATEWAY_SECRET', 'PYSPARK_SUBMIT_ARGS'):
    os.environ.pop(key, None)
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / 'src'))

from masar.workspace import completed_bronze_workspace, require_fixed_dataset
from masar.runtime import start_spark
from masar.quality_gate import run_quality_lab
from masar.native_contracts import validate_stage_result

require_fixed_dataset(SOURCE)
if completed_bronze_workspace(ROOT) != WORK:
    raise RuntimeError('مساحة العمل تغيرت بعد الاستعادة. أرسل هذه الرسالة.')
previous = WORK / 'reports/day04_quality_latest.json'
previous_report = json.loads(previous.read_text()) if previous.is_file() else None
print('تشغيل محاولة جديدة لفحص الجودة؛ انتظر انتهاء الخلية.', flush=True)
print('Python:', sys.version.split()[0], flush=True)
spark = start_spark(WORK, kafka=False)
try:
    result = run_quality_lab(spark, SOURCE, WORK)
    validate_stage_result('lab06_quality', result)
    print(json.dumps({'scope': result['scope'], 'checks': result['checks']}, indent=2), flush=True)
    print('Quarantined records:', flush=True)
    spark.read.format('delta').load(str(WORK / result['quarantine_table'])).show(7, truncate=False)
    print('Approved rows:', spark.read.format('delta').load(str(WORK / result['approved_table'])).count(), flush=True)
finally:
    spark.stop()

stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
record = WORK / 'reports/colab_recovery' / stamp
record.mkdir(parents=True, exist_ok=False)
(record / 'attempt.json').write_text(json.dumps({
    'scope': 'NEW_QUALITY_ATTEMPT_AFTER_RESTORING_SAVED_WORKSPACE',
    'previous_quality_report': previous_report, 'new_quality_report': result,
    'recovery_environment': state,
    'complete_course_rerun': False,
}, ensure_ascii=False, indent=2) + '\n')
archive = Path('/content') / ('day04_quality_recovery_' + stamp + '.zip')
files = [ROOT / 'outputs/day01_bronze_success.json'] + sorted(p for p in WORK.rglob('*') if p.is_file())
with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
    for path in files:
        if path.is_symlink() or any(p.is_symlink() for p in path.parents):
            raise RuntimeError('وصلة غير متوقعة أثناء حفظ المخرجات.')
        z.write(path, path.relative_to(ROOT).as_posix())
(BUNDLE / 'latest_handoff_path.txt').write_text(str(archive) + '\n')
print('✅ اكتمل فحص الجودة وحُفظت مخرجات المحاولة الجديدة.', flush=True)
print('ملف المخرجات:', archive, flush=True)
