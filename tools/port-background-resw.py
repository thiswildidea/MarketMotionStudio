# -*- coding: utf-8 -*-
"""把 AgolAdminKit 的背景图片 resw 键(10 个)移植到本项目 14 份 resw。

译文直接取自 AgolAdminKit 的同名键(同为 14 语言)，字节级插入(保 BOM 保行尾)，
统一插在 </root> 前，各语言顺序一致。可重复运行(已存在则跳过)。
"""
import xml.etree.ElementTree as ET
import glob
import os

SRC = r"D:/software/AgolAdminKit/src/AgolAdminKit/Strings"
DST = r"D:/software/MarketMotionStudio/src/MarketMotionStudio/Strings"

# 键名按此顺序写入，所有语言必须一致
KEYS = [
    "SettingsBackgroundLabel.Text",
    "SettingsBackgroundNote.Text",
    "SettingsBackgroundPick.Text",
    "SettingsBackgroundClear.Content",
    "SettingsBackgroundDimLabel.Text",
    "SettingsBackgroundForget",
    "SettingsBackgroundThumb",
    "SettingsBackgroundWindowsThumb",
    "SettingsBackgroundGalleryNote.Text",
    "SettingsBackgroundFailed",
]


def load(root_dir, tag):
    tree = ET.parse(os.path.join(root_dir, tag, "Resources.resw"))
    return {e.get("name"): (e.find("value").text or "") for e in tree.getroot().findall("data")}


def main():
    languages = sorted(os.listdir(DST))
    assert len(languages) == 14, languages

    for tag in languages:
        src = load(SRC, tag)
        dst_path = os.path.join(DST, tag, "Resources.resw")

        with open(dst_path, "rb") as f:
            text = f.read().decode("utf-8-sig")

        missing = [k for k in KEYS if k not in src]
        assert not missing, f"{tag} 源缺键: {missing}"
        already = [k for k in KEYS if f'name="{k}"' in text]
        if already:
            print(f"{tag}: 已存在 {already}，跳过")
            continue

        lines = "".join(
            '  <data name="{}" xml:space="preserve"><value>{}</value></data>\n'.format(
                k, src[k].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            )
            for k in KEYS
        )

        end = text.rindex("</root>")
        # 找到 </root> 前最后一个换行(最后一行 data 的行尾)
        nl = text.rindex("\n", 0, end)
        text = text[: nl + 1] + lines + text[nl + 1 :]

        with open(dst_path, "wb") as f:
            f.write(b"\xef\xbb\xbf" + text.encode("utf-8"))

        print(f"{tag}: +{len(KEYS)} 键")

    # 键序一致性校验
    import hashlib

    sigs = set()
    for tag in languages:
        root = ET.parse(os.path.join(DST, tag, "Resources.resw")).getroot()
        names = [e.get("name") for e in root.findall("data")]
        sigs.add(hashlib.md5("|".join(names).encode()).hexdigest())
    print("键序哈希一致:" , len(sigs) == 1, sigs)


if __name__ == "__main__":
    main()
