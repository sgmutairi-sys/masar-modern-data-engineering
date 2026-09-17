# فحص الجودة والعزل

| العنصر | الملف | النتيجة |
|---|---|---|
| التقرير الشامل | [quality.json](quality.json) | تسعة فحوص ناجحة؛ المرشح غير الآمن لم يُعتمد |
| مجموعة التوقعات | [gx_expectation_suite.json](gx_expectation_suite.json) | مجموعة GX الأصلية |
| البيانات الموثوقة | [gx_trusted_validation.json](gx_trusted_validation.json) | 75 صفًا، نجاح |
| المرشح المختلط | [gx_mixed_validation.json](gx_mixed_validation.json) | 82 صفًا، فشل مقصود |
| إعادة الفحص | [gx_rechecked_validation.json](gx_rechecked_validation.json) | 75 صفًا، نجاح |
| العزل | [quarantine_rows.json](quarantine_rows.json) | سبعة صفوف مع أسبابها؛ استخراج من تقرير السياسة الأصلي، وليس قراءة جديدة لـDelta |

ملفات checkpoint الأصلية متاحة للحالات [الموثوقة](gx_trusted_checkpoint.json) و[المختلطة](gx_mixed_checkpoint.json) و[المعاد فحصها](gx_rechecked_checkpoint.json).

يحفظ [تقرير السياسة الأصلي](../day04_quality/876c88d851db4dd1b33d70f6ffa1b546/mixed_policy.json) الصفوف المقبولة والمرفوضة وأسبابها و`promote_allowed=false` للمرشح المختلط؛ وهو فحص سياسة مستقل عن GX. يتضمن `quality.json` حسابات الحداثة عند زمن السيناريو الثابت `2026-06-04T03:04:00Z`، ومراجع جدول العزل والجدول المعتمد وبصماتها.

توجد Data Docs ونتائجها الأصلية في [مجلد تشغيل الجودة](../day04_quality/876c88d851db4dd1b33d70f6ffa1b546). يحفظ الأرشيف الكامل ملفات Delta وأصول HTML البصرية غير المدرجة هنا.

## محاولة الجودة الجديدة في الدفتر

المخرجات المحفوظة في [دفتر اليوم الرابع](../../day04/STUDENT.ipynb) تعرض تسعة فحوص ناجحة و7 سجلات معزولة و75 سجلًا معتمدًا لمحاولة جديدة بعد استعادة مساحة العمل. معرف المرشح الظاهر `6801045da5ed4b1ca794844ac78b38bc`. [سجل الاستخراج من الدفتر](../review/quality_rerun_notebook.json). وصل ZIP الجديد وفُحصت صفوف Parquet ونتائج GX وبصمات Delta الخاصة به. أُضيف [فهرس مستقل للمحاولة الجديدة](reruns/6801045da5ed4b1ca794844ac78b38bc/README.md)، مع إبقاء ملفات هذه الصفحة أدلة المحاولة الأصلية المحددة أعلاه حفاظًا على ارتباط إصدار Gold السابق بها.
