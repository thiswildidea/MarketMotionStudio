# -*- coding: utf-8 -*-
r"""市值历程：胶囊判据的离线证明（对着已经截下来的帧跑）。

为什么要有这一支。`verify-caphistory.py` 需要开着应用、按着按钮、等着取数，而它离线的
那一半 —— 「曲线末端那颗胶囊认不认得出来」—— 恰恰是全部难度所在：胶囊与曲线**同色**，
又故意画在曲线前面，所以位置和颜色都用不上，只能看形状。这一支把那一半单独拎出来，用
`artifacts/` 里已经存好的帧复算一遍，于是：

  * 判据本身随时可复核，不必占着应用；
  * 判据改动前后能立刻对比（改之前这里必然红）；
  * **没有它，那几条断言就只剩「跑绿了」一个证据** —— 而锁屏、没解锁、窗口没被点着的
    机器上，跑绿和跑红都不是判据的错。

帧从哪来：`verify-caphistory.py` 每次跑都会把那一帧留在 `artifacts/` 下（`frame_at`）。
这里只读不写。

用法：python tools\verify-caphistory-shape.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio")
OUT = ROOT / "artifacts"

sys.path.insert(0, str(ROOT / "tools"))
sys.argv = ["verify-caphistory-shape"]

import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("v", str(ROOT / "tools" / "verify-caphistory.py"))
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

PASSED = []
FAILED = []


def check(name, ok, note=""):
    (PASSED if ok else FAILED).append((name, note))
    print("  %s %s%s" % ("√" if ok else "×", name, "" if ok else "  " + str(note)))


def frame(name):
    path = str(OUT / name)

    return path if os.path.exists(path) else None


def main():
    # 这一支本身就是一个断言：帧在不在。不在就说清「先跑真机那一支」而不是报一堆认不出。
    for name in ("caphistory-single.png", "caphistory-compare.png",
                 "caphistory-growth-early.png", "caphistory-growth-late.png"):
        check("有帧 %s" % name, frame(name) is not None,
              "先跑 tools\\verify-caphistory.py 把帧截下来")

    if FAILED:
        return 1

    # ---- 1) 单只：两块面板各挂一颗 -----------------------------------------------
    #
    # 这是这次改动的主诉：**单只也要有**。判据是「同色里另有一段平得离谱的」，因为
    # 胶囊离曲线只有 5 列（和曲线自己两段之间的缝一样宽），间距分不开。
    print("单只：")

    for word, test in (("市值", v.IS_TRACK_0), ("股价", v.IS_TRACK_1)):
        rows, box = v.curve_rows(frame("caphistory-single.png"), test)

        check("认得出%s那条线" % word, rows is not None and len(rows) > 100,
              "只认出 %s 列" % (None if rows is None else len(rows)))

        if rows is None:
            continue

        cap = v.capsule_of(rows, box)
        curve = v.line_span(rows, box)

        check("单只 %s 那块面板的线头上有胶囊" % word, cap is not None,
              v.capsule_note(rows, box))

        if cap is None:
            continue

        # **胶囊在曲线的右边**，这是「骑在生长的那一端」的判据，不是「右边多了一段」：
        # 曲线那一段必须自己先画到它前面去。
        check("单只 %s 的胶囊骑在曲线前面" % word,
              curve is not None and cap[0] > curve["columns"][-1],
              "胶囊起于 %d，曲线止于 %s" % (
                  cap[0], None if curve is None else curve["columns"][-1]))

        # 曲线不该长成平的。这一条是上面那条判据的**正向对照**：把同一把尺子架到曲线
        # 自己身上，它必须不通过 —— 否则「胶囊很平」就不是在说胶囊。
        #
        # **只问曲线那一段里的列。** `flat_runs` 数的是整张图上的平段，胶囊自己那一段
        # 当然在里面；不先把 `capsule_of` 认定的那些列摘掉，这一条问的就成了「胶囊平不
        # 平」—— 而它必然平，于是它必然红，红得像是判据坏了。
        only_curve = {x: y for x, y in rows.items() if x not in set(cap)}
        strays = [r for r in v.flat_runs(only_curve, 1) if r[0] < cap[0]]

        check("曲线自己没有一段平到能冒充胶囊",
              all(len(r) < v.CAPSULE_FLAT for r in strays),
              "曲线里数出了 %d 列长的平段（胶囊要 %d 列）" % (
                  max((len(r) for r in strays), default=0), v.CAPSULE_FLAT))

    # ---- 2) 多标的：几条线几颗胶囊 -----------------------------------------------
    print("多标的：")

    for i, test in ((1, v.IS_TRACK_0), (2, v.IS_TRACK_1)):
        rows, box = v.curve_rows(frame("caphistory-compare.png"), test)

        check("认得出第 %d 条线" % i, rows is not None and len(rows) > 100,
              "只认出 %s 列" % (None if rows is None else len(rows)))

        if rows is None:
            continue

        cap = v.capsule_of(rows, box)
        curve = v.line_span(rows, box)

        check("多标的第 %d 条线带着自己的末端胶囊" % i, cap is not None,
              v.capsule_note(rows, box))
        check("多标的第 %d 条的胶囊骑在曲线前面" % i,
              cap is not None and curve is not None and cap[0] > curve["columns"][-1],
              "胶囊 %s" % (None if cap is None else cap[0]))

    # ---- 3) 胶囊与曲线同色，量出来的两段不能是一个东西 ---------------------------
    #
    # 这一条是给「两个数字碰巧都好看」设的闸：如果 `line_span` 压根没把胶囊摘出去，
    # 它会一路画到胶囊右端，于是「胶囊在曲线右边」自动成立而毫无意义。
    print("两段是两段：")

    rows, box = v.curve_rows(frame("caphistory-single.png"), v.IS_TRACK_0)
    curve = v.line_span(rows, box)
    cap = v.capsule_of(rows, box)

    check("曲线那一段没把胶囊吞进去",
          curve is not None and cap is not None and curve["columns"][-1] < cap[0] - 4,
          "曲线止于 %s，胶囊起于 %s" % (
              None if curve is None else curve["columns"][-1],
              None if cap is None else cap[0]))

    # ---- 4) 生长：早先画出的点没有挪动过 -----------------------------------------
    print("生长：")

    early, box = v.curve_rows(frame("caphistory-growth-early.png"))
    late, _ = v.curve_rows(frame("caphistory-growth-late.png"))
    jump = round((box[3] - box[2]) * 0.45)

    head_early = v.line_span(early, box)
    head_late = v.line_span(late, box)
    first = v.curve_columns(early, box, jump, head_early["columns"] if head_early else None)
    second = v.curve_columns(late, box, jump, head_late["columns"] if head_late else None)

    check("晚的那一帧画得更长", len(second) > len(first), "%d → %d 列" % (len(first), len(second)))

    # 末端三列不算：早帧线到此为止（收笔），晚帧线继续往下走（过路），同一个 x 上落点差
    # 两像素是这两件事的区别，不是点挪了位。整段不算就没人能拿它当借口。
    moved = v.compare_curve(early, late, first)
    check("早先画出的点后来没有挪动过", not moved,
          "%d 列挪了位，头三列 %s" % (len(moved), moved[:3]))

    # **而末端确实挪过** —— 把容差收到 0 就看得见。写在这里是为了让上一条的宽容有据可查，
    # 不是为了让谁去修它：一个正在生长的末端就是会往下走。
    raw = v.compare_curve(early, late, first, tail=0)
    check("末端那一列确实从收笔变成过路（所以上面才要宽出三列）",
          len(raw) == 1 and raw[0][0] == first[-1],
          "tail=0 时挪动的列 %s" % raw[:3])

    return 0


if __name__ == "__main__":
    try:
        code = main()
    finally:
        print()
        print("通过 %d 项，失败 %d 项" % (len(PASSED), len(FAILED)))

        for name, note in FAILED:
            print("  × %s  %s" % (name, note))

        sys.exit(1 if FAILED else code)
