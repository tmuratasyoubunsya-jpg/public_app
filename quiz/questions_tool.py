#!/usr/bin/env python3
"""ビジネス用語クイズの問題ファイル管理ツール

使い方:
  python questions_tool.py validate questions.json        # 問題の形式チェック
  python questions_tool.py stats    questions.json        # カテゴリ別の問題数
  python questions_tool.py to-csv   questions.json questions.csv   # Excelで編集する用
  python questions_tool.py from-csv questions.csv  questions.json  # Excelで編集した結果を反映

questions.json の形式（1問ぶん）:
  {"id": 1, "cat": "略語", "q": "「KPI」の意味は？", "a": "重要業績評価指標",
   "w": ["誤答1", "誤答2", "誤答3"], "e": "解説"}
  ・a が正解、w が誤答（3つ）。表示するときに選択肢の順番は自動でシャッフルされます。
  ・id は重複しない整数。
"""
import csv, json, sys
from collections import Counter

FIELDS = ["id", "カテゴリ", "問題", "正解", "誤答1", "誤答2", "誤答3", "解説"]

def load(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["questions"] if isinstance(data, dict) else data

def validate(items):
    errors, warns = [], []
    ids = Counter(); qs = Counter()
    for n, it in enumerate(items, 1):
        where = f"{n}件目(id={it.get('id')})"
        for k in ("id", "cat", "q", "a", "w", "e"):
            if k not in it or it[k] in ("", None, []):
                errors.append(f"{where}: 「{k}」がありません"); 
        if errors and errors[-1].startswith(where): continue
        ids[it["id"]] += 1; qs[it["q"].strip()] += 1
        if not isinstance(it["id"], int): errors.append(f"{where}: id は整数にしてください")
        w = it["w"]
        if not isinstance(w, list) or not (2 <= len(w) <= 4): errors.append(f"{where}: 誤答(w)は2〜4個にしてください（推奨は3個）")
        else:
            allc = [it["a"]] + w
            if len(set(x.strip() for x in allc)) != len(allc): errors.append(f"{where}: 選択肢に同じものがあります")
            if len(w) != 3: warns.append(f"{where}: 誤答が3個ではありません（{len(w)}個）")
        if len(it["q"]) > 90: warns.append(f"{where}: 問題文が長めです（{len(it['q'])}文字）")
        if len(it["e"]) > 140: warns.append(f"{where}: 解説が長めです（{len(it['e'])}文字）")
    for k, v in ids.items():
        if v > 1: errors.append(f"id={k} が {v}件 重複しています")
    for k, v in qs.items():
        if v > 1: errors.append(f"同じ問題文が {v}件 あります: {k}")
    return errors, warns

def stats(items):
    c = Counter(it.get("cat", "?") for it in items)
    print(f"合計 {len(items)} 問")
    for k, v in c.most_common(): print(f"  {k}: {v}")
    print(f"毎日5問なら、約 {len(items)//5} 日ぶんの問題があります（同じ問題が出るまで）")

def to_csv(items, out):
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        wr = csv.writer(f); wr.writerow(FIELDS)
        for it in items:
            w = (it["w"] + ["", "", ""])[:3]
            wr.writerow([it["id"], it["cat"], it["q"], it["a"], *w, it["e"]])

def from_csv(path):
    items = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if not (row.get("問題") or "").strip(): continue
            w = [(row.get(k) or "").strip() for k in ("誤答1", "誤答2", "誤答3")]
            w = [x for x in w if x]
            rid = (row.get("id") or "").strip()
            items.append({"id": int(rid) if rid else None, "cat": row["カテゴリ"].strip(), "q": row["問題"].strip(),
                          "a": row["正解"].strip(), "w": w, "e": row["解説"].strip()})
    mx = max([i["id"] for i in items if i["id"]] + [0])
    for it in items:
        if not it["id"]: mx += 1; it["id"] = mx
    return items

def save(items, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("[\n" + ",\n".join("  " + json.dumps(i, ensure_ascii=False) for i in items) + "\n]\n")

def main(argv):
    if len(argv) < 3: print(__doc__); return 2
    cmd, src = argv[1], argv[2]
    if cmd == "validate":
        items = load(src); e, w = validate(items)
        for x in e: print("エラー:", x)
        for x in w: print("注意:  ", x)
        print(f"{len(items)}問を確認: エラー {len(e)}件 / 注意 {len(w)}件"); return 1 if e else 0
    if cmd == "stats": stats(load(src)); return 0
    if cmd == "to-csv": to_csv(load(src), argv[3]); print("出力しました:", argv[3]); return 0
    if cmd == "from-csv":
        items = from_csv(src); e, w = validate(items)
        for x in e: print("エラー:", x)
        for x in w: print("注意:  ", x)
        if e: print("エラーがあるため、JSONは更新しませんでした。"); return 1
        save(items, argv[3]); print(f"{len(items)}問を書き出しました:", argv[3]); return 0
    print(__doc__); return 2

if __name__ == "__main__": sys.exit(main(sys.argv))
