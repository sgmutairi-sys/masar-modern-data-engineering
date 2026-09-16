from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from google.colab import files
import json

root = Path('/content/masar-modern-data-engineering').resolve()
outputs = root / 'outputs'
if not outputs.is_dir():
    raise RuntimeError('شغّل الخلية في جلسة Colab التي تحتوي مشروعك ومخرجاته.')

selected = set()
missing = []
for name in ('day01_handoff.zip', 'day02_handoff.zip'):
    path = outputs / name
    if path.is_file():
        selected.add(path)
        print('وجدت:', name)
    else:
        missing.append(name)

for name in ('source_inspection.json', 'cost_model_result.json'):
    found = [p for p in outputs.rglob(name) if p.is_file()]
    selected.update(found)
    if not found:
        missing.append(name + ' (قد يوجد داخل أرشيف اليوم الأول)')

expected_workspace = 'outputs/day01_bronze_jmbv27q9'
for report in outputs.glob('dbt_validation_*/reports/dbt_attempt.json'):
    try:
        data = json.loads(report.read_text())
    except (OSError, ValueError):
        continue
    workspace = str(data.get('input_workspace', '')).replace('\\', '/')
    if data.get('status') == 'PASSED_DBT_NATIVE' and workspace.endswith(expected_workspace):
        dbt_dir = report.parent.parent
        selected.update(p for p in dbt_dir.rglob('*') if p.is_file())
        print('وجدت مساحة dbt الناجحة:', dbt_dir.name)

safe_files = []
for path in sorted(selected):
    resolved = path.resolve()
    if not resolved.is_relative_to(root) or path.is_symlink():
        continue
    rel = path.relative_to(root)
    if any(part in {'.git', '.venv', '__pycache__', '.ipynb_checkpoints'} for part in rel.parts):
        continue
    if path.name == '.env' or path.suffix.lower() in {'.pem', '.key'}:
        continue
    safe_files.append(path)

if not safe_files:
    raise RuntimeError('لم توجد الأدلة في هذه الجلسة. أرفق أرشيفَي اليومين الأول والثاني المحفوظين لديك.')

archive = Path('/content/masar_remaining_evidence.zip')
with ZipFile(archive, 'w', ZIP_DEFLATED) as bundle:
    for path in safe_files:
        bundle.write(path, path.relative_to(root).as_posix())
    bundle.writestr('COLLECTION_STATUS.json', json.dumps({
        'action': 'collect_existing_files_without_rerunning_labs',
        'expected_workspace': expected_workspace,
        'file_count': len(safe_files),
        'not_found_as_separate_files': missing,
        'notebooks_included': False
    }, ensure_ascii=False, indent=2))

print('جُمعت', len(safe_files), 'ملفات موجودة. أرفق الملف الناتج في المحادثة.')
print('نزّل الدفاتر الخمسة من قائمة ملف في Colab وأرفقها أيضًا.')
files.download(str(archive))
