# أدلة dbt الأصلية

تقرير [dbt_attempt.json](dbt_attempt.json) يخص التشغيل `2be5afa6e0fe49a5adb0bf91f568b715` في مساحة `outputs/dbt_validation_nh58vl02`، وحالته `PASSED_DBT_NATIVE`. تطابق مع التقرير المقدم أولًا بالبايت، ووصلت ملفاته المكملة ضمن `masar_remaining_evidence.zip`.

- [صفحة التوثيق المولدة](commands/documentation/target/index.html)، [manifest](commands/documentation/target/manifest.json)، [catalog](commands/documentation/target/catalog.json): ستة نماذج وثلاثة مصادر.
- [نتائج الأوامر](commands): `run_results.json` الأصلي لكل build/gate/stage/documentation، و`sources.json` الأصلي لكل freshness.
- لقطات الأعمال الأصلية: [base](dbt_base_business_rows.json)، [rerun](dbt_rerun_business_rows.json)، [late](dbt_late_business_rows.json)، [late_replay](dbt_late_replay_business_rows.json).

نجحت ستة نماذج و23 اختبارًا في كل واحدة من مراحل build الأربع. نجح 13 اختبارًا في كل بوابة قبل الدمج. الأعداد 72، 72، 75، 75؛ وهذه مساحة مقارنة منفصلة عن Silver المصححة في اليوم الثالث.

GitHub يعرض مصدر HTML. لفتح التوثيق تفاعليًا بعد تنزيل المستودع، شغّل من جذره:

```bash
python3 -m http.server 8000 --bind 127.0.0.1 --directory reports/dbt/commands/documentation/target
```

ثم افتح `http://127.0.0.1:8000` محليًا. هذا يعرض التوثيق المحفوظ فقط، ولا يعيد تشغيل dbt. توجد بقية الآثار الأصلية الكاملة في أرشيف اليوم الثاني. `complete_course_verified=false` لا يعني فشل dbt؛ يعني أن هذا التقرير لا يعتمد الدورة كاملة.
