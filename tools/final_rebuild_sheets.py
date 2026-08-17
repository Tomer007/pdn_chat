#!/usr/bin/env python3
"""
Final rebuild: uses Excel as source for Q38-Q56 and Q57-Q61 first choice,
augments Q57-Q61 with full ranking positions from JSON files where available.
"""

import json, glob, re
from collections import defaultdict, Counter
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

PDN_CODES = ['E1', 'E5', 'E9', 'A3', 'A7', 'A11', 'T4', 'T8', 'T12', 'P2', 'P6', 'P10']

wb = openpyxl.load_workbook('/Users/tomer.gur/dev-tools/pdn_chat/docs/combined_matrix_report.xlsx')
ws_src = wb['תשובות משתמשים']
header = [cell.value for cell in ws_src[1]]
q38_idx = header.index('Q38')
q57_idx = header.index('Q57')

# ===========================
# DATASET FROM EXCEL
# ===========================
data_by_code = defaultdict(lambda: {
    'q38_q56': defaultdict(list),
    'q57_q61_first': defaultdict(list),
    'q57_q61_pos': defaultdict(lambda: defaultdict(lambda: defaultdict(int))),
    'count': 0
})

for row in ws_src.iter_rows(min_row=2, values_only=True):
    user_str = row[0]
    if not user_str:
        continue
    parts = [p.strip() for p in str(user_str).split('|')]
    pdn_code = parts[0]
    if pdn_code not in PDN_CODES:
        continue

    data_by_code[pdn_code]['count'] += 1

    # Q38-Q56
    for i, q_num in enumerate(range(38, 57)):
        val = row[q38_idx + i]
        if val is not None:
            data_by_code[pdn_code]['q38_q56'][q_num].append(str(val))

    # Q57-Q61 first choice
    for i, q_num in enumerate(range(57, 62)):
        val = row[q57_idx + i]
        if val and isinstance(val, str) and len(val) <= 2 and val in ['T', 'A', 'E', 'P']:
            data_by_code[pdn_code]['q57_q61_first'][q_num].append(val)

# ===========================
# AUGMENT Q57-Q61 WITH FULL RANKINGS FROM JSON
# ===========================
json_files = glob.glob('/Users/tomer.gur/dev-tools/pdn_chat/saved_results/**/*_answers.json', recursive=True)

for jf in json_files:
    with open(jf) as f:
        try:
            data = json.load(f)
        except:
            continue
    if '57' not in data:
        continue

    meta = data.get('metadata', {})
    email = meta.get('email', '').lower()
    
    # Match PDN code by email pattern only (reliable)
    m = re.search(r'\+([EATP]\d+)@', email, re.IGNORECASE)
    if not m:
        continue
    pdn_code = m.group(1).upper()
    if pdn_code not in PDN_CODES:
        continue

    for q_num in range(57, 62):
        q_str = str(q_num)
        if q_str not in data:
            continue
        q_data = data[q_str]
        if not isinstance(q_data, dict):
            continue
        ranking = q_data.get('ranking', {})
        if not isinstance(ranking, dict):
            continue
        for trait, pos in ranking.items():
            if trait in ['T', 'A', 'E', 'P'] and isinstance(pos, int) and 1 <= pos <= 4:
                data_by_code[pdn_code]['q57_q61_pos'][q_num][pos][trait] += 1

# ===========================
# STYLES
# ===========================
hdr_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
hdr_font = Font(bold=True, color="FFFFFF")
alt_fill = PatternFill(start_color="EFF3FB", end_color="EFF3FB", fill_type="solid")
thin = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)

def make_header_row(ws, headers):
    for col, val in enumerate(headers, 1):
        c = ws.cell(row=1, column=col, value=val)
        c.fill = hdr_fill
        c.font = hdr_font
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        c.border = thin
    ws.row_dimensions[1].height = 45

def pct(cnt, total):
    return f'{round(cnt * 100 / total)}%' if total else ''

# ===========================
# Q38-Q56 SHEET
# ===========================
Q38_56 = {
    38: "בדיקה לעומק לפני נטילת סיכון", 39: "קושי עם חוסר ודאות",
    40: "קבלת החלטות במהירות", 41: "קושי לקבל הנחיות",
    42: "נוחות להוביל אחרים", 43: "מוחצנות/מופנמות - ילדות",
    44: "מוחצנות/מופנמות - בגרות", 45: "הובלה/הצטרפות - ילדות",
    46: "הובלה/הצטרפות - בגרות", 47: "דברנות/שתקנות - ילדות",
    48: "דברנות/שתקנות - בגרות", 49: "עימותים/ריצוי - ילדות",
    50: "עימותים/ריצוי - בגרות", 51: "עמידה בזמנים - ילדות",
    52: "עמידה בזמנים - בגרות", 53: "סדר/בלגן - ילדות",
    54: "סדר/בלגן - בגרות", 55: "מאופקות/נועזות - ילדות",
    56: "מאופקות/נועזות - בגרות",
}

if 'Q38-Q56 סטטיסטיקה' in wb.sheetnames:
    del wb['Q38-Q56 סטטיסטיקה']
ws38 = wb.create_sheet('Q38-Q56 סטטיסטיקה')

make_header_row(ws38, ['שאלה'] + [f'{c}\n(N={data_by_code[c]["count"]})' for c in PDN_CODES])

for ri, q_num in enumerate(range(38, 57), 2):
    label = Q38_56[q_num]
    c = ws38.cell(row=ri, column=1, value=f'Q{q_num} - {label}')
    c.border = thin
    c.alignment = Alignment(wrap_text=True, vertical='center')
    if ri % 2 == 0:
        c.fill = alt_fill

    for ci, code in enumerate(PDN_CODES, 2):
        answers = data_by_code[code]['q38_q56'].get(q_num, [])
        total = len(answers)
        if total == 0:
            val = '-'
        else:
            counts = Counter(answers)
            lines = [f'{t}: {pct(cnt, total)} ({cnt}/{total})' for t, cnt in sorted(counts.items(), key=lambda x: -x[1])]
            val = '\n'.join(lines)
        cell = ws38.cell(row=ri, column=ci, value=val)
        cell.border = thin
        cell.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')
        if ri % 2 == 0:
            cell.fill = alt_fill
    ws38.row_dimensions[ri].height = 38

ws38.column_dimensions['A'].width = 30
for col in range(2, 14):
    ws38.column_dimensions[get_column_letter(col)].width = 14

# ===========================
# Q57-Q61 SHEET
# ===========================
Q57_61 = {
    57: "דירוג: אסרטיבי/אכפתי/שיטתי/שופע רעיונות",
    58: "דירוג: מוביל/תומך/זהיר/רעיוניסט",
    59: "דירוג: ממוקד מטרה/נותן/שיטתי/אופטימי",
    60: "מה היית רוצה לקבל מהאבחון",
    61: "מה חשוב לך שהאבחון יספק",
}

if 'Q57-Q61 סטטיסטיקה' in wb.sheetnames:
    del wb['Q57-Q61 סטטיסטיקה']
ws57 = wb.create_sheet('Q57-Q61 סטטיסטיקה')

make_header_row(ws57, ['שאלה'] + [f'{c}\n(N={data_by_code[c]["count"]})' for c in PDN_CODES])

for ri, q_num in enumerate(range(57, 62), 2):
    label = Q57_61[q_num]
    c = ws57.cell(row=ri, column=1, value=f'Q{q_num}\n{label}')
    c.border = thin
    c.alignment = Alignment(wrap_text=True, vertical='center')
    if ri % 2 == 0:
        c.fill = alt_fill

    for ci, code in enumerate(PDN_CODES, 2):
        first = data_by_code[code]['q57_q61_first'].get(q_num, [])
        pos_data = data_by_code[code]['q57_q61_pos'].get(q_num, {})
        total = len(first)

        if total == 0:
            val = '-'
        else:
            lines = []
            # First choice %
            fc = Counter(first)
            for trait in sorted(fc, key=lambda t: -fc[t]):
                lines.append(f'{trait}: {pct(fc[trait], total)} ({fc[trait]})')
            # Position breakdown from JSON (if available)
            if pos_data:
                lines.append('')
                for pos in [1, 2, 3, 4]:
                    pd = pos_data.get(pos, {})
                    if pd:
                        pos_str = f'מקום {pos}: ' + '  '.join(f'{t}={cnt}' for t, cnt in sorted(pd.items()))
                        lines.append(pos_str)
            val = '\n'.join(lines).strip()

        cell = ws57.cell(row=ri, column=ci, value=val)
        cell.border = thin
        cell.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')
        if ri % 2 == 0:
            cell.fill = alt_fill
    ws57.row_dimensions[ri].height = 95

ws57.column_dimensions['A'].width = 38
for col in range(2, 14):
    ws57.column_dimensions[get_column_letter(col)].width = 16

# ===========================
# SAVE
# ===========================
wb.save('/Users/tomer.gur/dev-tools/pdn_chat/docs/combined_matrix_report.xlsx')
print('Saved. Sheets:', wb.sheetnames)

# ===========================
# VALIDATION REPORT
# ===========================
print('\n====== VALIDATION REPORT ======')
wb2 = openpyxl.load_workbook('/Users/tomer.gur/dev-tools/pdn_chat/docs/combined_matrix_report.xlsx')

# REQ 1: Organized sheet
ws_o = wb2['גיליון תשובות מאורגנים']
h1 = [c.value for c in ws_o[1]]
print(f'\nREQ 1 - גיליון תשובות מאורגנים')
print(f'  Headers: {h1}')
print(f'  User rows: {ws_o.max_row - 1}')
print(f'  PASS: {h1 == ["Name", "UID", "Verified PDN Code"] and ws_o.max_row > 1}')

# REQ 2: Q38-Q56
ws38v = wb2['Q38-Q56 סטטיסטיקה']
rows_38 = ws38v.max_row - 1
cols_38 = ws38v.max_column
h2 = [c.value for c in ws38v[1]]
print(f'\nREQ 2 - Q38-Q56 סטטיסטיקה')
print(f'  Questions: {rows_38} (expected 19)')
print(f'  Columns: {cols_38} (expected 13)')
print(f'  PDN codes in header: {[x.split(chr(10))[0] for x in h2[1:]]}')
# Show sample data for E1 and P10
for code_name, col_offset in [('E1', 1), ('A7', 5), ('P10', 12)]:
    n_header = ws38v.cell(row=1, column=col_offset+1).value
    sample = ws38v.cell(row=2, column=col_offset+1).value
    print(f'  {code_name} Q38: {str(sample)[:50]}')
print(f'  PASS: {rows_38 == 19 and cols_38 == 13}')

# REQ 3: Q57-Q61
ws57v = wb2['Q57-Q61 סטטיסטיקה']
rows_57 = ws57v.max_row - 1
cols_57 = ws57v.max_column
print(f'\nREQ 3 - Q57-Q61 סטטיסטיקה')
print(f'  Questions: {rows_57} (expected 5)')
print(f'  Columns: {cols_57} (expected 13)')
for code_name, col_offset in [('E1', 1), ('E5', 2), ('P2', 10)]:
    val = ws57v.cell(row=2, column=col_offset+1).value
    print(f'  {code_name}/Q57: {str(val)[:80]}')
print(f'  PASS: {rows_57 == 5 and cols_57 == 13}')
print()
print('====== ALL REQUIREMENTS ======')
all_pass = (
    h1 == ["Name", "UID", "Verified PDN Code"] and ws_o.max_row > 1 and
    rows_38 == 19 and cols_38 == 13 and
    rows_57 == 5 and cols_57 == 13
)
print(f'OVERALL PASS: {all_pass}')
