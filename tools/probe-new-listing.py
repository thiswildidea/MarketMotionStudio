# -*- coding: utf-8 -*-
"""「持仓收益」选中一只票却报 `None of the instruments has a price inside the range.`
时，问源端到底有没有这只票 —— 以及它在不在被问的那个区间里。

2026-10-17 的实例：宇树科技W（科创板 sh688836）首根 K 线是 2026-08-19，
而页面上的自定义区间是 2012-06-28 → 2026-06-22，早于上市日 → 区间内 0 根 →
整页只有它一只被勾上 → `PositionLoader` 抛上面那句英文。

用法：
    python tools/probe-yushu.py                # 默认就是在查宇树科技
    python tools/probe-yushu.py 寒武纪 688256   # 换标的：查询词 + 备用代码
"""
import json
import re
import sys
import urllib.parse
import urllib.request

SEARCH = "https://smartbox.gtimg.cn/s3/?v=2&t=all&q={}"
KLINE = ("https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
         "?param={code},day,{start},{end},640,{adj}")

# 页面上那一对日期（自定义区间），以及今天的对照。
AS_PAGE = ("2012-06-28", "2026-06-22")
TODAY = "2026-10-17"

UA = {"User-Agent": "Mozilla/5.0"}


def get(url, encoding):
    req = urllib.request.Request(url, headers=UA)

    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode(encoding, "replace")


def unescape(body):
    return re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), body)


def search(query):
    """和 `StockDirectory.SearchAsync` 同一条路：GBK 解码 + \\uXXXX 反转义。"""
    raw = get(SEARCH.format(urllib.parse.quote(query)), "gbk")

    open_at, close_at = raw.find('"'), raw.rfind('"')
    body = unescape(raw[open_at + 1:close_at]) if 0 <= open_at < close_at else ""

    out = []

    for item in body.split("^"):
        f = item.split("~")

        if len(f) >= 5 and f[1] and f[2]:
            out.append((f[0] + f[1], f[2], f[4] if len(f) > 4 else ""))

    return out


def node_of(code, start, end, adj="hfq"):
    raw = get(KLINE.format(code=code, start=start, end=end, adj=adj), "utf-8")
    doc = json.loads(raw)

    for _key, node in (doc.get("data") or {}).items():
        if isinstance(node, dict):
            return node

    return {}


def rows_of(node):
    """`hfqday` → `qfqday` → `day`，和应用的分发顺序一致。"""
    return next((node[b] for b in ("hfqday", "qfqday", "day") if node.get(b)), [])


def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "宇树科技"
    fallback = sys.argv[2] if len(sys.argv) > 2 else "688836"

    print("=" * 74)
    print(f"1) 搜索「{query}」")
    print("=" * 74)
    hits = search(query)

    for code, name, kind in hits[:10]:
        print(f"  {code:<14} {name:<16} {kind}")

    if not hits:
        print(f"  源端没有命中 —— 用备用代码 {fallback}")

    code = hits[0][0] if hits else fallback

    print()
    print("=" * 74)
    print(f"2) {code} 全史（源端自己怎么说）")
    print("=" * 74)
    node = node_of(code, "2000-01-01", "2099-12-31")

    for key in ("fsStartDate", "attribute", "prec"):
        if key in node:
            print(f"  {key} = {node[key]}")

    all_rows = rows_of(node)
    print(f"  可用 block = {[b for b in ('hfqday', 'qfqday', 'day') if node.get(b)] or '（无）'}")

    if all_rows:
        print(f"  全史 {len(all_rows)} 根（单页上限 640，更早的要往回翻页）")
        print(f"  首根 = {all_rows[0][0]}  收 {all_rows[0][2]}")
        print(f"  末根 = {all_rows[-1][0]}  收 {all_rows[-1][2]}")
    else:
        print("  一个 K 线 block 都没有 —— 代码不对，或这根本不是股票")

    print()
    print("=" * 74)
    print("3) 结束日期往后挪一格，根数什么时候从 0 变成非 0")
    print("=" * 74)

    for end in (AS_PAGE[1], "2026-08-18", "2026-08-19", TODAY):
        rows = rows_of(node_of(code, AS_PAGE[0], end))
        note = f"  ({rows[0][0]} … {rows[-1][0]})" if rows else "   ← 空窗口"
        print(f"  {AS_PAGE[0]} → {end}: {len(rows):>4} 根{note}")

    print()
    print("=" * 74)
    print("4) 页面那个区间里，另外几只筹码有多少根（用来判『是不是只有它被勾上』）")
    print("=" * 74)

    if all_rows and all_rows[0][0] > AS_PAGE[1]:
        print(f"  注意：{code} 首根 {all_rows[0][0]} 已经晚于区间结束日 {AS_PAGE[1]}，"
              f"区间内必然 0 根。")
        print("  此时若页面只勾了这一只，全被跳过 → 报 "
              "'None of the instruments has a price inside the range.'")
        print("  若还勾了别的有数据的，则不会报错，只在状态条里点名跳过它。")
        print()

    for other in ("黄金ETF", "创业板指"):
        for other_code, other_name, _kind in search(other)[:2]:
            rows = rows_of(node_of(other_code, *AS_PAGE))

            if rows:
                print(f"  {other_code:<10} {other_name:<12} 区间内 {len(rows):>4} 根"
                      f"  ({rows[0][0]} … {rows[-1][0]})")
            else:
                print(f"  {other_code:<10} {other_name:<12} 区间内 0 根")


if __name__ == "__main__":
    main()
