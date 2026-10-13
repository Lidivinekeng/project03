import re
import shutil
import sys
import zipfile
import xml.etree.ElementTree as ET

import formulas

MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
RELS = "http://schemas.openxmlformats.org/package/2006/relationships"
RDOC = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
ET.register_namespace("", MAIN)


def evaluate(path):
    model = formulas.ExcelModel().loads(path).finish()
    out = {}
    for key, cell in model.calculate().items():
        mt = re.match(r"^'\[[^]]*\]([^']+)'!([A-Z]+\d+)$", key)
        if not mt:
            continue
        try:
            value = cell.value[0, 0]
        except Exception:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        out[(mt.group(1).upper(), mt.group(2))] = float(value)
    return out


def sheet_files(path):
    with zipfile.ZipFile(path) as zf:
        wb = ET.fromstring(zf.read("xl/workbook.xml"))
        rl = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    target = {r.get("Id"): r.get("Target").lstrip("/")
              for r in rl.findall(f"{{{RELS}}}Relationship")}
    out = {}
    for sh in wb.find(f"{{{MAIN}}}sheets"):
        rid = sh.get(f"{{{RDOC}}}id")
        out[sh.get("name").upper()] = target[rid]
    return out


def inject(path):
    values = evaluate(path)
    mapping = sheet_files(path)
    backup = path + ".nocache"
    shutil.copy2(path, backup)

    with zipfile.ZipFile(backup) as zf:
        items = {n: zf.read(n) for n in zf.namelist()}

    filled = 0
    missing = []
    for name, member in mapping.items():
        if member not in items or "worksheets/" not in member:
            continue
        root = ET.fromstring(items[member])
        changed = False
        for cell in root.iter(f"{{{MAIN}}}c"):
            if cell.find(f"{{{MAIN}}}f") is None:
                continue
            ref = cell.get("r")
            if (name, ref) not in values:
                missing.append(f"{name}!{ref}")
                continue
            for old in cell.findall(f"{{{MAIN}}}v"):
                cell.remove(old)
            ET.SubElement(cell, f"{{{MAIN}}}v").text = repr(values[(name, ref)])
            cell.attrib.pop("t", None)
            filled += 1
            changed = True
        if changed:
            items[member] = ET.tostring(root, xml_declaration=True,
                                        encoding="UTF-8")

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for n, data in items.items():
            zf.writestr(n, data)

    print(f"sheet map: {mapping}")
    print(f"cached {filled} formula results")
    if missing:
        print(f"no value available for {len(missing)} cells: "
              f"{', '.join(missing[:12])}")
    return values


def verify(path, values):
    from openpyxl import load_workbook
    cached = load_workbook(path, data_only=True)
    live = load_workbook(path, data_only=False)
    checked = wrong = lost = 0
    for ws in live.worksheets:
        cw = cached[ws.title]
        for row in ws.iter_rows():
            for cell in row:
                if not (isinstance(cell.value, str)
                        and cell.value.startswith("=")):
                    continue
                want = values.get((ws.title.upper(), cell.coordinate))
                if want is None:
                    continue
                got = cw[cell.coordinate].value
                checked += 1
                if got is None:
                    lost += 1
                elif abs(float(got) - want) > 1e-9:
                    wrong += 1
                    if wrong <= 5:
                        print(f"  WRONG {ws.title}!{cell.coordinate}: "
                              f"cached {got} vs computed {want}")
    print(f"verification: {checked} formula cells carry a cached value, "
          f"{wrong} disagree, {lost} empty")
    return wrong == 0 and lost == 0


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "p1_cost_distributions.xlsx"
    vals = inject(target)
    ok = verify(target, vals)
    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)
