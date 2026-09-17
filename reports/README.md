# أدلة التنفيذ المتاحة للمراجعة

هذه الملفات نسخ من مخرجات التشغيل التي قدمها سلطان، وليست نتائج أُنشئت بملء دفاتر الدورة. يحفظ [فهرس البصمات والمصادر](provenance.json) مسار كل نسخة داخل أرشيفها الأصلي، وبصمة SHA-256، وحجمها. نُشرت التقارير الصغيرة لإتاحة التحقق المباشر؛ تبقى الجداول الثنائية وملفات ZIP في الأرشيف الكامل الذي يحتاج رابط مشاركة.

| اللاب | الأدلة المباشرة |
|---|---|
| 01 | [فحص المصدر](source_inspection.json)، [Bronze](bronze.json)، [بصمات المصدر المراجعة](review/source_hash_verification.json)، [سجلات Delta](delta_logs) |
| 02 | [التكلفة](cost_model_result.json)، [القياس](benchmark.json)، [خطة CSV](plans/csv.txt)، [خطة Delta](plans/delta_v0.txt) |
| 03 | [التهيئة](day02_staging_latest.json)، [Silver](day02_silver.json)، [المرجع والفعلي](day02_expected_vs_actual.json)، [نتائج وتوثيق dbt](dbt/README.md) |
| 04 | [المعاملات ورفض الكتابة](day03_transactions.json)، [الصيانة والاستعادة](day03_maintenance_latest.json)، [سجلات المعاملات](delta_logs) |
| 05 | [التدفق](day04_stream_latest.json)، [المنتج والمستهلك والتقدم](day04/e831afa2054745278b37edeccead1c62)، [نقطة التحقق والإزاحات](checkpoints/day04/gps_e831afa2054745278b37edeccead1c62) |
| 06 | [نتائج GX والعزل وأسباب الرفض](quality/README.md) |
| 07 | [التعافي](day05_recovery.json)، [الفشل المقصود](day05_failures/80b105e7d60d48508afdc098f54f5401.json)، [المؤشر](day05_gold_latest.json)، [الإصداران المحفوظان](releases) |
| 08 | [التقديم والتسوية](day05_serving_latest.json)، [ملف الإصدار المختار](releases/6a5c31f6be704c46b0365b3a37b9fbbf/release.json)، [صادرات CSV الثمانية](serving/94dd2c8cdf9e4d83837f3c318ad337d5)، [التسوية المستقلة للملفات](review/retained_artifact_verification.json) |

## حدود هذه الأدلة

- مسارات `mini_lakehouse/...` و`reports/...` داخل JSON الأصلية نسبية إلى مساحة التشغيل الأصلية `outputs/day01_bronze_jmbv27q9`، وليست كلها روابط إلى جذر GitHub. لم تُعدّل النصوص الأصلية حتى تبقى بصماتها صحيحة؛ استخدم `provenance.json` لتحديد مكان النسخة المنشورة.
- ملفات `delta_logs/` و`checkpoints/` نسخ أدلة للقراءة؛ وجودها وحده لا يعيد بناء جداول Parquet ولا يعيد وسيط Kafka أو موضوعاته.
- فشل الحالة المختلطة في GX والفشل المقصود أثناء بناء Gold متوقعان في سيناريو الاختبار؛ توجد نتائج إعادة الفحص والتعافي.
- سجل المنتج والمستهلك متاح؛ سجل عملية وسيط Kafka العام لم يرد في الحزم. لا ندّعي اختبار تحمل أعطال أو crash recovery.
- ملفات HTML الخاصة بـGX أصلية؛ الأرشيف الكامل يحتفظ بأصول الموقع البصرية أيضًا. نتائج JSON هي الدليل القابل للفحص مباشرة على GitHub.
- ملفات `review/` و`quality/quarantine_rows.json` نتائج مراجعة أو استخراج معلّم من ملفات محفوظة، وليست تشغيلًا جديدًا للمحركات.
- وصل [دفتر المستخدم المجمع والمقتطفات اليومية](../notebooks/README.md). وصلت مخرجات محاولة الجودة الجديدة: تسعة فحوص ناجحة، و7 معزولات، و75 معتمدًا. وصل فحص إعداد اليوم الخامس الحالي، ولجميع خلايا الكود الأربعين مخرجات؛ لم تُنفذ إعادة تشغيل كاملة من نسخة نظيفة. [مراجعة المحاولة الجديدة](review/quality_rerun_notebook.json)؛ وصل ZIP الجديد وفُحصت تقاريره وبصماته وصفوف Parquet؛ [نتيجة المراجعة](review/quality_recovery_archive_review.json). راجع [حالة الاستكمال](../SUBMISSION_STATUS.md).

للتحقق محليًا من البصمات والتسوية: `python3 scripts/verify_submission_evidence.py` من جذر المستودع.

[فحص إعداد اليوم الخامس الحالي](review/day05_setup_notebook.json) يوثق المتطلبات ومساحة العمل دون إعادة تشغيل اللابين 07 و08.
