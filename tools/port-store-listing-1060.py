# -*- coding: utf-8 -*-
"""把商店文案（docs/store-listing.md，14 语言）的「此版本的新增功能」改到 1.0.6.0。

**这一栏是「换」不是「加」，历史留在 CHANGELOG.md。** 上一版那一栏还在数「本版新增一个图表
页」——那些页在 1.0.5.0 已经上架了；接着往后加就会变成一栏自相矛盾的旧版本说明。

本版只有**一件**用户可见的事，所以只有一句话：订阅买不成的时候不再一声不响。它值得单独上
一版，是因为那条路是个**死口** —— 商店没给出加载项时 `SubscribeAsync` 连商店自己的窗都不
开，于是「按了订阅」和「没按」在画面上完全一样，而人只能把它读成「这个按钮是坏的」。

**不在这里写第十五套「十七个图表页」。** 那句话已经在说明段里长期成立，写进「新增功能」会
让人以为页面数是本版变的。末尾那句「其余照旧」说的是订阅的范围没变，不是页面数。

定位与幂等：每个语言段里第二个 `###` 小标题之后的第一段正文，整行比对。store-listing.md 是
**CRLF 无 BOM**，写完照原样写回（剥掉 `\r` 比对，否则每次都差一个 `\r`，幂等就成了空话）。

用法：python tools\\port-store-listing-1060.py      （跑第二遍应当是「改了 0 条」）
"""

import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPO = pathlib.Path(__file__).resolve().parent.parent
LISTING = REPO / "docs" / "store-listing.md"

LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "fr", "it",
         "es", "pt-BR", "pl", "cs", "ru", "tr"]

# 商店这一栏的硬上限。一句话远够不着，但每次换文案都要算一遍最长的那一种语言 —— 上限是
# 按字符算的，德/法/意语一句能顶到中文的三倍长。
LIMIT = 1500

# 本版那一句。十四种语言同一种说法：**以前是安静的，现在不是**。
NEWS = {
    "zh-Hans":
        "本版修的是订阅买不成时一声不响这个毛病：以前点「订阅」若商店那边没有可买的内容，"
        "什么都不会发生——按了和没按在画面上完全一样。现在这两种情况都会明说：商店没有可购买的内容，"
        "或者商店报告购买已完成却没有授予权限，各自弹一句说明并写清原因。其余照旧："
        "十七个图表页的取数、播放动画、保存封面图依旧免费，收费的仍然只有导出视频与去掉水印这两件。",
    "zh-Hant":
        "本版修的是訂閱買不成時一聲不響這個毛病：以前點「訂閱」若商店那邊沒有可買的內容，"
        "什麼都不會發生——按了和沒按在畫面上完全一樣。現在這兩種情況都會明說：商店沒有可購買的內容，"
        "或者商店回報購買已完成卻沒有授予權限，各自彈一句說明並寫清原因。其餘照舊："
        "十七個圖表頁的取數、播放動畫、儲存封面圖依舊免費，收費的仍然只有匯出影片與移除浮水印這兩件。",
    "en-US":
        "This version fixes one thing: a purchase that could not go through used to say nothing at "
        "all. When the Store had nothing to sell, pressing Subscribe looked exactly like never "
        "having pressed it. Now both cases speak, each in its own dialog with the reason spelled "
        "out — the Store has nothing to sell, or it reports a purchase that granted nothing. "
        "Nothing else changed: fetching data, playing the animation and saving a cover image stay "
        "free on all seventeen chart pages, and the subscription still buys only two things, "
        "exporting a video and removing the watermark.",
    "ja":
        "このバージョンで直したのは、購読が成立しなかったときに何も言わないという一点です。"
        "以前は、ストア側に購入できるものがない場合、「購読」を押しても何も起きず、押したのと"
        "押していないのとで画面上の違いがありませんでした。今はどちらの場合も伝えます。"
        "ストアに購入できるものがない場合と、購入は完了したと報告されたのに権限が付与されなかった"
        "場合で、それぞれ理由を書いたダイアログが出ます。他は変わりません。十七のチャートページでの"
        "データ取得、アニメーションの再生、表紙画像の保存は引き続き無料で、購読で買うのは"
        "動画の書き出しと透かしの削除の二つだけです。",
    "ko":
        "이 버전은 한 가지를 고쳤습니다. 구매가 이루어지지 않을 때 아무 말도 하지 않았습니다. "
        "스토어에 살 수 있는 항목이 없으면 '구독'을 눌러도 아무 일도 일어나지 않아, 누른 것과 누르지 "
        "않은 것이 화면에서 전혀 다르지 않았습니다. 이제 두 경우 모두 이유를 적은 대화 상자로 "
        "알려줍니다. 스토어에 구매할 항목이 없는 경우와, 구매가 완료되었다고 보고되었지만 권한이 "
        "부여되지 않은 경우입니다. 다른 것은 그대로입니다. 열일곱 개 차트 페이지의 데이터 가져오기, "
        "애니메이션 재생, 표지 이미지 저장은 계속 무료이며, 구독으로 살 수 있는 것은 동영상 내보내기와 "
        "워터마크 제거 두 가지뿐입니다.",
    "de":
        "Diese Version behebt eines: Ein Kauf, der nicht zustande kam, sagte bisher gar nichts. "
        "Wenn der Store nichts zu verkaufen hatte, sah „Abonnieren“ genau so aus, als hätte man es "
        "nie gedrückt. Jetzt sprechen beide Fälle, jeder in einem eigenen Dialog und mit dem Grund: "
        "Der Store hat nichts zu verkaufen, oder er meldet einen Kauf, der nichts gewährt hat. "
        "Sonst bleibt alles, wie es ist: Daten abrufen, Animation abspielen und Titelbild speichern "
        "sind auf allen siebzehn Diagrammseiten weiterhin kostenlos, und das Abonnement kauft "
        "weiterhin nur zwei Dinge — das Video exportieren und das Wasserzeichen entfernen.",
    "fr":
        "Cette version corrige une chose : un achat qui n'aboutissait pas ne disait rien du tout. "
        "Quand le Store n'avait rien à vendre, appuyer sur S'abonner était identique à ne jamais "
        "l'avoir fait. Les deux cas parlent désormais, chacun dans sa propre boîte et avec la "
        "raison : le Store n'a rien à vendre, ou il signale un achat qui n'a rien accordé. Rien "
        "d'autre ne change : récupérer les données, lire l'animation et enregistrer l'image de "
        "couverture restent gratuits sur les dix-sept pages de graphiques, et l'abonnement "
        "continue d'acheter deux choses seulement — exporter une vidéo et retirer le filigrane.",
    "it":
        "Questa versione corregge una cosa: un acquisto che non andava a buon fine non diceva "
        "proprio nulla. Quando lo Store non aveva nulla da vendere, premere Abbonati era identico "
        "a non averlo mai premuto. Ora entrambi i casi parlano, ciascuno nella propria finestra e "
        "con il motivo: lo Store non ha nulla da vendere, oppure segnala un acquisto che non ha "
        "concesso nulla. Nient'altro cambia: recuperare i dati, riprodurre l'animazione e salvare "
        "l'immagine di copertina restano gratuiti su tutte le diciassette pagine di grafici, e "
        "l'abbonamento continua a comprare solo due cose — esportare un video e rimuovere la "
        "filigrana.",
    "es":
        "Esta versión corrige una cosa: una compra que no llegaba a buen puerto no decía absolutamente "
        "nada. Cuando la Tienda no tenía nada que vender, pulsar Suscribirse era exactamente igual a "
        "no haberlo pulsado nunca. Ahora ambos casos hablan, cada uno en su propio cuadro y con el "
        "motivo: la Tienda no tiene nada que vender, o informa de una compra que no concedió nada. "
        "Nada más cambia: obtener datos, reproducir la animación y guardar la imagen de portada siguen "
        "siendo gratis en las diecisiete páginas de gráficos, y la suscripción sigue comprando solo "
        "dos cosas — exportar un vídeo y quitar la marca de agua.",
    "pt-BR":
        "Esta versão corrige uma coisa: uma compra que não se concretizava não dizia absolutamente "
        "nada. Quando a Loja não tinha nada à venda, pressionar Assinar era exatamente igual a nunca "
        "ter pressionado. Agora os dois casos falam, cada um na sua própria caixa e com o motivo: a "
        "Loja não tem nada à venda, ou informa uma compra que não concedeu nada. Nada mais muda: "
        "buscar dados, reproduzir a animação e salvar a imagem de capa continuam gratuitos nas "
        "dezessete páginas de gráficos, e a assinatura continua comprando apenas duas coisas — "
        "exportar um vídeo e remover a marca d'água.",
    "pl":
        "Ta wersja naprawia jedną rzecz: zakup, który nie dochodził do skutku, nie mówił zupełnie "
        "nic. Gdy Sklep nie miał nic do sprzedania, naciśnięcie Subskrybuj wyglądało dokładnie tak, "
        "jakby się go nigdy nie nacisnęło. Teraz oba przypadki mówią, każdy we własnym oknie i z "
        "podaniem powodu: Sklep nie ma nic do sprzedania albo zgłasza zakup, który niczego nie "
        "przyznał. Poza tym bez zmian: pobieranie danych, odtwarzanie animacji i zapisywanie obrazu "
        "okładki pozostają bezpłatne na wszystkich siedemnastu stronach wykresów, a subskrypcja "
        "nadal kupuje tylko dwie rzeczy — eksport wideo i usunięcie znaku wodnego.",
    "cs":
        "Tato verze opravuje jednu věc: nákup, který neprošel, neříkal vůbec nic. Když Obchod neměl "
        "co prodat, vypadalo stisknutí Přihlásit se k odběru přesně tak, jako by se nestisklo nikdy. "
        "Teď oba případy mluví, každý ve vlastním dialogu a s uvedením důvodu: Obchod nemá nic k "
        "prodeji, nebo hlásí nákup, který nic neudělil. Jinak se nic nemění: načítání dat, "
        "přehrávání animace a ukládání titulního obrázku zůstává na všech sedmnácti stranách grafů "
        "zdarma a předplatné nadále kupuje jen dvě věci — export videa a odstranění vodoznaku.",
    "ru":
        "Эта версия исправляет одно: покупка, которая не проходила, не говорила решительно ничего. "
        "Когда в магазине нечего было купить, нажатие «Подписаться» выглядело точно так же, как "
        "будто его никогда не нажимали. Теперь оба случая говорят, каждый в своём окне и с указанием "
        "причины: в магазине нечего покупать, либо он сообщает о покупке, которая ничего не дала. "
        "Остальное без изменений: получение данных, воспроизведение анимации и сохранение обложки "
        "остаются бесплатными на всех семнадцати страницах графиков, а подписка по-прежнему "
        "покупает только две вещи — экспорт видео и удаление водяного знака.",
    "tr":
        "Bu sürüm tek bir şeyi düzeltiyor: gerçekleşmeyen bir satın alma hiçbir şey söylemiyordu. "
        "Mağazada satılacak bir şey olmadığında Abone ol'a basmak, hiç basılmamış gibi görünüyordu. "
        "Artık iki durum da konuşuyor, her biri kendi penceresinde ve nedeniyle: Mağazada satın "
        "alınacak bir şey yok ya da mağaza hiçbir yetki vermeyen bir satın alma bildiriyor. Bunun "
        "dışında değişen bir şey yok: veri çekme, animasyonu oynatma ve kapak görselini kaydetme on "
        "yedi grafik sayfasının tamamında ücretsiz kalıyor ve abonelik hâlâ yalnızca iki şey satın "
        "alıyor — video dışa aktarma ve filigranı kaldırma.",
}


def main():
    raw = LISTING.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        print("× store-listing.md 带着 BOM —— 商店文案不能带，先去掉再跑")
        return 1

    # 各文件保持自己的行尾：store-listing.md 是 CRLF。
    crlf = b"\r\n" in raw
    lines = raw.decode("utf-8").replace("\r\n", "\n").split("\n")
    heads = [i for i, s in enumerate(lines) if s.startswith("## ")]

    if len(heads) != 14:
        print(f"× 数到 {len(heads)} 个语言段，应当是 14")
        return 1

    if sorted(NEWS) != sorted(LANGS):
        print("× 文案漏了语言：%s" % sorted(set(LANGS) - set(NEWS)))
        return 1

    changed = 0

    for n, lang in enumerate(LANGS):
        start = heads[n]
        end = heads[n + 1] if n + 1 < len(heads) else len(lines)
        subs = [i for i in range(start, end) if lines[i].startswith("### ")]

        if len(subs) < 2:
            print(f"× {lang}: 只数到 {len(subs)} 个小标题")
            return 1

        at = subs[1] + 1       # 「此版本的新增功能」下面的正文

        while at < end and not lines[at].strip():
            at += 1

        text = NEWS[lang]

        if lines[at] == text:
            print(f"· {lang}: （已是本版，{len(text)} 字）")
            continue

        lines[at] = text
        changed += 1
        heads = [i for i, s in enumerate(lines) if s.startswith("## ")]
        print(f"· {lang}: 「{lines[subs[1]][4:]}」改写（{len(text)} 字）")

    if changed:
        LISTING.write_bytes(("\r\n" if crlf else "\n").join(lines).encode("utf-8"))

    longest = max((len(NEWS[l]), l) for l in LANGS)
    over = [(l, len(NEWS[l])) for l in LANGS if len(NEWS[l]) > LIMIT]

    if over:
        print(f"\n！超过商店 {LIMIT} 字上限：{over}")
        return 1

    print(f"\n最长的 {longest[1]} {longest[0]} 字，都在 {LIMIT} 以内")
    print(f"改了 {changed} 条（跑第二遍应当是 0）")

    return 0


if __name__ == "__main__":
    sys.exit(main())
