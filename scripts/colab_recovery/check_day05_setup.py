"""Read-only Day 5 prerequisite check in the recovered course Python process.

This records a CURRENT setup check; it does not replay Labs 07/08 or manufacture
the missing historical setup-cell output. Each later engine invocation must use
the same course interpreter and initialize its own imports and Spark session.
"""
from pathlib import Path
import json
import os
import sys

state_path = Path('/content/masar_recovery/runtime.json')
if not state_path.is_file():
    raise RuntimeError('ملفات جلسة الاستعادة غير موجودة. أرسل هذه الرسالة قبل المتابعة.')
state = json.loads(state_path.read_text())
ROOT = Path(state['root'])
SOURCE = ROOT / 'data/masar-small-v1'
os.environ['JAVA_HOME'] = state['java_home']
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / 'src'))

from masar.workspace import completed_bronze_workspace, require_fixed_dataset
from masar.runtime import require_environment, start_spark
from masar.native_contracts import validate_stage_result

require_fixed_dataset(SOURCE)
environment = require_environment()
WORK = completed_bronze_workspace(ROOT)
prerequisites = {}
for stage, name in [('lab05_streaming', 'day04_stream_latest.json'),
                    ('lab06_quality', 'day04_quality_latest.json')]:
    report = json.loads((WORK / 'reports' / name).read_text())
    validate_stage_result(stage, report)
    prerequisites[stage] = {'run_id': report['run_id'], 'saved_checks_passed': all(report['checks'].values())}

print('Continue workspace:', WORK.relative_to(ROOT), flush=True)
print(json.dumps({
    'scope': 'CURRENT_DAY05_DEPENDENCY_AND_SAVED_PREREQUISITE_CHECK_ONLY',
    'python': environment['python'],
    'java': environment['java'],
    'course_python_executable': sys.executable,
    'prerequisites': prerequisites,
    'engine_executed': False,
    'labs_07_08_reexecuted': False,
    'meaning': 'Current setup validation; earlier Lab 07/08 notebook outputs remain historical.',
}, ensure_ascii=False, indent=2), flush=True)
print('✅ نجح فحص تهيئة اليوم الخامس. احفظ الدفتر ونزّله بصيغة ipynb.', flush=True)
