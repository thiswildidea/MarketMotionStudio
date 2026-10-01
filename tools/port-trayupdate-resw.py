# -*- coding: utf-8 -*-
"""Adds the two tray update keys to all fourteen Resources.resw files.

Idempotent: a file that already holds the keys is left alone, so the script can be
run again after a merge without duplicating entries.

The files are UTF-8 with a BOM and LF endings. Reading and writing them as text
normalises the endings and drops the BOM, which shows up in git as the whole file
being rewritten, so both are handled byte-wise.

Values are taken from the sister project AgolAdminKit, which shipped this same tray
item first; translating them again would give fourteen more chances to drift.
"""

import pathlib
import sys

ROOT = pathlib.Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

# tag -> (TrayUpdateTo, TrayUpToDate)
VALUES = {
    "cs":      ("Aktualizovat na {0}", "Máte nejnovější verzi ({0})."),
    "de":      ("Auf {0} aktualisieren", "Sie haben die neueste Version ({0})."),
    "en-US":   ("Update to {0}", "You have the latest version ({0})."),
    "es":      ("Actualizar a {0}", "Tiene la versión más reciente ({0})."),
    "fr":      ("Mettre à jour vers {0}", "Vous disposez de la dernière version ({0})."),
    "it":      ("Aggiorna a {0}", "Hai la versione più recente ({0})."),
    "ja":      ("{0} に更新", "最新バージョン ({0}) を使用しています。"),
    "ko":      ("{0}(으)로 업데이트", "최신 버전({0})을 사용하고 있습니다."),
    "pl":      ("Aktualizuj do {0}", "Masz najnowszą wersję ({0})."),
    "pt-BR":   ("Atualizar para {0}", "Você tem a versão mais recente ({0})."),
    "ru":      ("Обновить до {0}", "У вас последняя версия ({0})."),
    "tr":      ("{0} sürümüne güncelle", "En son sürümü kullanıyorsunuz ({0})."),
    "zh-Hans": ("更新到 {0}", "已是最新版本（{0}）。"),
    "zh-Hant": ("更新至 {0}", "已是最新版本（{0}）。"),
}

# Inserted after the tray's own key block, wherever that block sits in the file —
# the fourteen files share one key order, so the anchor is the last tray key.
ANCHOR = '"TrayBusy"'


def main() -> int:
    changed = 0

    for tag, (to, up_to_date) in sorted(VALUES.items()):
        path = ROOT / tag / "Resources.resw"
        raw = path.read_bytes()
        had_bom = raw[:3] == b"\xef\xbb\xbf"
        text = raw.decode("utf-8-sig")

        if '"TrayUpdateTo"' in text or '"TrayUpToDate"' in text:
            print(f"{tag:<8} 已存在，跳过")
            continue

        lines = text.split("\n")
        index = next((i for i, line in enumerate(lines) if ANCHOR in line), None)
        if index is None:
            print(f"{tag:<8} 找不到锚点 {ANCHOR}", file=sys.stderr)
            return 1

        added = [
            f'  <data name="TrayUpdateTo"><value>{to}</value></data>',
            f'  <data name="TrayUpToDate"><value>{up_to_date}</value></data>',
        ]
        lines[index + 1:index + 1] = added

        out = "\n".join(lines)
        if had_bom:
            out = "\ufeff" + out
        path.write_bytes(out.encode("utf-8"))
        changed += 1
        print(f"{tag:<8} 已加入 2 键（{path.stat().st_size} 字节）")

    print(f"\n改动文件数：{changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
