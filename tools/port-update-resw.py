# -*- coding: utf-8 -*-
r"""把「商店更新按钮」的 resw 键从 AgolAdminKit 移植进本项目 14 份 Resources.resw。

两件事：
1. 就地改名 NavSettings.Content -> NavSettingsLabel.Text。
   设置项的内容从纯字符串变成了网格（标签 + 更新按钮），x:Uid 挂到
   TextBlock 上，键必须带 .Text 后缀——挂 .Content 会把整个网格替换成
   一个字符串，按钮随之消失。
2. 从 AgolAdminKit 同名键取现成译文，注入 10 个 Update*/NavUpdate* 键。

用法：python tools\port-update-resw.py    （可重复运行，先清旧键）
"""
import hashlib
import re
from pathlib import Path

SOURCE = Path(r"D:\software\AgolAdminKit\src\AgolAdminKit\Strings")
TARGET = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "ru", "tr"]

# 顺序即注入顺序：更新按钮 → 进度 → 悬停提示 → 忙碌确认 → 各种结果
KEYS = [
    "NavUpdate",
    "NavUpdating",
    "NavUpdateTip",
    "UpdateBusyTitle",
    "UpdateBusyBody",
    "UpdateBusyGo",
    "UpdateCancelled",
    "UpdateNeedsWiFi",
    "UpdateLowBattery",
    "UpdateFailed",
]


def read_values(path):
    text = path.read_bytes().decode("utf-8-sig")
    found = {}
    for key in KEYS:
        m = re.search(r'<data name="%s"[^>]*><value>(.*?)</value></data>' % re.escape(key), text, re.S)
        assert m, f"{path}: 缺键 {key}"
        found[key] = m.group(1)
    return found


def main():
    sources = {lang: read_values(SOURCE / lang / "Resources.resw") for lang in LANGS}

    for lang in LANGS:
        path = TARGET / lang / "Resources.resw"
        raw = path.read_bytes()
        text = raw.decode("utf-8-sig")

        # 1. 改名：Content 后缀 -> Text 后缀（只改键名，值不动）
        before = text
        text = text.replace('<data name="NavSettings.Content">', '<data name="NavSettingsLabel.Text">')
        assert text != before, f"{lang}: NavSettings.Content 未找到（可能已改名）"

        # 2. 清掉上一次注入的键，保证可重复运行
        for key in KEYS:
            text = re.sub(r'\n  <data name="%s"[^>]*><value>.*?</value></data>' % re.escape(key), "", text, flags=re.S)

        # 3. 注入
        block = "\n".join(f'  <data name="{key}"><value>{sources[lang][key]}</value></data>' for key in KEYS)
        assert text.count("</root>") == 1
        text = text.replace("</root>", block + "\n</root>")

        path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8") if raw.startswith(b"\xef\xbb\xbf") else text.encode("utf-8"))
        print(f"{lang}: 改名 1 键 + 注入 {len(KEYS)} 键")

    # 键序一致性校验
    digests = {}
    for lang in LANGS:
        text = (TARGET / lang / "Resources.resw").read_bytes().decode("utf-8-sig")
        order = re.findall(r'<data name="([^"]+)"', text)
        digests[lang] = hashlib.md5(",".join(order).encode()).hexdigest()
    assert len(set(digests.values())) == 1, f"键序不一致: {digests}"
    print("14 份键序一致 ✓  每份", len(order), "键")


if __name__ == "__main__":
    main()
