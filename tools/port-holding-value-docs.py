# -*- coding: utf-8 -*-
r"""给 14 份手册的「实时持仓收益」一章补一条：画面上那行「持仓市值」是这一刻的。

2026-10-23。那条线原先印的是**收盘**那个数，一整天不动；而且它左边那个百分比本来就在
算画面这一分钟。改成按分钟重算之后，买入让它在成交那一分钟跳上去、卖出让它落下来 ——
这是画面上看得见的变化，手册要说出来，否则「市值一直没动」会被当成正确。

插在「持仓列表跟着画面走」那条之后：两条说的是同一件事的两个面（列表与页眉都跟着画面走）。
幂等：新句子已经在文件里就跳过。帮助手册 LF 无 BOM，照原样写回。
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import listingtext as lt  # noqa: E402

CHAPTER = lt.chapter_of("NavPortfolioPnl")

LINE = {
    "zh-Hans": "- **画面上那行「持仓市值」是这一刻的。** 它跟着画面一分钟一分钟地重算 —— 价格在动，手里的股数也在动：上午买进的那一笔让它在那一分钟跳上去，卖出让它落下来。收尾四张卡片里那张仍是收盘那一刻的数，与结尾帧的这一行是同一个数。",
    "zh-Hant": "- **畫面上那行「持倉市值」是這一刻的。** 它跟著畫面一分鐘一分鐘地重算 —— 價格在動，手上的股數也在動：上午買進的那一筆讓它在那一分鐘跳上去，賣出讓它落下來。收尾四張卡片裡那張仍是收盤那一刻的數，與結尾幀的這一行是同一個數。",
    "en-US": "- **The position-value line on the frame is this minute's.** It is recomputed minute by minute as the picture advances — the prices move and so does the share count: a morning purchase lifts it on the minute it filled, a sale drops it. The four closing cards still report the close, which is the number this line has landed on by the last frame.",
    "ja": "- **画面の「保有評価額」はその時点の額です。** 再生に合わせて一分ごとに計算し直します。価格が動き、株数も動くからです —— 午前に買った分はその約定の分に跳ね上がり、売れば下がります。締めの四枚のカードは大引け時点の額で、最後のフレームではこの行と同じ数になります。",
    "ko": "- **화면의 '보유 평가액'은 그 분의 값이다.** 재생에 맞춰 1분마다 다시 계산한다. 가격이 움직이고 주식 수도 움직이기 때문이다 — 오전에 산 물량은 체결된 그 분에 올라가고, 팔면 내려간다. 마무리 네 장의 카드는 종가 시점의 값이며, 마지막 프레임에서는 이 줄과 같은 숫자다.",
    "de": "- **Die Zeile „Positionswert“ auf dem Bild gilt für diese Minute.** Sie wird mit dem Bild Minute für Minute neu gerechnet — die Kurse bewegen sich und die Stückzahl mit ihnen: Ein Kauf am Morgen hebt sie in der Minute seiner Ausführung, ein Verkauf senkt sie. Die vier Schlusskarten nennen weiterhin den Stand zum Schluss, und darauf läuft diese Zeile im letzten Bild zu.",
    "fr": "- **La ligne « valeur des positions » est celle de cette minute.** Elle est recalculée minute par minute avec l'image — les cours bougent et les titres aussi : un achat du matin la fait monter à la minute de son exécution, une vente la fait baisser. Les quatre cartes de clôture donnent toujours la clôture, et c'est le chiffre sur lequel cette ligne arrive à la dernière image.",
    "it": "- **La riga «valore posizioni» è quella di questo minuto.** Viene ricalcolata minuto per minuto insieme all'immagine — i prezzi si muovono e con loro le azioni: un acquisto del mattino la alza al minuto dell'esecuzione, una vendita la abbassa. Le quattro schede di chiusura riportano sempre la chiusura, ed è il numero su cui questa riga arriva all'ultimo fotogramma.",
    "es": "- **La línea «valor de la posición» es la de este minuto.** Se recalcula minuto a minuto con la imagen: los precios se mueven y las acciones también, así que una compra de la mañana la sube en el minuto de su ejecución y una venta la baja. Las cuatro tarjetas de cierre siguen dando el cierre, que es la cifra a la que llega esta línea en el último fotograma.",
    "pt-BR": "- **A linha «valor da posição» é a deste minuto.** Ela é recalculada minuto a minuto junto com a imagem — os preços mudam e as ações também: uma compra pela manhã a sobe no minuto da execução, uma venda a derruba. Os quatro cartões de fechamento continuam mostrando o fechamento, que é o número em que esta linha chega no último quadro.",
    "pl": "- **Wiersz „wartość pozycji” to wartość z tej minuty.** Jest przeliczany minuta po minucie wraz z obrazem — ceny się ruszają, a liczba akcji razem z nimi: poranny zakup podnosi go w minucie realizacji, sprzedaż obniża. Cztery karty na koniec nadal podają zamknięcie i na tej liczbie wiersz zatrzymuje się w ostatniej klatce.",
    "cs": "- **Řádek „hodnota pozic” je hodnota této minuty.** Přepočítává se minutu po minutě spolu s obrazem — ceny se hýbou a s nimi i počet akcií: ranní nákup ho zvedne v minutě provedení, prodej sníží. Čtyři závěrečné karty dál ukazují závěr a na tom čísle tento řádek v posledním snímku skončí.",
    "ru": "- **Строка «стоимость позиций» — это стоимость на данную минуту.** Она пересчитывается минута за минутой вместе с картинкой: цены меняются, и число акций тоже — утренняя покупка поднимает её в минуту исполнения, продажа опускает. Четыре итоговые карточки по-прежнему показывают закрытие, и на этом числе строка останавливается в последнем кадре.",
    "tr": "- **Karedeki «pozisyon değeri» satırı o dakikanın değeridir.** Görüntüyle birlikte dakika dakika yeniden hesaplanır — fiyatlar değişir, adet de onlarla birlikte: sabah alınan pay, işlemin gerçekleştiği dakikada satırı yukarı çeker, satış aşağı indirir. Kapanıştaki dört kart yine kapanışı verir ve satır son karede o sayıya varır.",
}

ANCHOR = {
    "zh-Hans": "- **持仓列表跟着画面走。**",
    "zh-Hant": "- **持倉列表跟著畫面走。**",
    "en-US": "- **The holdings list moves with the picture.**",
    "ja": "- **保有銘柄の一覧は画面に合わせて動く。**",
    "ko": "- **보유 목록은 화면을 따라 움직인다.**",
    "de": "- **Die Liste der Bestände bewegt sich mit dem Bild.**",
    "fr": "- **La liste des lignes suit l'image.**",
    "it": "- **L'elenco delle posizioni segue l'immagine.**",
    "es": "- **La lista de posiciones sigue a la imagen.**",
    "pt-BR": "- **A lista de posições acompanha a imagem.**",
    "pl": "- **Lista pozycji podąża za obrazem.**",
    "cs": "- **Seznam pozic jde s obrazem.**",
    "ru": "- **Список позиций движется вместе с картинкой.**",
    "tr": "- **Pozisyon listesi görüntüyle birlikte hareket eder.**",
}


def main():
    for tag in lt.LANGS:
        path = lt.HELP / f"help-{tag}.md"

        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        body = raw.decode("utf-8-sig")

        crlf = "\r\n" in body
        if crlf:
            body = body.replace("\r\n", "\n")

        lines = body.split("\n")
        heads = [i for i, line in enumerate(lines) if line.startswith("## ")]
        start = heads[CHAPTER]
        end = heads[CHAPTER + 1] if CHAPTER + 1 < len(heads) else len(lines)

        if any(line.strip() == LINE[tag] for line in lines[start:end]):
            print(f"{tag:9} already there")
            continue

        at = next((i for i in range(start, end) if lines[i].startswith(ANCHOR[tag])), None)

        assert at is not None, f"{tag}: 找不到「列表跟着画面走」那条"

        block = ["", LINE[tag]] if lines[at + 1].strip() == "" else [LINE[tag]]
        lines[at + 1:at + 1] = block

        rebuilt = "\n".join(lines)

        if crlf:
            rebuilt = rebuilt.replace("\n", "\r\n")

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + rebuilt.encode("utf-8"))

        print(f"{tag:9} +1")


if __name__ == "__main__":
    main()
