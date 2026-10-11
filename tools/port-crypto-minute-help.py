# -*- coding: utf-8 -*-
r"""在手册加密 K 线那一章，**周期**那条之后补一条讲分钟档 —— 14 份。

**为什么要补。** 那一章现在只说「周期（日、周、月）」。周期下拉已经有六档了，少掉的三档
恰好是最需要解释的三档：它们问的是「哪一天」而不是一段区间，界面会因此换掉一个控件，
而且往回能选多少天每档都不一样（1 分钟 8 天、5/15 分钟 60 天）。这些不说，读者选了
1 分钟却只能选最近八天，会当成坏了。

**插在「周期」那条之后而不是另起一段**：两条说的是同一件事的两半 —— 周期决定画哪条序列，
而分钟档的周期问的是另一个问题（一天，不是一段）。放在一起，改周期会换控件这件事才
连得起来。

**幂等靠整条精确匹配**：这条是我们插的、文本固定，第二次运行时原样命中就跳过。股票 K 线
章里也有讲 1/5/15 分钟的那条，措辞不同，不会被认成同一条。

**位置按章内偏移找**（章标题 +5），不按标题文本找：14 份标题是各语言自己写的，唯一相同
的是顺序 —— 这也是 `port-crypto-help.py` 用序号插章的原因。跑之前会断言那一行确实是一条
`- ` 开头的项目符号，防止某份文件多一个空行而插错地方。

BOM **照抄原文**（这 14 份实测**不带** BOM）。

用法：python tools\port-crypto-minute-help.py
"""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "src" / "MarketMotionStudio" / "Assets" / "Help"

# 复用插章脚本里那三章的原文，只为拿到「加密 K 线」这一章在各语言的标题行。
_spec = importlib.util.spec_from_file_location("port_crypto_help", HERE / "port-crypto-help.py")
_helper = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_helper)

TAGS = _helper.TAGS


def candle_chapter(tag: str) -> str:
    """加密 K 线那一章的标题行 —— 三章里最先出现的那一章。"""
    for line in _helper.SECTIONS[tag].split("\n"):
        if line.startswith("## "):
            return line.strip()

    raise AssertionError(f"{tag}: the crypto candle chapter has no heading")


# 每份一条，插在「周期」那条之后。措辞跟着各语言已有的说法走。
BULLET = {
    "en-US":
        "- **1, 5 and 15 minutes** are asked for a day rather than for a span: choosing one "
        "of them swaps the span list for a date picker. The one-minute grain reaches back "
        "eight days, the other two sixty, and no further — that is how much the source "
        "keeps, not a limit this app chose. A coin trades through every hour of the day, so "
        "one day is already upwards of a thousand candles.",

    "de":
        "- **1, 5 und 15 Minuten** werden nach einem Tag gefragt, nicht nach einer Spanne: Wer "
        "eine davon wählt, bekommt statt der Spanne eine Datumsauswahl. Die Ein-Minuten-Auflösung "
        "reicht acht Tage zurück, die beiden anderen sechzig, und nicht weiter — so viel hält die "
        "Quelle, nicht so viel diese Anwendung erlaubt. Ein Coin handelt rund um die Uhr, also ist "
        "ein einziger Tag schon über tausend Kerzen.",

    "es":
        "- **1, 5 y 15 minutos** se piden por un día, no por un intervalo: al elegir uno de ellos, "
        "la lista de intervalos se cambia por un selector de fecha. El grano de un minuto llega "
        "ocho días atrás, los otros dos sesenta, y no más — es lo que guarda la fuente, no un "
        "límite que ponga esta aplicación. Un coin cotiza las veinticuatro horas, así que un solo "
        "día ya son más de mil velas.",

    "fr":
        "- **1, 5 et 15 minutes** se demandent pour un jour et non pour une période : en choisir une "
        "remplace la liste des périodes par un sélecteur de date. Le grain d'une minute remonte à "
        "huit jours, les deux autres à soixante, et pas au-delà — c'est ce que la source conserve, "
        "ce n'est pas une limite posée par cette application. Une cryptomonnaie se négocie à toute "
        "heure, donc une seule journée fait déjà plus de mille chandeliers.",

    "it":
        "- **1, 5 e 15 minuti** si chiedono per un giorno, non per un intervallo: sceglierne uno "
        "sostituisce l'elenco degli intervalli con un selettore di data. Il dettaglio da un minuto "
        "arriva a otto giorni indietro, gli altri due a sessanta, e non oltre — è quanto conserva la "
        "fonte, non un limite scelto da questa applicazione. Una crypto tratta a ogni ora del "
        "giorno, quindi un solo giorno è già più di mille candele.",

    "pl":
        "- **1, 5 i 15 minut** pyta o dzień, nie o zakres: wybranie jednej z nich zamienia listę "
        "zakresów na wybór daty. Ziarno jednominutowe sięga osiem dni wstecz, dwa pozostałe "
        "sześćdziesiąt, i ani dnia dalej — tyle trzyma źródło, to nie limit narzucony przez tę "
        "aplikację. Coin handluje przez całą dobę, więc jeden dzień to już ponad tysiąc świec.",

    "pt-BR":
        "- **1, 5 e 15 minutos** são pedidos por um dia, não por um intervalo: escolher um deles "
        "troca a lista de intervalos por um seletor de data. O grão de um minuto alcança oito dias, "
        "os outros dois sessenta, e não mais — é o quanto a fonte guarda, não um limite que este "
        "aplicativo imponha. Uma cripto negocia a todas as horas, então um único dia já passa de "
        "mil candles.",

    "cs":
        "- **1, 5 a 15 minut** se ptá na den, ne na rozsah: zvolením jedné z nich se seznam rozsahů "
        "vymění za výběr data. Zrnitost jedné minuty sahá osm dní zpět, zbylé dvě šedesát, a dál ne — "
        "tolik zdroj drží, není to limit, který by si určila tato aplikace. Coin se obchoduje "
        "čtyřiadvacet hodin denně, takže jeden den je už přes tisíc svíček.",

    "tr":
        "- **1, 5 ve 15 dakika** bir aralık değil bir gün ister: bunlardan biri seçildiğinde aralık "
        "listesinin yerini tarih seçici alır. Bir dakikalık çözünürlük sekiz gün, diğer ikisi "
        "altmış gün geriye gider, daha gerisi yok — bu, kaynağın tuttuğu kadardır, uygulamanın "
        "koyduğu bir sınır değil. Bir coin günün her saatinde işlem görür, bu yüzden tek bir gün "
        "bile bini aşkın mumdur.",

    "ru":
        "- **1, 5 и 15 минут** запрашиваются за день, а не за период: при выборе одного из них "
        "список периодов меняется на выбор даты. Минутный шаг доступен на восемь дней назад, два "
        "остальных — на шестьдесят, и не дальше: столько хранит источник, это не предел, "
        "установленный приложением. Монета торгуется круглые сутки, поэтому один день — это уже "
        "больше тысячи свечей.",

    "ja":
        "- **1・5・15 分**は期間ではなく**一日**を指定します。いずれかを選ぶと、期間のリストが日付選択に "
        "切り替わります。1 分足は 8 日前まで、5 分足と 15 分足は 60 日前までで、それより先にはありません "
        "—— これはソースが保持している範囲であって、このアプリが決めた制限ではありません。暗号資産は "
        "一日中取引されるため、一日だけでも千本以上のローソク足になります。",

    "ko":
        "- **1·5·15분**은 기간이 아니라 **하루**를 지정합니다. 이 중 하나를 고르면 기간 목록이 날짜 "
        "선택으로 바뀝니다. 1분은 8일 전까지, 5분과 15분은 60일 전까지이고 그보다 앞은 없습니다 — 그것은 "
        "소스가 보관하는 범위이며 이 앱이 정한 제한이 아닙니다. 암호화폐는 하루 종일 거래되므로 하루만 "
        "해도 천 개가 넘는 캔들이 됩니다.",

    "zh-Hans":
        "- **1、5、15 分钟**问的是「哪一天」而不是一段区间：选了其中一个，下面的区间下拉会换成日期选择框。"
        "1 分钟能往回选 8 天，5 分钟与 15 分钟 60 天，再往前就没有了 —— 这是数据源保留的范围，不是本应用"
        "自己设的限制。币种一天二十四小时都在交易，所以光一天就已经是一千多根 K 线。",

    "zh-Hant":
        "- **1、5、15 分鐘**問的是「哪一天」而不是一段區間：選了其中一個，下面的區間下拉會換成日期選擇框。"
        "1 分鐘能往回選 8 天，5 分鐘與 15 分鐘 60 天，再往前就沒有了 —— 這是資料源保留的範圍，不是本應用"
        "自己設的限制。幣種一天二十四小時都在交易，所以光一天就已經是一千多根 K 線。",
}


def main() -> int:
    for tag in TAGS:
        path = ROOT / f"help-{tag}.md"

        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig")

        bullet = BULLET[tag]

        if bullet in text:
            print(f"{tag}: already there")
            continue

        lines = text.split("\n")
        eol = "\r" if lines and lines[0].endswith("\r") else ""

        title = candle_chapter(tag)

        at = next((i for i, line in enumerate(lines) if line.strip() == title), None)
        assert at is not None, f"{tag}: the crypto candle chapter is not in the file"

        # 章标题 → 空行 → 导语 → 空行 → 第 1 条 → 第 2 条（周期）。14 份同结构，逐份核对过。
        period = at + 5

        assert 0 <= period < len(lines), f"{tag}: offset {period} is outside the file"
        assert lines[period].lstrip().startswith("- "), \
            f"{tag}: line {period + 1} is not a bullet — {lines[period][:60]!r}"

        lines.insert(period + 1, bullet + eol)

        out = "\n".join(lines)

        path.write_bytes(out.encode("utf-8-sig") if had_bom else out.encode("utf-8"))

        print(f"{tag}: inserted after line {period + 1}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
