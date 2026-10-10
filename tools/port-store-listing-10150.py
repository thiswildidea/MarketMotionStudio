# -*- coding: utf-8 -*-
"""把商店文案（docs/store-listing.md，14 语言）的「此版本的新增功能」改到 1.0.15.0。

**这一栏是「换」不是「加」，历史留在 CHANGELOG.md。** 上一版那一栏说的是手册搬到网页上。那是真的，
也已经交上去了（1.0.14.0）。接着往后加，这一栏就成了两件事各说一半。

本版只有一件事：**设置里改了市场或语言之后那条「重启应用」的提示，现在钉在设置页最顶端。** 它不再
是滚动区里的一张卡，而是滚动区**外面**的一行 —— 改完立刻看得见，页面往下滚多远它都停在原处。

**只说用户能感知的那半句，不说实现方式。** 「页面根从 `ScrollViewer` 换成两行 `Grid`」「七个调用点
统一走一处 `Note`」都是代码的事，写出来等于让用户替我们查错。用户那半句是：提示现在在最顶上，滚不
走；而且上面有个「立即重启」按钮，不用自己去关应用。

**也不顺手加别的东西。** 这一版同时修了共用库 `winui.py` 里认画布的那个函数（整批截图都认错框），
那是判据的事、不是产品的事，商店里没有它的位置。

**重音字母照写。** 德语的 ü/ä/ö/ß、法语的 é/ç/à、捷克的 ř/ž/ě/ů、波兰语的 ł/ż/ą/ę、土耳其语的
ğ/ı/şü 是这个字的一部分，不是装饰；为了「保险」把它们写成 u/a/o/s/e/c/r/z/l/g 等于在商店里挂一句
拼错的德语。文件是 UTF-8，Python 3 源码默认就是 UTF-8，没有需要绕开的编码问题。

定位与幂等：每个语言段里第二个 `###` 小标题之后的第一段正文，整行比对。store-listing.md 是
**CRLF 无 BOM**，写完照原样写回（剥掉 `\r` 比对，否则每次都差一个 `\r`，幂等就成了空话）。

**脚本名由 manifest 的版本号算出 `10150`，不是取巧写成 `1150`。** `verify-docs.py` 把四段版本
号**全拼**当作文件名（`1.0.15.0` → 四段拼起来是 `10150`；写成 `1150` 是省掉了第三段的一位，那是
留给 `1.1.5.0` 的形状），算不出/找不到就大声失败。

用法：python tools\\port-store-listing-10150.py      （跑第二遍应当是「改了 0 条」）
"""

import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPO = pathlib.Path(__file__).resolve().parent.parent
LISTING = REPO / "docs" / "store-listing.md"

LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "fr", "it",
         "es", "pt-BR", "pl", "cs", "ru", "tr"]

# 商店这一栏的硬上限。本版只说一件事，比上一版短。每次换文案都要算一遍最长的那一种语言：
# 上限是按字符算的，德/意/葡一句能顶到中文的三倍长。
LIMIT = 1500

# 本版那一句。十四种语言同一种说法：**改了市场或语言之后那条「重启应用」的提示现在钉在设置页最顶
# 端，页面往下滚多远它都停在原处；提示条上还有一个「立即重启」按钮。**
NEWS = {
    "zh-Hans":
        "设置里改了市场或语言之后，那条「重启应用」的提示现在钉在设置页最顶端：改完立刻看得见，页面"
        "往下滚多远它都停在原处。以前它排在滚动区的最后，改完那一眼并不在同一屏。提示条上还有一个"
        "「立即重启」按钮，不用自己去关应用。",
    "zh-Hant":
        "設定裡改了市場或語言之後，那條「重新啟動應用程式」的提示現在釘在設定頁最頂端：改完立刻看得"
        "見，頁面往下捲多遠它都停在原處。以前它排在捲動區的最後，改完那一眼並不在同一個畫面。提示條"
        "上還有一個「立即重新啟動」按鈕，不必自己關掉應用程式。",
    "en-US":
        "The “restart the app” notice shown after you change the market or the language is now "
        "pinned to the top of Settings: it is on screen the moment you change something, and it "
        "stays put however far the page is scrolled. It used to be the last card inside the "
        "scrolling area, four cards below the one you had just changed. The notice also carries a "
        "Restart now button, so you do not have to close the app yourself.",
    "ja":
        "設定で市場や言語を変更したあとに出る「アプリを再起動してください」という通知が、設定ページの"
        "最上部に固定されました。変更した瞬間に画面に表示され、ページをどこまでスクロールしてもその"
        "位置に留まります。以前はスクロール領域の最後にあり、変更した直後の画面には入っていませんで"
        "した。通知には「今すぐ再起動」ボタンも付きました。",
    "ko":
        "시장이나 언어를 바꿀 때 나오는 ‘앱을 다시 시작하세요’ 안내가 이제 설정 페이지 맨 위에 고정됩"
        "니다. 바꾸는 순간 화면에 보이고, 페이지를 아무리 아래로 스크롤해도 그 자리에 그대로 있습니다. "
        "예전에는 스크롤 영역의 맨 마지막에 있어 방금 바꾼 항목과 같은 화면에 없었습니다. 안내에 ‘지금 "
        "다시 시작’ 버튼도 함께 붙었습니다.",
    "de":
        "Der Hinweis „App neu starten“, der nach dem Ändern des Marktes oder der Sprache erscheint, "
        "steht jetzt oben in den Einstellungen: Er ist in dem Moment sichtbar, in dem du etwas "
        "änderst, und bleibt dort, egal wie weit die Seite gescrollt wird. Früher war er die letzte "
        "Karte im Scrollbereich, vier Karten unter der gerade geänderten. Der Hinweis hat außerdem "
        "die Schaltfläche „Jetzt neu starten“.",
    "fr":
        "La mention « redémarrer l’application » affichée après un changement de marché ou de "
        "langue est maintenant épinglée en haut des paramètres : elle apparaît dès le changement et "
        "reste en place, quelle que soit la distance de défilement de la page. Elle était "
        "auparavant la dernière carte de la zone de défilement, quatre cartes sous celle que vous "
        "veniez de modifier. La mention porte aussi un bouton « Redémarrer maintenant ».",
    "it":
        "L’avviso «riavvia l’app» mostrato dopo aver cambiato mercato o lingua è ora fissato in "
        "cima alle impostazioni: compare nel momento stesso in cui fai la modifica e resta lì, "
        "qualunque sia lo scorrimento della pagina. Prima era l’ultima scheda dell’area scorrevole, "
        "quattro schede sotto quella che avevi appena modificato. L’avviso ha anche un pulsante "
        "«Riavvia ora».",
    "es":
        "El aviso «reinicia la aplicación» que aparece al cambiar el mercado o el idioma ahora está "
        "fijado en la parte superior de la configuración: se ve en el momento en que haces el cambio "
        "y se queda ahí por mucho que se desplace la página. Antes era la última tarjeta del área de "
        "desplazamiento, cuatro tarjetas por debajo de la que acababas de cambiar. El aviso incluye "
        "además un botón «Reiniciar ahora».",
    "pt-BR":
        "O aviso «reinicie o aplicativo» exibido ao alterar o mercado ou o idioma agora fica fixado "
        "no topo das configurações: aparece no momento em que você faz a alteração e permanece lá, "
        "não importa o quanto a página role. Antes era o último cartão da área de rolagem, quatro "
        "cartões abaixo do que você acabou de alterar. O aviso também traz um botão «Reiniciar "
        "agora».",
    "pl":
        "Komunikat „uruchom aplikację ponownie”, który pojawia się po zmianie rynku lub języka, jest "
        "teraz przypięty na górze ustawień: widać go w momencie zmiany i zostaje na miejscu, "
        "niezależnie od tego, jak daleko przewiniesz stronę. Dawniej był ostatnią kartą w obszarze "
        "przewijania, cztery karty poniżej tej, którą właśnie zmieniłeś. Komunikat ma też przycisk "
        "„Uruchom ponownie teraz”.",
    "cs":
        "Oznámení „restartujte aplikaci“, které se zobrazí po změně trhu nebo jazyka, je nyní "
        "připnuté v horní části nastavení: je vidět v okamžiku změny a zůstává na místě, ať stránku "
        "posunete kamkoli. Dříve bylo poslední kartou v oblasti posouvání, čtyři karty pod tou, "
        "kterou jste právě změnili. Oznámení má také tlačítko „Restartovat“.",
    "ru":
        "Сообщение «перезапустите приложение», которое появляется после смены рынка или языка, "
        "теперь закреплено в верхней части настроек: оно видно в момент изменения и остаётся на "
        "месте, как далеко ни прокрутите страницу. Раньше оно было последней карточкой в "
        "прокручиваемой области — на четыре карточки ниже той, которую вы только что изменили. В "
        "сообщении есть и кнопка «Перезапустить».",
    "tr":
        "Pazarı veya dili değiştirdikten sonra görünen «uygulamayı yeniden başlatın» bildirimi artık "
        "Ayarlar’ın en üstüne sabitlendi: değişikliği yaptığınız anda görünür ve sayfayı ne kadar "
        "kaydırırsanız kaydırın yerinde kalır. Eskiden kaydırma alanının son kartıydı — az önce "
        "değiştirdiğiniz kartın dört kart altında. Bildirimde ayrıca «Şimdi yeniden başlat» düğmesi "
        "var.",
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
