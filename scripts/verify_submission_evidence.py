"""Verify retained artifacts using only Python's standard library; no engine rerun."""
from pathlib import Path
from decimal import Decimal
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]

def read_json(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def verify_notebook_extracts():
    audit = read_json('reports/review/notebook_submission_review.json')
    master_path = ROOT / audit['original_published_path']
    if hashlib.sha256(master_path.read_bytes()).hexdigest() != audit['original_sha256']:
        raise ValueError('Original notebook hash mismatch')
    master = json.loads(master_path.read_text(encoding='utf-8'))
    missing = []
    for day in audit['days']:
        path = ROOT / day['path']
        if hashlib.sha256(path.read_bytes()).hexdigest() != day['sha256']:
            raise ValueError('Daily notebook hash mismatch: ' + day['path'])
        excerpt = json.loads(path.read_text(encoding='utf-8'))
        originals = master['cells'][day['source_cell_start_zero_based']:day['source_cell_end_exclusive']]
        if len(excerpt['cells']) != len(originals) + 1:
            raise ValueError('Daily cell count mismatch: ' + day['path'])
        for index, (original, retained) in enumerate(zip(originals, excerpt['cells'][1:])):
            for field in ['cell_type', 'source', 'outputs', 'execution_count', 'attachments']:
                if original.get(field) != retained.get(field):
                    raise ValueError('Cell content changed: ' + day['path'])
            if original['cell_type'] == 'code' and original.get('execution_count') is None:
                missing.append({'day': day['day'], 'source_cell_index_zero_based': day['source_cell_start_zero_based'] + index})
    return {'original_preserved': True, 'daily_excerpts_verified': len(audit['days']),
            'source_code_and_outputs_preserved': True,
            'cells_without_saved_execution': missing,
            'all_code_cells_have_saved_execution': not missing,
            'scope': 'INTEGRITY_CHECK_OF_SAVED_NOTEBOOKS_NOT_REEXECUTION'}


def verify_quality_recovery():
    review = read_json('reports/review/quality_recovery_archive_review.json')
    run_id = review['new_run_id']
    base = 'reports/quality/reruns/' + run_id
    provenance = read_json(base + '/provenance.json')
    for item in provenance['files']:
        if hashlib.sha256((ROOT / item['repository_path']).read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Quality recovery artifact mismatch: ' + item['repository_path'])
    native = read_json('reports/day04_quality/' + run_id + '/quality.json')
    notebook = read_json('notebooks/Sultan_Training_Project.ipynb')
    snapshot = read_json('reports/review/quality_rerun_notebook.json')
    cell = notebook['cells'][snapshot['quality_source_cell_index_zero_based']]
    output = '\n'.join(''.join(o.get('text', [])) for o in cell['outputs'])
    printed, _ = json.JSONDecoder().raw_decode(output[output.index('{\n  "scope"'):])
    if printed != {k: native[k] for k in ['scope', 'checks']}:
        raise ValueError('Notebook quality output differs from the native report')
    approved = read_json(base + '/approved_business_rows.json')
    lines = sorted(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False) for r in approved['rows'])
    digest = hashlib.sha256(('\n'.join(lines) + '\n').encode()).hexdigest()
    if len(approved['rows']) != 75 or digest != native['approved_business_digest']:
        raise ValueError('Approved snapshot differs from native business digest')
    policy = read_json('reports/day04_quality/' + run_id + '/mixed_policy.json')
    rejected = read_json(base + '/quarantine_rows.json')['rows']
    if len(rejected) != 7:
        raise ValueError('Quarantine snapshot count mismatch')
    expected = {r['candidate_row']: r for r in policy['quarantine']}
    for row in rejected:
        source = expected[row['candidate_row']]
        if (row['reason_codes'] != source['reason_codes'] or json.loads(row['raw_business_json']) != source['row']):
            raise ValueError('Quarantine snapshot differs from native policy')
    return {'published_original_files_verified': len(provenance['files']),
            'notebook_matches_native_quality_report': True,
            'approved_snapshot_rows': 75, 'quarantine_snapshot_rows': 7,
            'scope': 'PUBLISHED_SAVED_FILE_CHECK_NOT_NEW_PARQUET_READ_OR_ENGINE_RUN',
            'original_archive_independent_review': 'reports/review/quality_recovery_archive_review.json'}


def verify_day05_setup():
    saved = read_json('reports/review/day05_setup_notebook.json')
    audit = read_json('reports/review/notebook_submission_review.json')
    if saved['notebook_sha256'] != audit['original_sha256']:
        raise ValueError('Day 5 setup notebook hash mismatch')
    master = read_json(saved['notebook'])
    cell = master['cells'][saved['source_cell_index_zero_based']]
    output = '\n'.join(''.join(o.get('text', [])) for o in cell['outputs'])
    printed, _ = json.JSONDecoder().raw_decode(output[output.index('{\n  "scope"'):])
    if printed != saved['saved_setup_result']:
        raise ValueError('Day 5 setup snapshot differs from notebook output')
    if printed['engine_executed'] is not False or printed['labs_07_08_reexecuted'] is not False:
        raise ValueError('Setup scope must not claim a new engine run')
    for key, path in [('lab05_streaming', 'reports/day04_stream_latest.json'),
                      ('lab06_quality', 'reports/quality/rerun_latest.json')]:
        native = read_json(path)
        expected = {'run_id': native['run_id'], 'saved_checks_passed': all(native['checks'].values())}
        if printed['prerequisites'][key] != expected:
            raise ValueError('Day 5 prerequisite identity mismatch: ' + key)
    return {'saved_setup_output_verified': True,
            'prerequisite_report_ids_match': True,
            'labs_07_08_reexecuted': False,
            'scope': 'SAVED_SETUP_EVIDENCE_CHECK_NOT_ENGINE_REEXECUTION'}

def main():
    notebook_review = verify_notebook_extracts()
    quality_recovery = verify_quality_recovery()
    day05_setup = verify_day05_setup()
    provenance = read_json('reports/provenance.json')
    for item in provenance['files']:
        data = (ROOT / item['repository_path']).read_bytes()
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('Artifact hash mismatch: ' + item['repository_path'])
    source = read_json('data/masar-small-v1/manifest.json')
    for item in source['files']:
        data = (ROOT / 'data/masar-small-v1' / item['path']).read_bytes()
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('Source hash mismatch: ' + item['path'])
    serving = read_json('reports/day05_serving_latest.json')
    tables = {}
    for name, item in serving['exports'].items():
        data = (ROOT / item['path']).read_bytes()
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('Export hash mismatch: ' + name)
        with (ROOT / item['path']).open(encoding='utf-8', newline='') as stream:
            tables[name] = list(csv.DictReader(stream))
        if len(tables[name]) != item['rows']:
            raise ValueError('Export row count mismatch: ' + name)
    fact = tables['bi.fact_trips']
    actual = {'trip_count': len(fact), 'unique_trip_count': len({r['trip_id'] for r in fact}),
              'total_fare_sar': str(sum(Decimal(r['fare_sar']) for r in fact)),
              'gps_event_count': sum(int(r['gps_event_count']) for r in fact),
              'duration_seconds': sum(int(r['duration_seconds']) for r in fact)}
    expected = {'trip_count': 75, 'unique_trip_count': 75, 'total_fare_sar': '1880.60',
                'gps_event_count': 217, 'duration_seconds': 95400}
    differences = {k: str(Decimal(str(actual[k]))-Decimal(str(v))) for k,v in expected.items()}
    if any(Decimal(v) != 0 for v in differences.values()):
        raise ValueError('Reconciliation failed: ' + str(differences))
    labels = tables['ai.zone_hourly_labels']
    # The original serving report records detailed feature and label validations.
    if not serving['checks']['labels_not_fabricated'] or not serving['checks']['feature_availability_checked']:
        raise ValueError('Saved feature/label checks did not pass')
    return {'scope': 'SAVED_ARTIFACT_REVIEW_NOT_SPARK_KAFKA_DBT_RERUN',
            'verified_original_artifacts': len(provenance['files']),
            'source_files_verified': len(source['files']), 'exports_verified': len(tables),
            'actual': actual, 'expected': expected, 'differences': differences,
            'submitted_notebook_integrity': notebook_review,
            'quality_recovery_artifacts': quality_recovery,
            'day05_current_setup': day05_setup,
            'clean_full_pipeline_rerun': False,
            'status': 'ARTIFACT_CHECKS_PASSED_SUBMISSION_STILL_INCOMPLETE'}

if __name__ == '__main__':
    print(json.dumps(main(), ensure_ascii=False, indent=2))

