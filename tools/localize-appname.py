# -*- coding: utf-8 -*-
"""Give the shell a localizable app name (Start menu, Apps list, Settings).

Until now the package manifest carried the display name as a string literal, so
the Start menu showed "MarketMotionStudio" in every language. A manifest string
can only be localized when it is a *plain* resource identifier: `AppTitle.Text`
is a property identifier owned by x:Uid, and it cannot be reused for this (a file
may not hold both `X` and `X.Text`). So the same product name is published a
second time under `AppDisplayName`, which the manifest references as
`ms-resource:AppDisplayName`.

Run: python tools\\localize-appname.py
Idempotent — a file that already has the key is left alone.
"""
import codecs
import hashlib
import os
import re

STRINGS = r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings"
TAGS = ["cs", "de", "en-US", "es", "fr", "it", "ja", "ko", "pl", "pt-BR", "ru",
        "tr", "zh-Hans", "zh-Hant"]

# The two localised product names. Every other language ships the English one:
# that is also what an unlisted language falls back to.
EN = "Market Motion Studio"
NAMES = {"zh-Hans": "行情指标动画工作室", "zh-Hant": "行情指標動畫工作室"}

COMMENT = {
    "zh-Hans": """  <!-- 外壳显示名（开始菜单、应用列表、系统设置）。清单以 ms-resource:AppDisplayName
       读取此键，因此随系统显示语言变化；没有对应语言时回退英文。
       与 AppTitle.Text 是同一个产品名，但那个键归 x:Uid 所有，不能兼作标识符。 -->
""",
    "zh-Hant": """  <!-- 外殼顯示名稱（開始功能表、應用程式清單、系統設定）。資訊清單以
       ms-resource:AppDisplayName 讀取此鍵，因此隨系統顯示語言變化；
       沒有對應語言時回退英文。與 AppTitle.Text 是同一個產品名，
       但那個鍵歸 x:Uid 所有，不能兼作識別碼。 -->
""",
}
COMMENT_EN = """  <!-- The shell display name (Start menu, Apps list, Settings). The package
       manifest reads this key as ms-resource:AppDisplayName, so it follows the
       OS display language; a language we do not ship falls back to English.
       Same product name as AppTitle.Text, but that key belongs to x:Uid and a
       file cannot hold both "X" and "X.Text". -->
"""

KEY = "AppDisplayName"
ANCHOR = re.compile(r'^[ \t]*<data name="AppTitle\.Text"><value>(.*?)</value></data>[ \t]*$',
                    re.MULTILINE)
KEYS = re.compile(r'<data name="([^"]+)"')


def keyhash(text):
    return hashlib.md5("\n".join(KEYS.findall(text)).encode("utf-8")).hexdigest()[:12]


before, after = set(), set()
for tag in TAGS:
    path = os.path.join(STRINGS, tag, "Resources.resw")
    raw = open(path, "rb").read()
    assert raw[:3] == codecs.BOM_UTF8, f"{tag}: BOM missing, this file is UTF-8 BOM"
    assert b"\r\n" not in raw, f"{tag}: CRLF found, this file is LF"
    text = raw.decode("utf-8-sig")
    before.add(keyhash(text))

    if f'<data name="{KEY}">' in text:
        print(f"  {tag:8s} already present")
        after.add(keyhash(text))
        continue

    m = ANCHOR.search(text)
    assert m, f"{tag}: AppTitle.Text anchor not found"
    title = m.group(1)
    value = NAMES.get(tag, EN)
    assert title == value, f"{tag}: AppTitle.Text is {title!r}, expected {value!r}"

    block = COMMENT.get(tag, COMMENT_EN) + f'  <data name="{KEY}"><value>{value}</value></data>\n'
    text = text[:m.end() + 1] + block + text[m.end() + 1:]

    # utf-8 with the BOM it already had, LF — never let read_text/write_text near it
    open(path, "wb").write(codecs.BOM_UTF8 + text.encode("utf-8"))
    after.add(keyhash(text))
    print(f"  {tag:8s} +{KEY} = {value}")

assert len(before) == 1, f"key order already differed before: {before}"
assert len(after) == 1, f"key order differs after: {sorted(after)}"
print(f"\nkey-order hash: {before.pop()} -> {after.pop()} (identical in all 14 files)")
