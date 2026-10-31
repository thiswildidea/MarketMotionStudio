"""Adds the two Stock Connect fee captions to all fourteen resource files.

Both are `NumberBox` headers, so the keys carry `.Header` — `x:Uid` looks for `<uid>.Header` and a
plain key would draw an empty label above the box (the failure mode that has bitten this project
twice: 按钮有框无字 / 标签空白).

Idempotent: an existing key is left alone, and the file's BOM and LF endings are preserved by
editing the decoded text and writing it back the same way it was read.
"""

import io
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent / "src" / "MarketMotionStudio" / "Strings"

ROWS = {
    "zh-Hans": ("港股通佣金（‱，买卖都收）", "港股通最低佣金（港元）"),
    "zh-Hant": ("港股通佣金（‱，買賣都收）", "港股通最低佣金（港元）"),
    "en-US": ("Stock Connect commission (‱, both sides)", "Stock Connect minimum commission (HK$)"),
    "ja": ("港股通の手数料（‱、売買両方）", "港股通の最低手数料（香港ドル）"),
    "ko": ("홍콩주식통 커미션(‱, 매수·매도 모두)", "홍콩주식통 최소 커미션(HK$)"),
    "de": ("Stock-Connect-Provision (‱, beide Seiten)", "Mindestprovision Stock Connect (HK$)"),
    "fr": ("commission Stock Connect (‱, les deux sens)", "commission minimale Stock Connect (HK$)"),
    "es": ("comisión Stock Connect (‱, ambos sentidos)", "comisión mínima Stock Connect (HK$)"),
    "it": ("commissione Stock Connect (‱, entrambi i lati)", "commissione minima Stock Connect (HK$)"),
    "pt-BR": ("comissão Stock Connect (‱, ambos os lados)", "comissão mínima Stock Connect (HK$)"),
    "ru": ("комиссия Stock Connect (‱, обе стороны)", "минимальная комиссия Stock Connect (HK$)"),
    "pl": ("prowizja Stock Connect (‱, obie strony)", "minimalna prowizja Stock Connect (HK$)"),
    "cs": ("provize Stock Connect (‱, obě strany)", "minimální provize Stock Connect (HK$)"),
    "tr": ("Stock Connect komisyonu (‱, iki yön)", "en düşük Stock Connect komisyonu (HK$)"),
}

ANCHOR = '  <data name="PortfolioPnlFeeTransfer.Header">'


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


changed = 0

for resw in sorted(ROOT.glob("*/Resources.resw")):
    lang = resw.parent.name

    if lang not in ROWS:
        print(f"{lang}: no row")
        continue

    raw = resw.read_bytes()
    had_bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")

    commission, minimum = ROWS[lang]
    wanted = [
        f'  <data name="PortfolioPnlFeeKongCommission.Header"><value>{esc(commission)}</value></data>',
        f'  <data name="PortfolioPnlFeeKongMinimum.Header"><value>{esc(minimum)}</value></data>',
    ]

    missing = [line for line in wanted if line.split('"')[1] not in text]

    if not missing:
        print(f"{lang}: already present")
        continue

    at = text.index(ANCHOR)
    end = text.index("\n", at) + 1
    text = text[:end] + "\n".join(missing) + "\n" + text[end:]

    resw.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + text.encode("utf-8"))
    changed += 1
    print(f"{lang}: added {len(missing)}")

print("files changed:", changed)
