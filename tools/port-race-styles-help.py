#!/usr/bin/env python3
"""Adds the race pages' display-style line to all fourteen help files.

The race pages gained a display-style menu (`tools/port-race-styles.py`): the bar race and
four re-stagings of the same standings, ported from NbaMotionStudio's career race. The sector
race's help section carries the sentence; the anchor is the section's interval bullet, whole
line, the same one `port-sectorrace-help-range.py` left behind.

Idempotent: a file that already carries the bullet is left alone. No BOM (markdown here), LF
preserved.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
HELP = ROOT / "src" / "MarketMotionStudio" / "Assets" / "Help"

# The interval bullet as it stands now, per language — the anchor the new line goes after.
ANCHORS = {
    "help-cs.md": "- Období může být 1, 3, 6, 12 nebo 24 měsíců, nebo vlastní počáteční a koncové datum. "
                  "Vlastní rozsah sahá přibližně 900 dní — tolik zvládne jeden požadavek — a výběr dat tam končí.",
    "help-de.md": "- Der Zeitraum kann 1, 3, 6, 12 oder 24 Monate betragen oder frei mit Start- und Enddatum "
                  "gewählt werden. Ein eigener Zeitraum reicht etwa 900 Tage weit — so viel wie eine Anfrage — "
                  "und die Datumsauswahl endet dort.",
    "help-en-US.md": "- The interval can be 1, 3, 6, 12 or 24 months, or a custom start and end date. A custom "
                     "span reaches about 900 days — one request's worth — and the date pickers stop there.",
    "help-es.md": "- El periodo puede ser de 1, 3, 6, 12 o 24 meses, o fechas de inicio y fin personalizadas. "
                  "Un intervalo personalizado llega a unos 900 días — lo que abarca una solicitud — y los "
                  "selectores de fecha terminan ahí.",
    "help-fr.md": "- La période peut être de 1, 3, 6, 12 ou 24 mois, ou des dates de début et de fin "
                  "personnalisées. Un intervalle personnalisé remonte à environ 900 jours — la portée d'une "
                  "requête — et les sélecteurs de date s'arrêtent là.",
    "help-it.md": "- Il periodo può essere di 1, 3, 6, 12 o 24 mesi, oppure date di inizio e fine personalizzate. "
                  "Un intervallo personalizzato arriva a circa 900 giorni — quanto copre una richiesta — e i "
                  "selettori di data si fermano lì.",
    "help-ja.md": "- 期間は1、3、6、12、24ヶ月、または開始・終了日の指定が選べます。指定した期間は約900日まで "
                  "— 1回のリクエストで取れる範囲 — で、日付の選択はそこで止まります。",
    "help-ko.md": "- 구간은 1, 3, 6, 12, 24개월 또는 시작·종료일 지정이 가능합니다. 직접 지정한 기간은 약 "
                  "900일까지 — 한 번의 요청이 닿는 범위 — 이며 날짜 선택기는 거기서 멈춥니다.",
    "help-pl.md": "- Zakres to 1, 3, 6, 12 lub 24 miesiące albo dowolna data początkowa i końcowa. Własny "
                  "zakres sięga około 900 dni — tyle, ile obejmuje jedno żądanie — i tam kończą się selektory dat.",
    "help-pt-BR.md": "- O intervalo pode ser de 1, 3, 6, 12 ou 24 meses, ou datas de início e fim personalizadas. "
                     "Um intervalo personalizado alcança cerca de 900 dias — o alcance de uma solicitação — e os "
                     "seletores de data param aí.",
    "help-ru.md": "- Период — 1, 3, 6, 12 или 24 месяца либо произвольные даты начала и конца. Свой интервал "
                  "охватывает около 900 дней — столько берёт один запрос — и выбор дат на этом останавливается.",
    "help-tr.md": "- Dönem 1, 3, 6, 12 veya 24 ay ya da özel başlangıç ve bitiş tarihi olabilir. Kendi "
                  "aralığınız yaklaşık 900 güne ulaşır — bir isteğin kapsadığı kadar — ve tarih seçiciler orada durur.",
    "help-zh-Hans.md": "- 区间可选 1、3、6、12、24 个月或自定义起止日。自定义区间最长约 900 天 ——"
                       "也就是一次请求能取的量 —— 日期选择器到此为止。",
    "help-zh-Hant.md": "- 區間可選 1、3、6、12、24 個月或自訂起止日。自訂區間最長約 900 天 ——"
                       "也就是一次請求能取的量 —— 日期選擇器到此為止。",
}

BULLETS = {
    "help-cs.md": "- **Styl zobrazení** nabízí pět podob: závod pruhů, podiové sloupce, sloupce panorámy, "
                  "pyramida trůnu a skyline s fokusem. Všechny čtou stejné pořadí — přepnutí jen změní kresbu, "
                  "nic nenačítá znovu, a stránka si pamatuje poslední volbu.",
    "help-de.md": "- **Anzeigestil** hat fünf Varianten: Balkenrennen, Podestsäulen, Skyline-Säulen, "
                  "Thronpyramide und Fokus-Skyline. Alle fünf lesen dieselbe Rangliste — das Umschalten ändert "
                  "nur die Zeichnung, lädt nichts neu, und jede Seite merkt sich die letzte Wahl.",
    "help-en-US.md": "- **Display style** comes in five: bar race, podium columns, skyline columns, throne "
                     "pyramid and the focus skyline. All five read the same standings — switching redraws the "
                     "race, it never refetches, and each page remembers the last choice.",
    "help-es.md": "- **Estilo de visualización**: cinco variantes — carrera de barras, columnas de podio, "
                  "columnas horizonte, pirámide del trono y skyline con foco. Las cinco leen la misma "
                  "clasificación — cambiar solo cambia el dibujo, no vuelve a descargar nada, y cada página "
                  "recuerda la última elección.",
    "help-fr.md": "- **Style d'affichage** : cinq variantes — course à barres, colonnes podium, colonnes "
                  "skyline, pyramide du trône et skyline animée. Les cinq lisent le même classement — changer "
                  "ne fait que redessiner, ne retélécharge rien, et chaque page garde le dernier choix.",
    "help-it.md": "- **Stile di visualizzazione**: cinque varianti — gara a barre, colonne podio, colonne "
                  "skyline, piramide del trono e skyline con fuoco. Tutte e cinque leggono la stessa "
                  "classifica — il cambio ridisegna soltanto, non riscarica nulla, e ogni pagina ricorda "
                  "l'ultima scelta.",
    "help-ja.md": "- **表示スタイル**は5種類から選べます：バーレース、柱の表彰台、スカイライン柱、王座ピラミッド、"
                  "フォーカス・スカイライン。5種とも同じ順位表を読んでいるだけで、切り替えは描き方を変えるだけ。"
                  "再取得はせず、各ページは前回の選択を覚えています。",
    "help-ko.md": "- **표시 스타일**은 다섯 가지입니다: 막대 레이스, 포디움 기둥, 스카이라인 기둥, 왕좌 피라미드, "
                  "포커스 스카이라인. 다섯 가지 모두 같은 순위표를 읽으며, 전환은 그리는 방식만 바꿀 뿐 다시 "
                  "가져오지 않고 각 페이지는 마지막 선택을 기억합니다.",
    "help-pl.md": "- **Styl wykresu** ma pięć odmian: wyścig pasków, kolumny podium, kolumny panoramy, "
                  "piramida tronu i skyline z fokusem. Wszystkie czytają te same rankingi — zmiana tylko "
                  "przerysowuje, niczego nie pobiera ponownie, a strona zapamiętuje ostatni wybór.",
    "help-pt-BR.md": "- **Estilo de exibição**: cinco variantes — corrida de barras, colunas de pódio, colunas "
                     "horizonte, pirâmide do trono e skyline com foco. As cinco leem a mesma classificação — "
                     "trocar apenas redesenha, não baixa nada de novo, e cada página lembra a última escolha.",
    "help-ru.md": "- **Стиль показа** — пять вариантов: гонка полос, колонны пьедестала, колонны-небоскрёбы, "
                  "пирамида трона и небоскрёбы с фокусом. Все пять читают одну и ту же таблицу — переключение "
                  "лишь меняет рисунок, ничего не загружает заново, и страница запоминает последний выбор.",
    "help-tr.md": "- **Görüntü stili** beş çeşittir: çubuk yarışı, podyum kolonları, silüet kolonlar, taht "
                  "piramidi ve odaklı silüet. Beşi de aynı sıralamayı okur — geçiş yalnızca çizimi değiştirir, "
                  "yeniden veri almaz ve her sayfa son seçimi hatırlar.",
    "help-zh-Hans.md": "- **展示样式**可选五种：条形竞速、三柱领奖台、天际线立柱、王座金字塔、聚焦天际线。"
                       "五种读的是同一份排名——切换只是换一种画法，不重新取数，各页记住上一次的选择。",
    "help-zh-Hant.md": "- **顯示樣式**可選五種：條形競速、三柱頒獎台、天際線立柱、王座金字塔、聚焦天際線。"
                       "五種讀的是同一份排名——切換只是換一種畫法，不重新取數，各頁記住上一次的選擇。",
}


def main():
    changed, skipped, problem = [], [], []

    for name in sorted(ANCHORS):
        path = HELP / name

        if not path.exists():
            problem.append(f"{name} (missing)")
            continue

        text = path.read_text(encoding="utf-8").lstrip("\ufeff")

        if BULLETS[name] in text:
            skipped.append(name)
            continue

        anchor = ANCHORS[name]

        if text.count(anchor) != 1:
            problem.append(f"{name} ({text.count(anchor)} anchor matches)")
            continue

        text = text.replace(anchor, anchor + "\n" + BULLETS[name])

        # No BOM, LF — help files are markdown (see port-sectorrace-help-range.py).
        path.write_bytes(text.encode("utf-8"))
        changed.append(name)

    print(f"changed : {len(changed)}  {' '.join(changed)}")
    print(f"skipped : {len(skipped)}  {' '.join(skipped) or '-'}")
    print(f"problem : {len(problem)}  {' '.join(problem) or '-'}")


if __name__ == "__main__":
    main()
