#!/usr/bin/env python3
"""Adds the board page's strings to all fourteen resource files.

The new 持仓·大盘 双屏 page (`Pages/BoardPage.xaml`) reads twenty-one keys; zh-Hans was
written by hand when the page was built, and this script ports the other thirteen. The
Chinese is the source of truth; each language below is a translation of it, not a new
text.

Idempotent: a file that already carries `NavBoard.Content` is left alone. resw keeps its
BOM and LF endings.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
STRINGS = ROOT / "src" / "MarketMotionStudio" / "Strings"

ZH = {
    "NavBoard.Content": "持仓·大盘 双屏",
    "BoardPageTitle.Text": "持仓·大盘 双屏",
    "BoardPageSubtitle.Text": "上半是持仓的当日盈亏，下半是 A 股与港股指数的实时走势：两边各占一半，共用一根时钟。",
    "BoardTitle": "持仓·大盘",
    "BoardSectionIndex.Text": "指数（A 股 / 港股）",
    "BoardSectionMainland.Text": "A 股指数 · 15:00 收盘",
    "BoardSectionKong.Text": "港股指数 · 16:00 收盘",
    "BoardSectionBook.Text": "持仓（在「实时持仓收益」里编辑）",
    "BoardAutoRefresh.Header": "开盘时自动刷新",
    "BoardNote.Text": "数据是最近一个交易日的分钟行情；收盘后重取即可得到当日全貌。",
    "BoardFetched": "取到 {0} / {1} 个指数 · {2} 分钟 · 组合 {3}",
    "BoardNeedIndex": "至少选一个指数，下半屏才有东西可画。",
    "BoardFetchFailed": "取数失败，稍后再试；已经画出的画面仍然可用。",
    "BoardPnlLabel": "持仓当日盈亏",
    "BoardPnlStatLine": "组合 {0} · 持仓 {1} 只",
    "BoardContribBest": "贡献最大 {0} {1}",
    "BoardContribWorst": "拖累最大 {0} {1}",
    "BoardIndexLabel": "指数走势 · 涨跌幅",
    "BoardNoIndex": "未选指数",
    "BoardNoon": "午间休市",
    "BoardMainlandClose": "A 股收盘 15:00",
}

T = {}

T["en-US"] = {
    "NavBoard.Content": "Book & Board Split",
    "BoardPageTitle.Text": "Book & Board Split",
    "BoardPageSubtitle.Text": "The book's day above, mainland and Hong Kong indexes below: half the frame each, on one clock.",
    "BoardTitle": "Book & Board",
    "BoardSectionIndex.Text": "Indexes (mainland / Hong Kong)",
    "BoardSectionMainland.Text": "Mainland indexes · close 15:00",
    "BoardSectionKong.Text": "Hong Kong indexes · close 16:00",
    "BoardSectionBook.Text": "The book (edited on Intraday P&L)",
    "BoardAutoRefresh.Header": "Refresh while the market is open",
    "BoardNote.Text": "The data is the latest trading day, minute by minute; one fetch after the close is the whole day.",
    "BoardFetched": "{0} of {1} indexes · {2} minutes · book {3}",
    "BoardNeedIndex": "Pick at least one index — the lower half has nothing to draw otherwise.",
    "BoardFetchFailed": "The fetch failed; try again later. What is already drawn stays.",
    "BoardPnlLabel": "The book's day",
    "BoardPnlStatLine": "Book {0} · {1} positions",
    "BoardContribBest": "Best: {0} {1}",
    "BoardContribWorst": "Worst: {0} {1}",
    "BoardIndexLabel": "Indexes · change from yesterday's close",
    "BoardNoIndex": "No index selected",
    "BoardNoon": "Lunch break",
    "BoardMainlandClose": "Mainland close 15:00",
}

T["zh-Hant"] = {
    "NavBoard.Content": "持倉·大盤 雙屏",
    "BoardPageTitle.Text": "持倉·大盤 雙屏",
    "BoardPageSubtitle.Text": "上半是持倉的當日盈虧，下半是 A 股與港股指數的即時走勢：兩邊各佔一半，共用一根時鐘。",
    "BoardTitle": "持倉·大盤",
    "BoardSectionIndex.Text": "指數（A 股 / 港股）",
    "BoardSectionMainland.Text": "A 股指數 · 15:00 收盤",
    "BoardSectionKong.Text": "港股指數 · 16:00 收盤",
    "BoardSectionBook.Text": "持倉（在「即時持倉收益」裡編輯）",
    "BoardAutoRefresh.Header": "開盤時自動重新整理",
    "BoardNote.Text": "資料是最近一個交易日的分鐘行情；收盤後重取即可得到當日全貌。",
    "BoardFetched": "取到 {0} / {1} 個指數 · {2} 分鐘 · 組合 {3}",
    "BoardNeedIndex": "至少選一個指數，下半屏才有東西可畫。",
    "BoardFetchFailed": "取數失敗，稍後再試；已經畫出的畫面仍然可用。",
    "BoardPnlLabel": "持倉當日盈虧",
    "BoardPnlStatLine": "組合 {0} · 持倉 {1} 隻",
    "BoardContribBest": "貢獻最大 {0} {1}",
    "BoardContribWorst": "拖累最大 {0} {1}",
    "BoardIndexLabel": "指數走勢 · 漲跌幅",
    "BoardNoIndex": "未選指數",
    "BoardNoon": "午間休市",
    "BoardMainlandClose": "A 股收盤 15:00",
}

T["ja"] = {
    "NavBoard.Content": "資産と市場の分割表示",
    "BoardPageTitle.Text": "資産と市場の分割表示",
    "BoardPageSubtitle.Text": "上に保有資産の当日損益、下に A 股と香港指数のリアルタイム推移：半分ずつ、一つの時計で。",
    "BoardTitle": "資産と市場",
    "BoardSectionIndex.Text": "指数（A 股 / 香港株）",
    "BoardSectionMainland.Text": "A 股指数 · 15:00 終了",
    "BoardSectionKong.Text": "香港指数 · 16:00 終了",
    "BoardSectionBook.Text": "保有資産（編集は「リアルタイム損益」で）",
    "BoardAutoRefresh.Header": "取引時間中は自動更新",
    "BoardNote.Text": "データは直近取引日の分足です。終了後に取り直せば一日分がそろいます。",
    "BoardFetched": "指数 {0} / {1} · {2} 分 · 資産 {3}",
    "BoardNeedIndex": "指数を一つ以上選んでください。下半分に描くものがなくなります。",
    "BoardFetchFailed": "取得に失敗しました。すでに描かれた画面はそのまま使えます。",
    "BoardPnlLabel": "保有資産の当日損益",
    "BoardPnlStatLine": "資産 {0} · 保有 {1} 銘柄",
    "BoardContribBest": "最大の功労者 {0} {1}",
    "BoardContribWorst": "最大の足かせ {0} {1}",
    "BoardIndexLabel": "指数の推移 · 前日終値比",
    "BoardNoIndex": "指数未選択",
    "BoardNoon": "昼間休場",
    "BoardMainlandClose": "A 股終了 15:00",
}

T["ko"] = {
    "NavBoard.Content": "계좌·시장 분할",
    "BoardPageTitle.Text": "계좌·시장 분할",
    "BoardPageSubtitle.Text": "위쪽 절반은 보유 계좌의 당일 손익, 아래쪽 절반은 A주와 홍콩 지수의 실시간 흐름: 하나의 시계로 함께 흘러갑니다.",
    "BoardTitle": "계좌·시장",
    "BoardSectionIndex.Text": "지수 (A주 / 홍콩)",
    "BoardSectionMainland.Text": "A주 지수 · 15:00 마감",
    "BoardSectionKong.Text": "홍콩 지수 · 16:00 마감",
    "BoardSectionBook.Text": "보유 계좌 (편집은 「실시간 수익」에서)",
    "BoardAutoRefresh.Header": "장중 자동 새로 고침",
    "BoardNote.Text": "데이터는 최근 거래일의 분별 시세입니다. 마감 후 다시 가져오면 하루 전체가 됩니다.",
    "BoardFetched": "지수 {0} / {1} · {2}분 · 계좌 {3}",
    "BoardNeedIndex": "지수를 하나 이상 선택하세요. 아래쪽에 그릴 것이 없어집니다.",
    "BoardFetchFailed": "가져오기에 실패했습니다. 이미 그려진 화면은 그대로입니다.",
    "BoardPnlLabel": "계좌 당일 손익",
    "BoardPnlStatLine": "계좌 {0} · 보유 {1}종목",
    "BoardContribBest": "최고 기여 {0} {1}",
    "BoardContribWorst": "최대 발목 {0} {1}",
    "BoardIndexLabel": "지수 흐름 · 전일 종가 대비",
    "BoardNoIndex": "선택된 지수 없음",
    "BoardNoon": "점심 휴장",
    "BoardMainlandClose": "A주 마감 15:00",
}

T["de"] = {
    "NavBoard.Content": "Depot & Markt geteilt",
    "BoardPageTitle.Text": "Depot & Markt geteilt",
    "BoardPageSubtitle.Text": "Oben der Tag des Depots, unten die Festland- und Hongkong-Indizes: je die halbe Bildhöhe, eine Uhr für beide.",
    "BoardTitle": "Depot & Markt",
    "BoardSectionIndex.Text": "Indizes (Festland / Hongkong)",
    "BoardSectionMainland.Text": "Festland-Indizes · Schluss 15:00",
    "BoardSectionKong.Text": "Hongkong-Indizes · Schluss 16:00",
    "BoardSectionBook.Text": "Depot (bearbeitet unter »Intraday-Gewinn«)",
    "BoardAutoRefresh.Header": "Während der Handelszeit aktualisieren",
    "BoardNote.Text": "Die Daten sind die Minutenkurse des letzten Handelstags; ein Abruf nach Schluss ergibt den ganzen Tag.",
    "BoardFetched": "{0} von {1} Indizes · {2} Minuten · Depot {3}",
    "BoardNeedIndex": "Wähle mindestens einen Index — sonst hat die untere Hälfte nichts zu zeichnen.",
    "BoardFetchFailed": "Der Abruf ist fehlgeschlagen; versuche es später erneut. Gezeichnetes bleibt stehen.",
    "BoardPnlLabel": "Der Tag des Depots",
    "BoardPnlStatLine": "Depot {0} · {1} Positionen",
    "BoardContribBest": "Bester Beitrag: {0} {1}",
    "BoardContribWorst": "Schlechtester: {0} {1}",
    "BoardIndexLabel": "Indizes · Veränderung zum Vortagsschluss",
    "BoardNoIndex": "Kein Index gewählt",
    "BoardNoon": "Mittagspause",
    "BoardMainlandClose": "Festland-Schluss 15:00",
}

T["fr"] = {
    "NavBoard.Content": "Portefeuille & marché partagés",
    "BoardPageTitle.Text": "Portefeuille & marché partagés",
    "BoardPageSubtitle.Text": "En haut la journée du portefeuille, en bas les indices de Chine continentale et de Hong Kong : une moitié chacun, une seule horloge.",
    "BoardTitle": "Portefeuille & marché",
    "BoardSectionIndex.Text": "Indices (continent / Hong Kong)",
    "BoardSectionMainland.Text": "Indices du continent · clôture 15:00",
    "BoardSectionKong.Text": "Indices de Hong Kong · clôture 16:00",
    "BoardSectionBook.Text": "Le portefeuille (à modifier dans « P&L intraday »)",
    "BoardAutoRefresh.Header": "Actualiser pendant la séance",
    "BoardNote.Text": "Les données sont les minutes du dernier jour de bourse ; un fetch après la clôture donne la journée entière.",
    "BoardFetched": "{0} sur {1} indices · {2} minutes · portefeuille {3}",
    "BoardNeedIndex": "Choisis au moins un indice — sinon la moitié basse n'a rien à dessiner.",
    "BoardFetchFailed": "Le fetch a échoué ; réessaie plus tard. Ce qui est déjà dessiné reste.",
    "BoardPnlLabel": "La journée du portefeuille",
    "BoardPnlStatLine": "Portefeuille {0} · {1} positions",
    "BoardContribBest": "Meilleure contribution : {0} {1}",
    "BoardContribWorst": "Pire contribution : {0} {1}",
    "BoardIndexLabel": "Indices · variation depuis la clôture d'hier",
    "BoardNoIndex": "Aucun indice choisi",
    "BoardNoon": "Pause déjeuner",
    "BoardMainlandClose": "Clôture continentale 15:00",
}

T["es"] = {
    "NavBoard.Content": "Cartera y mercado, divididos",
    "BoardPageTitle.Text": "Cartera y mercado, divididos",
    "BoardPageSubtitle.Text": "Arriba el día de la cartera, abajo los índices de China continental y Hong Kong: media pantalla cada uno, un solo reloj.",
    "BoardTitle": "Cartera y mercado",
    "BoardSectionIndex.Text": "Índices (continental / Hong Kong)",
    "BoardSectionMainland.Text": "Índices continentales · cierre 15:00",
    "BoardSectionKong.Text": "Índices de Hong Kong · cierre 16:00",
    "BoardSectionBook.Text": "La cartera (se edita en «P&L intradía»)",
    "BoardAutoRefresh.Header": "Actualizar durante la sesión",
    "BoardNote.Text": "Los datos son los minutos del último día de bolsa; una lectura tras el cierre da el día completo.",
    "BoardFetched": "{0} de {1} índices · {2} minutos · cartera {3}",
    "BoardNeedIndex": "Elige al menos un índice; si no, la mitad inferior no tiene nada que dibujar.",
    "BoardFetchFailed": "La lectura falló; inténtalo más tarde. Lo ya dibujado permanece.",
    "BoardPnlLabel": "El día de la cartera",
    "BoardPnlStatLine": "Cartera {0} · {1} posiciones",
    "BoardContribBest": "Mejor aporte: {0} {1}",
    "BoardContribWorst": "Peor aporte: {0} {1}",
    "BoardIndexLabel": "Índices · variación desde el cierre de ayer",
    "BoardNoIndex": "Ningún índice elegido",
    "BoardNoon": "Pausa del mediodía",
    "BoardMainlandClose": "Cierre continental 15:00",
}

T["it"] = {
    "NavBoard.Content": "Portafoglio e mercato divisi",
    "BoardPageTitle.Text": "Portafoglio e mercato divisi",
    "BoardPageSubtitle.Text": "Sopra la giornata del portafoglio, sotto gli indici della Cina continentale e di Hong Kong: metà schermo ciascuno, un solo orologio.",
    "BoardTitle": "Portafoglio e mercato",
    "BoardSectionIndex.Text": "Indici (continentale / Hong Kong)",
    "BoardSectionMainland.Text": "Indici continentali · chiusura 15:00",
    "BoardSectionKong.Text": "Indici di Hong Kong · chiusura 16:00",
    "BoardSectionBook.Text": "Il portafoglio (si modifica in «P&L intraday»)",
    "BoardAutoRefresh.Header": "Aggiorna durante la seduta",
    "BoardNote.Text": "I dati sono i minuti dell'ultima giornata di borsa; un prelievo dopo la chiusura dà la giornata intera.",
    "BoardFetched": "{0} di {1} indici · {2} minuti · portafoglio {3}",
    "BoardNeedIndex": "Scegli almeno un indice: altrimenti la metà inferiore non ha nulla da disegnare.",
    "BoardFetchFailed": "Il prelievo è fallito; riprova più tardi. Ciò che è già disegnato resta.",
    "BoardPnlLabel": "La giornata del portafoglio",
    "BoardPnlStatLine": "Portafoglio {0} · {1} posizioni",
    "BoardContribBest": "Migliore contributo: {0} {1}",
    "BoardContribWorst": "Peggiore: {0} {1}",
    "BoardIndexLabel": "Indici · variazione dalla chiusura di ieri",
    "BoardNoIndex": "Nessun indice scelto",
    "BoardNoon": "Pausa pranzo",
    "BoardMainlandClose": "Chiusura continentale 15:00",
}

T["pt-BR"] = {
    "NavBoard.Content": "Carteira e mercado divididos",
    "BoardPageTitle.Text": "Carteira e mercado divididos",
    "BoardPageSubtitle.Text": "Em cima o dia da carteira, em baixo os índices da China continental e de Hong Kong: meia tela para cada, um só relógio.",
    "BoardTitle": "Carteira e mercado",
    "BoardSectionIndex.Text": "Índices (continental / Hong Kong)",
    "BoardSectionMainland.Text": "Índices do continente · fechamento 15:00",
    "BoardSectionKong.Text": "Índices de Hong Kong · fechamento 16:00",
    "BoardSectionBook.Text": "A carteira (editada em «P&L intradiário»)",
    "BoardAutoRefresh.Header": "Atualizar durante o pregão",
    "BoardNote.Text": "Os dados são os minutos do último dia de pregão; uma leitura após o fechamento dá o dia inteiro.",
    "BoardFetched": "{0} de {1} índices · {2} minutos · carteira {3}",
    "BoardNeedIndex": "Escolha pelo menos um índice; senão a metade de baixo não tem nada a desenhar.",
    "BoardFetchFailed": "A leitura falhou; tente mais tarde. O que já está desenhado permanece.",
    "BoardPnlLabel": "O dia da carteira",
    "BoardPnlStatLine": "Carteira {0} · {1} posições",
    "BoardContribBest": "Melhor contribuição: {0} {1}",
    "BoardContribWorst": "Pior contribuição: {0} {1}",
    "BoardIndexLabel": "Índices · variação desde o fechamento de ontem",
    "BoardNoIndex": "Nenhum índice escolhido",
    "BoardNoon": "Pausa do almoço",
    "BoardMainlandClose": "Fechamento do continente 15:00",
}

T["ru"] = {
    "NavBoard.Content": "Портфель и рынок, пополам",
    "BoardPageTitle.Text": "Портфель и рынок, пополам",
    "BoardPageSubtitle.Text": "Сверху день портфеля, снизу индексы материка и Гонконга: по половине кадра, на одних часах.",
    "BoardTitle": "Портфель и рынок",
    "BoardSectionIndex.Text": "Индексы (материк / Гонконг)",
    "BoardSectionMainland.Text": "Индексы материка · закрытие 15:00",
    "BoardSectionKong.Text": "Индексы Гонконга · закрытие 16:00",
    "BoardSectionBook.Text": "Портфель (правится на странице «Интрадей П&У»)",
    "BoardAutoRefresh.Header": "Обновлять во время торгов",
    "BoardNote.Text": "Данные — поминутные котировки последнего торгового дня; одно обновление после закрытия даёт весь день.",
    "BoardFetched": "{0} из {1} индексов · {2} минут · портфель {3}",
    "BoardNeedIndex": "Выберите хотя бы один индекс — иначе нижней половине нечего рисовать.",
    "BoardFetchFailed": "Загрузка не удалась; попробуйте позже. Уже нарисованное остаётся.",
    "BoardPnlLabel": "День портфеля",
    "BoardPnlStatLine": "Портфель {0} · {1} позиций",
    "BoardContribBest": "Лучший вклад: {0} {1}",
    "BoardContribWorst": "Худший: {0} {1}",
    "BoardIndexLabel": "Индексы · изменение от вчерашнего закрытия",
    "BoardNoIndex": "Индексы не выбраны",
    "BoardNoon": "Обеденный перерыв",
    "BoardMainlandClose": "Закрытие материка 15:00",
}

T["pl"] = {
    "NavBoard.Content": "Portfel i rynek, na pół",
    "BoardPageTitle.Text": "Portfel i rynek, na pół",
    "BoardPageSubtitle.Text": "U góry dzień portfela, u dołu indeksy Chin kontynentalnych i Hongkongu: po połowie kadru, na jednym zegarze.",
    "BoardTitle": "Portfel i rynek",
    "BoardSectionIndex.Text": "Indeksy (kontynent / Hongkong)",
    "BoardSectionMainland.Text": "Indeksy kontynentu · zamknięcie 15:00",
    "BoardSectionKong.Text": "Indeksy Hongkongu · zamknięcie 16:00",
    "BoardSectionBook.Text": "Portfel (edycja na stronie «P&L intraday»)",
    "BoardAutoRefresh.Header": "Odświeżaj w czasie sesji",
    "BoardNote.Text": "Dane to minuty ostatniego dnia sesji; jedno pobranie po zamknięciu daje cały dzień.",
    "BoardFetched": "{0} z {1} indeksów · {2} minut · portfel {3}",
    "BoardNeedIndex": "Wybierz przynajmniej jeden indeks — inaczej dolna połowa nie ma czego rysować.",
    "BoardFetchFailed": "Pobranie nie powiodło się; spróbuj później. To, co już narysowano, zostaje.",
    "BoardPnlLabel": "Dzień portfela",
    "BoardPnlStatLine": "Portfel {0} · {1} pozycji",
    "BoardContribBest": "Najlepszy wkład: {0} {1}",
    "BoardContribWorst": "Najgorszy: {0} {1}",
    "BoardIndexLabel": "Indeksy · zmiana od wczorajszego zamknięcia",
    "BoardNoIndex": "Nie wybrano indeksu",
    "BoardNoon": "Przerwa obiadowa",
    "BoardMainlandClose": "Zamknięcie kontynentu 15:00",
}

T["tr"] = {
    "NavBoard.Content": "Portföy ve Piyasa bölünmüş",
    "BoardPageTitle.Text": "Portföy ve Piyasa bölünmüş",
    "BoardPageSubtitle.Text": "Üstte portföyün günü, altta Çin anakarası ve Hong Kong endeksleri: yarısı yarıya, tek saat.",
    "BoardTitle": "Portföy ve Piyasa",
    "BoardSectionIndex.Text": "Endeksler (anakara / Hong Kong)",
    "BoardSectionMainland.Text": "Anakara endeksleri · kapanış 15:00",
    "BoardSectionKong.Text": "Hong Kong endeksleri · kapanış 16:00",
    "BoardSectionBook.Text": "Portföy («Gün içi kâr» sayfasında düzenlenir)",
    "BoardAutoRefresh.Header": "Piyasa açıkken yenile",
    "BoardNote.Text": "Veriler son işlem gününün dakikalarıdır; kapanıştan sonra bir çekim günün tamamını verir.",
    "BoardFetched": "{0} / {1} endeks · {2} dakika · portföy {3}",
    "BoardNeedIndex": "En az bir endeks seç — yoksa alt yarıya çizilecek bir şey yok.",
    "BoardFetchFailed": "Çekim başarısız; sonra tekrar dene. Çizilmiş olan yerinde kalır.",
    "BoardPnlLabel": "Portföyün günü",
    "BoardPnlStatLine": "Portföy {0} · {1} pozisyon",
    "BoardContribBest": "En iyi katkı: {0} {1}",
    "BoardContribWorst": "En kötü: {0} {1}",
    "BoardIndexLabel": "Endeksler · dünkü kapanışa göre değişim",
    "BoardNoIndex": "Endeks seçilmedi",
    "BoardNoon": "Öğle arası",
    "BoardMainlandClose": "Anakara kapanışı 15:00",
}

T["cs"] = {
    "NavBoard.Content": "Portfolio a trh napůl",
    "BoardPageTitle.Text": "Portfolio a trh napůl",
    "BoardPageSubtitle.Text": "Nahoře den portfolia, dole indexy pevninské Číny a Hongkongu: po polovině rámu, na jedny hodiny.",
    "BoardTitle": "Portfolio a trh",
    "BoardSectionIndex.Text": "Indexy (pevnina / Hongkong)",
    "BoardSectionMainland.Text": "Indexy pevniny · uzavření 15:00",
    "BoardSectionKong.Text": "Indexy Hongkongu · uzavření 16:00",
    "BoardSectionBook.Text": "Portfolio (upravuje se na «Intraday P&L»)",
    "BoardAutoRefresh.Header": "Aktualizovat během obchodování",
    "BoardNote.Text": "Data jsou minuty posledního obchodního dne; jedno stažení po uzavření dá celý den.",
    "BoardFetched": "{0} z {1} indexů · {2} minut · portfolio {3}",
    "BoardNeedIndex": "Vyber alespoň jeden index — jinak spodní polovina nemá co kreslit.",
    "BoardFetchFailed": "Stažení se nezdařilo; zkus to později. To, co už je nakresleno, zůstává.",
    "BoardPnlLabel": "Den portfolia",
    "BoardPnlStatLine": "Portfolio {0} · {1} pozic",
    "BoardContribBest": "Největší přínos: {0} {1}",
    "BoardContribWorst": "Největší brzda: {0} {1}",
    "BoardIndexLabel": "Indexy · změna od včerejšího uzavření",
    "BoardNoIndex": "Není vybrán index",
    "BoardNoon": "Polední přestávka",
    "BoardMainlandClose": "Uzavření pevniny 15:00",
}

def esc(value):
    """XML-escapes a value. `Book & Board` written raw is a parse error, and the
    providers of this file (plain text here, resw there) do not share a syntax."""
    return (value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


LANGS = ["cs", "de", "en-US", "es", "fr", "it", "ja", "ko", "pl", "pt-BR", "ru", "tr", "zh-Hans", "zh-Hant"]

changed = 0

for lang in LANGS:
    path = STRINGS / lang / "Resources.resw"
    raw = path.read_bytes()
    had_bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")

    if 'name="NavBoard.Content"' in text:
        print(f"{lang}: already present")
        continue

    table = T[lang]
    assert set(table) == set(ZH), lang

    block = "".join(f'  <data name="{k}"><value>{esc(v)}</value></data>\n' for k, v in table.items())

    trimmed = text.rstrip()
    assert trimmed.endswith("</root>")
    text = trimmed[: -len("</root>")].rstrip("\n") + "\n" + block + "</root>\n"

    path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + text.encode("utf-8"))
    changed += 1
    print(f"{lang}: added {len(table)} keys")

print(f"changed {changed} files")
