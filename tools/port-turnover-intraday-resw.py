# -*- coding: utf-8 -*-
r"""把「成交额页加自选 + 日内分时」要用的 resw 键注入 14 份 Resources.resw。

两件事共一批键：

* **自选篮** —— 成交额页原先只有八个板块（都是指数合成出来的），现在多了「我的清单」这一项，
  指数和个股可以混装。篮子的求和口径和板块不同（缺那一天记 0，见 `BasketTurnover`），
  所以 `TurnoverScopeWatchlist` 的文案只说「我的清单」，不说是怎么算的。
* **日内分时** —— 一个新视图：一个交易日从开盘到收盘的累计成交额。源端是 `day/query` 的
  第 4 个字段（累计成交额，元），截到 15:00；只保留最近 5 个交易日，所以这个视图**没有
  区间选择**。

单位（亿元 / 100M CNY）一律走已有的 `TurnoverUnit`，不新造一个词：这三处（画面单位行、
日内状态行、日线状态行）必须是同一个词，三种译法是三种出错的机会。

resw 是 UTF-8 **带 BOM** + LF。删键按「基础名 + 可选后缀」匹配——文件里两种条目格式并存，
写成 `">` 结尾会漏掉带 `xml:space="preserve"` 的那一种（PRI278 的根因）。

幂等：先删同名键再追加，跑几遍结果一样。

用法：python tools\port-turnover-intraday-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# 每条文案写满 14 列，列序与 LANGS 完全一致：
# en-US, de, es, fr, it, pl, pt-BR, cs, tr, ru, ja, ko, zh-Hant, zh-Hans

PAGE = [
    # ---- 自选：Scope 下拉的最后一项 -------------------------------------------------
    ("TurnoverScopeWatchlist", [
        "My list", "Eigene Liste", "Mi lista", "Ma liste", "La mia lista", "Moja lista",
        "Minha lista", "Můj seznam", "Listem", "Мой список", "マイリスト", "내 목록",
        "自選清單", "自选清单"]),

    # 空篮子时说的。清单是共享的，可能在这页之外的另一页被清空，所以这句要写得
    # 让人知道去哪儿补。
    ("TurnoverBasketEmpty", [
        "Add at least one instrument to your list first.",
        "Fügen Sie zuerst mindestens ein Instrument zu Ihrer Liste hinzu.",
        "Añada primero al menos un instrumento a su lista.",
        "Ajoutez d'abord au moins un instrument à votre liste.",
        "Aggiunga prima almeno uno strumento alla sua lista.",
        "Dodaj najpierw co najmniej jeden instrument do swojej listy.",
        "Adicione primeiro pelo menos um instrumento à sua lista.",
        "Nejprve přidejte alespoň jeden nástroj do svého seznamu.",
        "Önce listenize en az bir enstrüman ekleyin.",
        "Сначала добавьте в список хотя бы один инструмент.",
        "まずリストに銘柄を 1 件以上追加してください。",
        "먼저 목록에 종목을 하나 이상 추가하세요.",
        "請先在清單中加入至少一檔標的。",
        "请先在清单中加入至少一只标的。"]),

    # 清单是跨市场的，而成交额是各市场各报各的币种 —— 混着加就是把港元加进人民币。
    # 所以非 A 股的被挡在篮子外，而且**要说出来**：悄悄少几只，画面照样漂亮，只有合计数是错的。
    ("TurnoverBasketSkipped", [
        "{0} on your list are not A-shares and were left out — turnover is reported in each "
        "market's own currency.",

        "{0} Ihrer Liste sind keine A-Aktien und wurden weggelassen — der Umsatz wird in der "
        "jeweiligen Währung des Marktes gemeldet.",

        "{0} de su lista no son acciones A y se omitieron — la contratación se publica en la "
        "moneda de cada mercado.",

        "{0} de votre liste ne sont pas des actions A et ont été ignorées — les transactions "
        "sont publiées dans la devise de chaque marché.",

        "{0} della lista non sono azioni A e sono stati esclusi — gli scambi sono espressi "
        "nella valuta di ogni mercato.",

        "{0} z listy to nie są akcje A i zostały pominięte — obroty są podawane w walucie "
        "każdego rynku.",

        "{0} da lista não são ações A e ficaram de fora — o giro é informado na moeda de "
        "cada mercado.",

        "{0} ze seznamu nejsou akcie A a byly vynechány — obrat je uváděn v měně každého trhu.",

        "Listenizdeki {0} kalem A hissesi değil ve dahil edilmedi — işlem hacmi her piyasanın "
        "kendi para biriminde bildirilir.",

        "{0} в списке — не акции A, они пропущены: оборот указывается в валюте каждого рынка.",

        "リストの {0} 件は A 株ではないため除外しました。売買代金は各市場の通貨で"
        "報告されます。",

        "목록의 {0}개는 A주가 아니라 제외했습니다. 거래대금은 각 시장의 통화로 보고됩니다.",

        "清單裡有 {0} 檔不是 A 股，已略過——成交額是各市場各報各的幣別。",

        "清单里有 {0} 只不是 A 股，已略过——成交额是各市场各报各的币种。"]),

    # 表头上接在数字后面的：「5 只自选」。
    ("TurnoverBasketLabel", [
        "of my own", "aus eigener Liste", "de mi lista", "de ma liste", "dalla mia lista",
        "z mojej listy", "da minha lista", "z mého seznamu", "listemdeki",
        "из моего списка", "マイリストの", "내 목록의", "自選", "自选"]),

    # ---- 自选：挑哪几只进合计 ------------------------------------------------------
    # 选择器下面那行说明。这一页是唯一把自选加成一个数的榜，而清单常常是给排名榜建的
    # （十几只是常态）—— 十几只加在一起，是一个谁的账也不是的数。
    ("TurnoverPickNote.Text", [
        "Click a name to include it in the total or leave it out.",
        "Klicken Sie auf einen Namen, um ihn in die Summe aufzunehmen oder herauszulassen.",
        "Haga clic en un nombre para incluirlo en el total o dejarlo fuera.",
        "Cliquez sur un nom pour l'inclure dans le total ou l'en retirer.",
        "Faccia clic su un nome per includerlo nel totale o escluderlo.",
        "Kliknij nazwę, aby dodać ją do sumy lub pominąć.",
        "Clique em um nome para incluí-lo no total ou deixá-lo de fora.",
        "Kliknutím na název jej přidáte do součtu, nebo jej vynecháte.",
        "Bir adı toplama eklemek veya dışarıda bırakmak için üzerine tıklayın.",
        "Нажмите на название, чтобы включить его в сумму или исключить.",
        "名前をクリックすると合計に含めたり外したりできます。",
        "이름을 클릭하면 합계에 넣거나 뺄 수 있습니다.",
        "點一下名稱，把它加進或移出合計。",
        "点一下名称，把它加进或移出合计。"]),

    # 一只都没勾时说的。和「清单是空的」是两回事：那个要往里加标的，这个只要点回来。
    ("TurnoverPickNone", [
        "No instrument is switched on. Click a name to add it to the total.",
        "Kein Instrument ist eingeschaltet. Klicken Sie auf einen Namen, um ihn zur Summe "
        "hinzuzufügen.",
        "Ningún instrumento está activado. Haga clic en un nombre para añadirlo al total.",
        "Aucun instrument n'est activé. Cliquez sur un nom pour l'ajouter au total.",
        "Nessuno strumento è attivo. Faccia clic su un nome per aggiungerlo al totale.",
        "Żaden instrument nie jest włączony. Kliknij nazwę, aby dodać ją do sumy.",
        "Nenhum instrumento está ativado. Clique em um nome para adicioná-lo ao total.",
        "Není zapnut žádný nástroj. Kliknutím na název jej přidáte do součtu.",
        "Hiçbir enstrüman açık değil. Toplama eklemek için bir adı tıklayın.",
        "Ни один инструмент не включён. Нажмите на название, чтобы добавить его в сумму.",
        "どの銘柄も選ばれていません。名前をクリックすると合計に加えられます。",
        "선택된 종목이 없습니다. 이름을 클릭하면 합계에 넣을 수 있습니다.",
        "沒有勾選任何標的。點一下名稱，把它加進合計。",
        "没有勾选任何标的。点一下名称，把它加进合计。"]),

    # ---- 日内：View 下拉的第三项 ----------------------------------------------------
    ("TurnoverViewIntraday", [
        "Intraday", "Intraday", "Intradía", "Séance", "Intraday", "W ciągu dnia",
        "Intradiário", "V průběhu dne", "Gün içi", "Внутри дня", "日中", "장중",
        "日內", "日内"]),

    # ---- 日内：画面上的字 ----------------------------------------------------------
    # 默认标题（没填自定义标题时画面顶部那行）。
    ("TurnoverIntradayStageTitle", [
        "Turnover by minute", "Umsatz Minute für Minute", "Contratación por minuto",
        "Transactions minute par minute", "Scambi minuto per minuto",
        "Obroty minuta po minucie", "Giro minuto a minuto", "Obrat po minutách",
        "Dakika dakika işlem hacmi", "Оборот по минутам", "分足売買代金",
        "분별 거래대금", "當日成交額", "当日成交额"]),

    # 副标题：{0}=标的名，{1}=单位（TurnoverUnit）。与日线那句同构。
    ("TurnoverIntradaySubtitle", [
        "{0} · unit: {1}", "{0} · Einheit: {1}", "{0} · unidad: {1}", "{0} · unité : {1}",
        "{0} · unità: {1}", "{0} · jednostka: {1}", "{0} · unidade: {1}",
        "{0} · jednotka: {1}", "{0} · birim: {1}", "{0} · единица: {1}",
        "{0} · 単位: {1}", "{0} · 단위: {1}", "{0} · 單位：{1}", "{0} · 单位：{1}"]),

    # 表头那一行：{0}=日期，{1}=分钟数（这个数字会被高亮，所以整句是一个串）。
    ("TurnoverIntradayLine", [
        "{0} · {1} minutes", "{0} · {1} Minuten", "{0} · {1} minutos", "{0} · {1} minutes",
        "{0} · {1} minuti", "{0} · {1} minut", "{0} · {1} minutos", "{0} · {1} minut",
        "{0} · {1} dakika", "{0} · {1} мин", "{0} · {1} 分", "{0} · {1}분",
        "{0} · {1} 分鐘", "{0} · {1} 分钟"]),

    # 午休那条竖线上的小字。
    ("TurnoverIntradayNoon", [
        "Lunch", "Mittagspause", "Descanso", "Pause déjeuner", "Pausa", "Przerwa",
        "Intervalo", "Polední přestávka", "Öğle arası", "Обед", "昼休み", "점심시간",
        "午休", "午休"]),

    # ---- 日内：四张结算卡 ----------------------------------------------------------
    # 后三张是占全天的百分比（画面上是 xx.x%），因为这一页问的是「钱什么时候动的」，
    # 四张卡都写金额就等于把同一个总数说四遍。
    ("TurnoverIntradayStatTotal", [
        "Day total", "Tagessumme", "Total del día", "Total du jour", "Totale giornata",
        "Suma dnia", "Total do dia", "Celkem za den", "Gün toplamı", "Итого за день",
        "1 日の合計", "하루 합계", "全天成交", "全天成交"]),

    ("TurnoverIntradayStatMorning", [
        "Before lunch", "Vormittag", "Mañana", "Matinée", "Mattina", "Przed południem",
        "Antes do intervalo", "Dopoledne", "Öğle öncesi", "До обеда", "前場", "오전",
        "上午", "上午"]),

    ("TurnoverIntradayStatAfternoon", [
        "After lunch", "Nachmittag", "Tarde", "Après-midi", "Pomeriggio", "Po południu",
        "Após o intervalo", "Odpoledne", "Öğle sonrası", "После обеда", "後場", "오후",
        "下午", "下午"]),

    ("TurnoverIntradayStatClose", [
        "Last 30 min", "Letzte 30 Min.", "Últimos 30 min", "30 dernières min",
        "Ultimi 30 min", "Ostatnie 30 min", "Últimos 30 min", "Posledních 30 min",
        "Son 30 dk", "Последние 30 мин", "終盤 30 分", "마지막 30분",
        "尾盤 30 分", "尾盘 30 分"]),

    # ---- 日内：状态行与拒因 --------------------------------------------------------
    # {0}=代码，进度。
    ("TurnoverIntradayFetching", [
        "Fetching {0} minute by minute…", "Rufe {0} Minute für Minute ab…",
        "Obteniendo {0} minuto a minuto…", "Récupération de {0} minute par minute…",
        "Recupero di {0} minuto per minuto…", "Pobieram {0} minuta po minucie…",
        "Obtendo {0} minuto a minuto…", "Načítám {0} po minutách…",
        "{0} dakika dakika alınıyor…", "Получаю {0} по минутам…",
        "{0} を分足で取得中…", "{0} 분별 데이터를 가져오는 중…",
        "正在取 {0} 的分時資料…", "正在取 {0} 的分时数据…"]),

    # {0}=名字，{1}=日期，{2}=分钟数，{3}=合计，{4}=单位。
    ("TurnoverIntradayFetched", [
        "{0} on {1} · {2} minutes · {3} {4} by the close",
        "{0} am {1} · {2} Minuten · {3} {4} zum Schlusskurs",
        "{0} el {1} · {2} minutos · {3} {4} al cierre",
        "{0} le {1} · {2} minutes · {3} {4} à la clôture",
        "{0} il {1} · {2} minuti · {3} {4} alla chiusura",
        "{0} {1} · {2} minut · {3} {4} na zamknięciu",
        "{0} em {1} · {2} minutos · {3} {4} no fechamento",
        "{0} {1} · {2} minut · {3} {4} na závěr",
        "{0} · {1} · {2} dakika · kapanışta {3} {4}",
        "{0} {1} · {2} мин · {3} {4} на закрытии",
        "{0} {1} · {2} 分 · 大引け {3} {4}",
        "{0} {1} · {2}분 · 종가 기준 {3} {4}",
        "{0} · {1} · {2} 分鐘 · 收盤 {3} {4}",
        "{0} · {1} · {2} 分钟 · 收盘 {3} {4}"]),

    # 三种拒因分开说：它们的差别决定了这一行以后会不会自己变好。
    # None —— 源端根本没有它的分时数据。
    ("TurnoverIntradayNone", [
        "The source has no minute data for {0}.",
        "Die Quelle hat keine Minutendaten für {0}.",
        "La fuente no tiene datos por minuto de {0}.",
        "La source n'a pas de données par minute pour {0}.",
        "La fonte non ha dati minuto per minuto per {0}.",
        "Źródło nie ma danych minutowych dla {0}.",
        "A fonte não tem dados por minuto de {0}.",
        "Zdroj nemá minutová data pro {0}.",
        "Kaynakta {0} için dakika verisi yok.",
        "У источника нет минутных данных по {0}.",
        "ソースに {0} の分足データはありません。",
        "소스에 {0}의 분별 데이터가 없습니다.",
        "來源沒有 {0} 的分時資料。", "来源没有 {0} 的分时数据。"]),

    # NoAmount —— 有分时但那一行没有成交额列（实测只有北证 50 bj899050）。
    # 必须说清「不是 0」：把它当 0 加进去，是把一个数钱的单位加进一笔钱里。
    ("TurnoverIntradayNoAmount", [
        "{0} reports minutes but no turnover column, so it cannot be added to an amount — "
        "this is not a zero.",
        "{0} meldet Minuten, aber keine Umsatzspalte, und kann daher keinem Betrag "
        "hinzugefügt werden — das ist keine Null.",
        "{0} informa minutos pero ninguna columna de contratación, así que no puede "
        "sumarse a un importe — esto no es un cero.",
        "{0} indique des minutes mais aucune colonne de transactions ; impossible de "
        "l'ajouter à un montant — ce n'est pas un zéro.",
        "{0} riporta minuti ma nessuna colonna di scambi, quindi non può essere sommato "
        "a un importo — non è uno zero.",
        "{0} podaje minuty, ale nie ma kolumny obrotu, więc nie można dodać tego do kwoty "
        "— to nie jest zero.",
        "{0} informa minutos, mas nenhuma coluna de giro, então não pode ser somado a um "
        "valor — isso não é zero.",
        "{0} uvádí minuty, ale žádný sloupec obratu, nelze jej tedy přičíst k částce "
        "— to není nula.",
        "{0} dakika verisi veriyor ama işlem hacmi sütunu yok, bu yüzden bir tutara "
        "eklenemez — bu sıfır değildir.",
        "{0} выдаёт минуты, но нет колонки оборота, поэтому его нельзя прибавить к сумме "
        "— это не ноль.",
        "{0} は分足を返しますが売買代金の列がないため、金額に加算できません。"
        "ゼロではありません。",
        "{0}는 분별 데이터는 있지만 거래대금 열이 없어 금액에 더할 수 없습니다. "
        "0이 아닙니다.",
        "{0} 有分時資料但沒有成交額欄，不能加進金額——這不是 0。",
        "{0} 有分时数据但没有成交额栏，不能加进金额——这不是 0。"]),

    # TooFew —— 只有开盘那几分钟（当天的交易日还没走完）。
    ("TurnoverIntradayTooFew", [
        "{0} has too few minutes to be a session — the day may still be in progress.",
        "{0} hat zu wenige Minuten für einen Handelstag — der Tag läuft vielleicht noch.",
        "{0} tiene demasiados pocos minutos para ser una sesión — el día puede seguir en curso.",
        "{0} n'a pas assez de minutes pour être une séance — la journée est peut-être en cours.",
        "{0} ha troppo pochi minuti per essere una seduta — la giornata potrebbe essere "
        "ancora in corso.",
        "{0} ma za mało minut, by być sesją — dzień może jeszcze trwać.",
        "{0} tem poucos minutos para ser um pregão — o dia pode estar em andamento.",
        "{0} má příliš málo minut na celý den — den možná ještě neskončil.",
        "{0} bir seans için çok az dakika içeriyor — gün henüz bitmemiş olabilir.",
        "{0} слишком мало минут для сессии — возможно, день ещё идёт.",
        "{0} は 1 日分として分が少なすぎます。取引時間中の可能性があります。",
        "{0}는 하루치로 보기엔 분이 너무 적습니다. 장이 진행 중일 수 있습니다.",
        "{0} 的分鐘太少，不足以構成一個交易日——當天可能還在進行中。",
        "{0} 的分钟太少，不足以构成一个交易日——当天可能还在进行中。"]),
]


def entry(key, value):
    """One <data> line, escaped.

    A bare `&` is not legal XML, and MakePri reports it as `PRI224: root node not found`,
    naming the root element rather than the value that broke it.
    """
    safe = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return f'  <data name="{key}"><value>{safe}</value></data>\n'


def main():
    for tag in LANGS:
        path = ROOT / tag / "Resources.resw"

        text = path.read_bytes().decode("utf-8-sig")

        if not text.endswith("\n"):
            text += "\n"

        at = LANGS.index(tag)
        lines = []

        for key, values in PAGE:
            assert len(values) == len(LANGS), f"{key}: {len(values)} values"
            lines.append(entry(key, values[at]))

        # Idempotent: drop a key of the same name wherever it already sits, then append.
        # `[^>]*` after the name because this file holds two entry shapes — the single-line
        # `<data name="K">` a machine wrote and the hand-edited
        # `<data name="K" xml:space="preserve">` — and a pattern that insists on `">` matches
        # only the first, which is how a file once ended up holding both `K` and `K.Text`
        # (PRI278: key defined as both a resource and a scope).
        for key, _ in PAGE:
            base = key.split(".")[0]

            text = re.sub(
                rf'  <data name="{re.escape(base)}(\.\w+)?"[^>]*>.*?</data>\n',
                "", text, flags=re.S)

        at_root = text.rfind("</root>")
        assert at_root > 0, f"{tag}: no </root>"

        text = text[:at_root] + "".join(lines) + text[at_root:]

        # Bytes, not text: read_text/write_text would normalise the line endings and git
        # would see the whole file rewritten. utf-8-sig because a resw without its BOM is
        # read as UTF-16 by MakePri.
        path.write_bytes(text.encode("utf-8-sig"))

        print(f"{tag}: +{len(lines)} keys")


if __name__ == "__main__":
    main()
