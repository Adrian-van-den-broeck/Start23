# Revised swimming source: complete field comparison

Date: 2026-11-04, Europe/Amsterdam. Private developer review evidence; no activation.

The original intake and all historical review reports remain unchanged. This is a separate prospective source revision, not a correction of historical calculations. Original upload: `F:\Projecten Business\Start23\Code\.worktrees\joren-new-workout-catalog\docs\trainings\Zwemtrainingen_IF2.xlsx`. A byte-identical custody copy is retained in `docs/catalog/sources`.

| Version | Bytes | SHA-256 | Worksheet |
| --- | --- | --- | --- |
| HISTORICAL fixed-distance workbook | 7333 | `bd7d62439d77a0730f2b0eed6ab10b3d7c4d03bdc1645089024184b0b43e2674` | Zwemtrainingen Catalogus |
| PROSPECTIVE IF² candidate | 7405 | `7c2ee58f719036d41d15e4446727a7144b46b600df4a9ea26f78c82f7093f6cb` | Zwemtrainingen |

Historical PDF SHA-256: `ec1d141f60925628ca78b45801fedf8074c71adf57d9c877ada2e34199f5a59a`. Its fixed constants are not the new IF² method.

Both archives contain one visible sheet, extent A1:O24, 317 explicit cells including 300 workout cells. Every cell was inspected from OOXML without opening, resaving or recalculating either workbook. Numeric lexemes, displayed number formats, formula/cache presence, cell types, styles and serialized original cell XML are retained independently in the versioned JSON evidence. Both files contain zero formula cells; all source loads are stored constants. The archives themselves retain exact original lexical bytes.

43 cell values changed: 20 M loads, 10 C titles, 12 I/J zone cells across six rows, and A2. All 20 N ordered interval strings are value-identical. 83 complete cell records differ, including formatting: 60 style indices change (G/M/N workout cells); G5:G24 changes number format General -> 0.00, while M remains #,##0.0 and N remains General. Font definitions also change (6 -> 7 fonts; 9 -> 10 cell styles), so identical interval text does not imply identical serialized cell XML. Workbook sheet title changes as shown above. ZIP member contents change in docProps/core.xml, xl/workbook.xml, xl/styles.xml and xl/worksheets/sheet1.xml; the other five member contents remain identical. Metadata timestamps are not approvals.

| Cell | Historical exact value | Revised exact value |
| --- | --- | --- |
| A2 | Z1 t/m Z5 zijn in METERS. TSS is direct berekend per 100m. Rust (sec) genereert 0 TSS. | Z1 t/m Z5 zijn in METERS. TSS berekend door meters om te zetten naar minuten * IF^2 * 0.90. |
| M5 | 14.4 | 16.9 |
| M6 | 21.6 | 25.3 |
| M7 | 28.8 | 33.8 |
| M8 | 36 | 42.2 |
| M9 | 43.2 | 50.6 |
| M10 | 50.4 | 59.1 |
| M11 | 57.6 | 67.5 |
| M12 | 64.8 | 75.90000000000001 |
| M13 | 72 | 84.40000000000001 |
| C14 | Race pace blokken | Race pace blokken (5x) |
| M14 | 28.4 | 31.4 |
| C15 | Race pace blokken | Race pace blokken (10x) |
| M15 | 48.2 | 52.6 |
| C16 | Lange interval | Lange interval 5x400m |
| M16 | 56.6 | 58.2 |
| C17 | Lange interval | Lange interval 4x500m |
| M17 | 56.6 | 58.2 |
| M18 | 56.7 | 61.6 |
| C19 | Snelheid | Snelheid 10x100m |
| I19 | 300 | 600 |
| J19 | 300 | 0 |
| M19 | 37.3 | 39.9 |
| C20 | Snelheid | Snelheid 15x100m |
| I20 | 300 | 600 |
| J20 | 300 | 0 |
| M20 | 50.8 | 54.8 |
| C21 | Snelheid | Snelheid 20x100m |
| I21 | 300 | 600 |
| J21 | 300 | 0 |
| M21 | 64.3 | 69.59999999999999 |
| C22 | Weerstand | Weerstand 10x100m |
| I22 | 300 | 600 |
| J22 | 300 | 0 |
| M22 | 37.3 | 39.9 |
| C23 | Weerstand | Weerstand 15x100m |
| I23 | 300 | 600 |
| J23 | 300 | 0 |
| M23 | 50.8 | 54.8 |
| C24 | Weerstand | Weerstand 20x100m |
| I24 | 300 | 600 |
| J24 | 300 | 0 |
| M24 | 64.3 | 69.59999999999999 |

All other cell values, including IDs, sport, Expected RPE, Expected Zone, total distance, multiplier, ordered intervals and training focus, are unchanged. All six changed I/J pairs conflict with unchanged N: aggregate Z2=600/Z3=0, execution Z2=300/Z3=300. These are SOURCE-CONFLICTED, never silently normalized or activated. See the exact [correction request](JOREN_SWIMMING_IF2_CORRECTION_REQUEST_NL.md).
