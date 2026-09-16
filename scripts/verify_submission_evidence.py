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

def main():
    notebook_review = verify_notebook_extracts()
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
            'clean_full_pipeline_rerun': False,
            'status': 'ARTIFACT_CHECKS_PASSED_SUBMISSION_STILL_INCOMPLETE'}

if __name__ == '__main__':
    print(json.dumps(main(), ensure_ascii=False, indent=2))

