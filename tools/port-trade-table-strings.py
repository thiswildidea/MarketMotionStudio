#!/usr/bin/env python3
"""Adds the filed-trades table's column headers to all fourteen resource files.

The archive is a table now: number, day, clock, direction, name, price, size. Seven headings,
all on `TextBlock`s, so every key carries `.Text`.

It also renames `PortfolioImportApply` to `PortfolioImportApply.Content`. That button used to be
the dialog's primary button, whose caption came from `Strings.Get`; it is now an ordinary button
inside the flow, so XAML looks for the suffixed key — and the two spellings cannot both exist
(same name as a resource and a scope is refused by the index, PRI278).

Idempotent: a file already carrying `TradeColumnNumber.Text` is left alone. resw keeps its BOM
and LF endings.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
STRINGS = ROOT / "src" / "MarketMotionStudio" / "Strings"

ZH = {
    "TradeColumnNumber.Text": "序号",
    "TradeColumnDay.Text": "日期",
    "TradeColumnTime.Text": "时间",
    "TradeColumnSide.Text": "方向",
    "TradeColumnName.Text": "名称",
    "TradeColumnPrice.Text": "价格",
    "TradeColumnShares.Text": "数量",
    "PortfolioImportApply.Content": "导入",
}

T = {
    "en-US": {
        "TradeColumnNumber.Text": "No.",
        "TradeColumnDay.Text": "Day",
        "TradeColumnTime.Text": "Time",
        "TradeColumnSide.Text": "Side",
        "TradeColumnName.Text": "Name",
        "TradeColumnPrice.Text": "Price",
        "TradeColumnShares.Text": "Size",
        "PortfolioImportApply.Content": "Import",
    },
    "zh-Hant": {
        "TradeColumnNumber.Text": "序號",
        "TradeColumnDay.Text": "日期",
        "TradeColumnTime.Text": "時間",
        "TradeColumnSide.Text": "方向",
        "TradeColumnName.Text": "名稱",
        "TradeColumnPrice.Text": "價格",
        "TradeColumnShares.Text": "數量",
        "PortfolioImportApply.Content": "匯入",
    },
    "cs": {
        "TradeColumnNumber.Text": "Č.",
        "TradeColumnDay.Text": "Datum",
        "TradeColumnTime.Text": "Čas",
        "TradeColumnSide.Text": "Strana",
        "TradeColumnName.Text": "Název",
        "TradeColumnPrice.Text": "Cena",
        "TradeColumnShares.Text": "Počet",
        "PortfolioImportApply.Content": "Importovat",
    },
    "de": {
        "TradeColumnNumber.Text": "Nr.",
        "TradeColumnDay.Text": "Datum",
        "TradeColumnTime.Text": "Zeit",
        "TradeColumnSide.Text": "Seite",
        "TradeColumnName.Text": "Name",
        "TradeColumnPrice.Text": "Kurs",
        "TradeColumnShares.Text": "Stück",
        "PortfolioImportApply.Content": "Importieren",
    },
    "es": {
        "TradeColumnNumber.Text": "N.º",
        "TradeColumnDay.Text": "Fecha",
        "TradeColumnTime.Text": "Hora",
        "TradeColumnSide.Text": "Lado",
        "TradeColumnName.Text": "Nombre",
        "TradeColumnPrice.Text": "Precio",
        "TradeColumnShares.Text": "Títulos",
        "PortfolioImportApply.Content": "Importar",
    },
    "fr": {
        "TradeColumnNumber.Text": "N°",
        "TradeColumnDay.Text": "Date",
        "TradeColumnTime.Text": "Heure",
        "TradeColumnSide.Text": "Sens",
        "TradeColumnName.Text": "Nom",
        "TradeColumnPrice.Text": "Prix",
        "TradeColumnShares.Text": "Quantité",
        "PortfolioImportApply.Content": "Importer",
    },
    "it": {
        "TradeColumnNumber.Text": "N.",
        "TradeColumnDay.Text": "Data",
        "TradeColumnTime.Text": "Ora",
        "TradeColumnSide.Text": "Lato",
        "TradeColumnName.Text": "Nome",
        "TradeColumnPrice.Text": "Prezzo",
        "TradeColumnShares.Text": "Quantità",
        "PortfolioImportApply.Content": "Importa",
    },
    "ja": {
        "TradeColumnNumber.Text": "番号",
        "TradeColumnDay.Text": "日付",
        "TradeColumnTime.Text": "時刻",
        "TradeColumnSide.Text": "売買",
        "TradeColumnName.Text": "銘柄",
        "TradeColumnPrice.Text": "価格",
        "TradeColumnShares.Text": "数量",
        "PortfolioImportApply.Content": "取り込む",
    },
    "ko": {
        "TradeColumnNumber.Text": "번호",
        "TradeColumnDay.Text": "날짜",
        "TradeColumnTime.Text": "시간",
        "TradeColumnSide.Text": "구분",
        "TradeColumnName.Text": "종목",
        "TradeColumnPrice.Text": "가격",
        "TradeColumnShares.Text": "수량",
        "PortfolioImportApply.Content": "가져오기",
    },
    "pl": {
        "TradeColumnNumber.Text": "Nr",
        "TradeColumnDay.Text": "Data",
        "TradeColumnTime.Text": "Czas",
        "TradeColumnSide.Text": "Strona",
        "TradeColumnName.Text": "Nazwa",
        "TradeColumnPrice.Text": "Cena",
        "TradeColumnShares.Text": "Wolumen",
        "PortfolioImportApply.Content": "Importuj",
    },
    "pt-BR": {
        "TradeColumnNumber.Text": "Nº",
        "TradeColumnDay.Text": "Data",
        "TradeColumnTime.Text": "Hora",
        "TradeColumnSide.Text": "Lado",
        "TradeColumnName.Text": "Nome",
        "TradeColumnPrice.Text": "Preço",
        "TradeColumnShares.Text": "Qtde",
        "PortfolioImportApply.Content": "Importar",
    },
    "ru": {
        "TradeColumnNumber.Text": "№",
        "TradeColumnDay.Text": "Дата",
        "TradeColumnTime.Text": "Время",
        "TradeColumnSide.Text": "Сторона",
        "TradeColumnName.Text": "Название",
        "TradeColumnPrice.Text": "Цена",
        "TradeColumnShares.Text": "Кол-во",
        "PortfolioImportApply.Content": "Импорт",
    },
    "tr": {
        "TradeColumnNumber.Text": "No",
        "TradeColumnDay.Text": "Tarih",
        "TradeColumnTime.Text": "Saat",
        "TradeColumnSide.Text": "Yön",
        "TradeColumnName.Text": "Ad",
        "TradeColumnPrice.Text": "Fiyat",
        "TradeColumnShares.Text": "Adet",
        "PortfolioImportApply.Content": "İçe aktar",
    },
}

# The unsuffixed spelling of the button key, dropped wherever a previous run left it.
LEGACY = ("PortfolioImportApply",)


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    changed = 0

    for lang, table in [("zh-Hans", ZH), *T.items()]:
        resw = STRINGS / lang / "Resources.resw"

        if not resw.exists():
            print(f"{lang}: MISSING FILE")
            continue

        raw = resw.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig")

        dropped = False

        for legacy in LEGACY:
            pattern = r'^  <data name="%s"><value>.*?</value></data>\n' % re.escape(legacy)

            if re.search(pattern, text, flags=re.M):
                text = re.sub(pattern, "", text, flags=re.M)
                dropped = True

        missing = {k: v for k, v in table.items() if f'name="{k}"' not in text}

        if not missing and not dropped:
            print(f"{lang}: already present")
            continue

        trimmed = text.rstrip()
        assert trimmed.endswith("</root>"), lang
        body = trimmed[: -len("</root>")].rstrip("\n")

        if missing:
            body += "\n" + "".join(
                f'  <data name="{k}"><value>{esc(v)}</value></data>\n' for k, v in missing.items()
            ).rstrip("\n")

        resw.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + (body + "\n</root>\n").encode("utf-8"))
        changed += 1
        print(f"{lang}: added {len(missing)} keys, dropped {len(LEGACY) if dropped else 0}")

    print(f"changed {changed} files")


if __name__ == "__main__":
    main()
