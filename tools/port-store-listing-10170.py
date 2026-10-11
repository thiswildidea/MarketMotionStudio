# -*- coding: utf-8 -*-
"""把商店文案（docs/store-listing.md，14 语言）的「此版本的新增功能」改到 1.0.17.0。

**这一栏是「换」不是「加」，历史留在 CHANGELOG.md。** 上一版那一栏说的是加密货币成为一个市场、
带来六个页面。那已经交上去了（1.0.16.0），所以本版**另起一条，只说它之后的改动**。

**本版没有新页面，是把手册补齐。** 两件事，都是打开帮助就能看见的：

- 加密货币那六个章节各配一张图，而图是从**那个语言自己的窗口**里截的 —— 土耳其语手册里是土耳其
  语的窗口。一份英文截图下面垫十四种说明，那是给不会读英文的人看英文。
- 开篇那句话重写了。它从第一个版本起就在说这个应用做的是 A 股行情，**后来加了三个市场它一个字
  没动** —— 一句仍然正确的话，读起来像已经写完的。现在它说清四件事：四个市场、9:16 竖屏动画、
  导出的 MP4、以及那个文件要发到哪里。

**为什么要为「改文档」发一个版本。** 手册大部分时候是从网上读的，改完推一次站点就生效；但**包里
那份副本**是取不到网时才用的，它只能跟着包走。商店描述同理 —— 它是写在清单里的。

**只说用户能感知的那半句。** 「截图脚本按整行替换」「`port-help-intro.py`」都是代码的事。但
「图是从你自己的语言窗口里截的」**必须说**：它决定了那六章的图为什么不是一张通用截图。

**重音字母照写。** 德语的 ü/ä/ö/ß、法语的 é/ç/à、捷克的 ř/ž/ě/ů、波兰语的 ł/ż/ą/ę、土耳其语的
ğ/ı/ş 是这个字的一部分，不是装饰；为了「保险」把它们写成 u/a/o/s/e/c/r/z/l/g 等于在商店里挂一句
拼错的德语。文件是 UTF-8，Python 3 源码默认就是 UTF-8，没有需要绕开的编码问题。

定位与幂等：每个语言段里第二个 `###` 小标题之后的第一段正文，整行比对。store-listing.md 是
**CRLF 无 BOM**，写完照原样写回（剥掉 `\r` 比对，否则每次都差一个 `\r`，幂等就成了空话）。

**脚本名由 manifest 的版本号算出 `10170`，不是取巧写成 `1170`。** `verify-docs.py` 把四段版本
号**全拼**当作文件名（`1.0.17.0` → 四段拼起来是 `10170`；写成 `1170` 是省掉了第三段的一位，那是
留给 `1.1.7.0` 的形状），算不出/找不到就大声失败。

用法：python tools\\port-store-listing-10170.py      （跑第二遍应当是「改了 0 条」）
"""

import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPO = pathlib.Path(__file__).resolve().parent.parent
LISTING = REPO / "docs" / "store-listing.md"

LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "fr", "it",
         "es", "pt-BR", "pl", "cs", "ru", "tr"]

# 商店这一栏的硬上限。本版说两件事，比上一版短。欧洲语言一句能顶到中文的三倍长，所以每次换文案
# 都要把最长的那一种语言打出来看一眼。
LIMIT = 1500

# 本版那一句。十四种语言同一种说法：**手册补齐了 —— 加密六章各有自己语言窗口的图；开篇那句话不再
# 只说 A 股，而是四个市场、9:16、MP4 和发到哪里。**
NEWS = {
    "zh-Hans":
        "手册补齐了。加密货币那六个章节现在各有一张图——图是从那个语言自己的窗口里截的，所以土耳其语的"
        "手册里是土耳其语的窗口，不是一张英文截图下面垫十四种说明。开篇那句话也重写了：它从第一个版本"
        "起就在说这个应用做的是 A 股行情，后来加了三个市场它一个字没动——一句仍然正确的话，读起来像已"
        "经写完的。现在它说清了四件事：股票（A 股、港股、美股）和加密货币四个市场，9:16 竖屏动画，导出"
        "的 MP4，以及那个文件要发到哪里——抖音、快手、小红书、视频号、TikTok、YouTube、Instagram。",
    "zh-Hant":
        "手冊補齊了。加密貨幣那六個章節現在各有一張圖——圖是從那個語言自己的視窗裡截的，所以土耳其語的"
        "手冊裡是土耳其語的視窗，不是一張英文截圖下面墊十四種說明。開篇那句話也重寫了：它從第一個版本"
        "起就在說這個應用做的是 A 股行情，後來加了三個市場它一個字沒動——一句仍然正確的話，讀起來像已"
        "經寫完的。現在它說清了四件事：股票（A 股、港股、美股）和加密貨幣四個市場，9:16 直式動畫，匯出"
        "的 MP4，以及那個檔案要發到哪裡——抖音、快手、小紅書、視頻號、TikTok、YouTube、Instagram。",
    "en-US":
        "The manual is filled in. The six cryptocurrency chapters now each carry a picture — taken from "
        "that language's own window, so the Turkish manual shows a Turkish window rather than one English "
        "screenshot with fourteen captions underneath. The opening sentence has been rewritten too: since "
        "the first release it said this app turns A-share indicators into videos, and it never moved "
        "while three markets were added, because a sentence that is still true reads as one that is "
        "finished. It now says four things: four markets — China A-shares, Hong Kong, the US and "
        "cryptocurrency — the 9:16 vertical animation, the MP4 it exports, and where that file is meant "
        "to go: Douyin, Kuaishou, Xiaohongshu, WeChat Channels, TikTok, YouTube and Instagram.",
    "ja":
        "マニュアルが埋まりました。暗号資産の六つの章にそれぞれ図が入りました。その言語自身のウィンドウ"
        "から撮ったものなので、トルコ語のマニュアルにはトルコ語のウィンドウが写っています。一枚の英語"
        "スクリーンショットの下に十四言語の説明を並べたものではありません。冒頭の一文も書き直しました"
        "。初版以来このアプリを「A 株の指標を動画にする」とだけ説明していて、その後三つの市場が加わって"
        "も一字も動きませんでした。まだ正しい文は、書き終えたように読めるのです。今は四つのことを述べ"
        "ます。株式（A 株・香港・米国）と暗号資産の四市場、9:16 の縦型アニメーション、書き出される "
        "MP4、そしてそのファイルの送り先——抖音、快手、小紅書、微信视频号、TikTok、YouTube、"
        "Instagram です。",
    "ko":
        "설명서가 채워졌습니다. 암호화폐 여섯 개 장에 각각 그림이 들어갔습니다. 그 언어 자신의 창에서 "
        "캡처한 것이므로 터키어 설명서에는 터키어 창이 보입니다. 영어 스크린샷 한 장 아래에 열네 언어의 "
        "설명을 붙인 것이 아닙니다. 첫 문장도 다시 썼습니다. 첫 버전부터 이 앱을 ‘A주 지표를 영상으로 "
        "만든다’고만 설명해 왔고, 그 뒤 세 시장이 추가되는 동안 한 글자도 바뀌지 않았습니다. 여전히 옳은 "
        "문장은 이미 완성된 것처럼 읽히기 때문입니다. 이제 네 가지를 말합니다. 주식(A주·홍콩·미국)과 "
        "암호화폐, 네 개의 시장, 9:16 세로 애니메이션, 내보내는 MP4, 그리고 그 파일이 가야 할 곳 — "
        "더우인, 콰이서우, 샤오홍수, 위챗 채널, TikTok, YouTube, Instagram.",
    "de":
        "Das Handbuch ist vervollständigt. Die sechs Kapitel über Kryptowährungen tragen jetzt je ein "
        "Bild, aufgenommen im Fenster der jeweiligen Sprache: Im türkischen Handbuch steht ein "
        "türkisches Fenster, kein englischer Schnittbild, unter dem vierzehn Sprachen dasselbe "
        "erklären. Der erste Satz ist ebenfalls neu geschrieben. Seit der ersten Version hieß es, diese "
        "App mache aus A-Aktien-Kennzahlen Videos, und das blieb unverändert, während drei Märkte "
        "dazukamen — ein Satz, der noch stimmt, liest sich wie fertig. Jetzt nennt er vier Dinge: vier "
        "Märkte — A-Aktien, Hongkong, USA und Kryptowährungen — die 9:16-Animation im Hochformat, das "
        "exportierte MP4 und wohin diese Datei soll: Douyin, Kuaishou, Xiaohongshu, WeChat-Kanäle, "
        "TikTok, YouTube und Instagram.",
    "fr":
        "Le manuel est complété. Les six chapitres sur les cryptomonnaies portent maintenant chacun une "
        "image, prise dans la fenêtre de cette langue : le manuel turc montre une fenêtre turque, et non "
        "une capture anglaise sous laquelle quatorze langues racontent la même chose. La phrase "
        "d’ouverture a été réécrite elle aussi. Depuis la première version elle disait que cette "
        "application transforme les indicateurs des actions A en vidéos, et elle n’a pas bougé pendant "
        "que trois marchés s’ajoutaient — une phrase qui reste vraie se lit comme une phrase finie. Elle "
        "dit maintenant quatre choses : quatre marchés — actions A, Hong Kong, États-Unis et "
        "cryptomonnaies — l’animation verticale 9:16, le MP4 exporté, et là où ce fichier est censé "
        "aller : Douyin, Kuaishou, Xiaohongshu, Chaînes WeChat, TikTok, YouTube et Instagram.",
    "it":
        "Il manuale è completo. I sei capitoli sulle criptovalute hanno ora ciascuno un’immagine, presa "
        "nella finestra di quella lingua: il manuale turco mostra una finestra turca, non uno screenshot "
        "inglese sotto il quale quattordici lingue spiegano la stessa cosa. Anche la frase d’apertura è "
        "stata riscritta. Dalla prima versione diceva che questa app trasforma gli indicatori delle "
        "azioni A in video, e non si è mossa mentre si aggiungevano tre mercati — una frase che è ancora "
        "vera si legge come una frase finita. Ora dice quattro cose: quattro mercati — azioni A, Hong "
        "Kong, Stati Uniti e criptovalute — l’animazione verticale 9:16, l’MP4 esportato e dove quel "
        "file deve andare: Douyin, Kuaishou, Xiaohongshu, Canali WeChat, TikTok, YouTube e Instagram.",
    "es":
        "El manual está completo. Los seis capítulos de criptomonedas llevan ahora una imagen cada uno, "
        "tomada en la ventana de ese idioma: el manual turco muestra una ventana turca, no una captura "
        "en inglés bajo la cual catorce idiomas explican lo mismo. La frase de apertura también se ha "
        "reescrito. Desde la primera versión decía que esta aplicación convierte indicadores de acciones "
        "A en vídeos, y no se movió mientras se añadían tres mercados — una frase que sigue siendo "
        "cierta se lee como una frase terminada. Ahora dice cuatro cosas: cuatro mercados — acciones A, "
        "Hong Kong, Estados Unidos y criptomonedas — la animación vertical 9:16, el MP4 exportado y a "
        "dónde va ese archivo: Douyin, Kuaishou, Xiaohongshu, Canales de WeChat, TikTok, YouTube e "
        "Instagram.",
    "pt-BR":
        "O manual está completo. Os seis capítulos sobre criptomoedas agora trazem uma imagem cada um, "
        "tirada na janela daquele idioma: o manual turco mostra uma janela turca, e não uma captura em "
        "inglês sob a qual catorze idiomas explicam o mesmo. A frase de abertura também foi reescrita. "
        "Desde a primeira versão ela dizia que este aplicativo transforma indicadores de ações A em "
        "vídeos, e não mudou enquanto três mercados eram acrescentados — uma frase que continua certa se "
        "lê como uma frase pronta. Agora diz quatro coisas: quatro mercados — ações A, Hong Kong, "
        "Estados Unidos e criptomoedas — a animação vertical 9:16, o MP4 exportado e para onde esse "
        "arquivo deve ir: Douyin, Kuaishou, Xiaohongshu, Canais do WeChat, TikTok, YouTube e Instagram.",
    "pl":
        "Podręcznik jest uzupełniony. Sześć rozdziałów o kryptowalutach ma teraz po jednym obrazku, "
        "zrobionym w oknie tego języka: turecki podręcznik pokazuje tureckie okno, a nie angielski zrzut "
        "ekranu, pod którym czternaście języków tłumaczy to samo. Pierwsze zdanie również zostało "
        "napisane od nowa. Od pierwszej wersji mówiło, że ta aplikacja zamienia wskaźniki akcji A w "
        "filmy, i nie drgnęło, gdy dochodziły trzy rynki — zdanie, które wciąż jest prawdziwe, czyta się "
        "jak skończone. Teraz mówi cztery rzeczy: cztery rynki — akcje A, Hongkong, USA i kryptowaluty — "
        "animację pionową 9:16, eksportowany MP4 i dokąd ten plik ma trafić: Douyin, Kuaishou, "
        "Xiaohongshu, Kanały WeChat, TikTok, YouTube i Instagram.",
    "cs":
        "Příručka je doplněná. Šest kapitol o kryptoměnách má nyní po jednom obrázku, pořízeném v okně "
        "toho jazyka: turecká příručka ukazuje turecké okno, ne anglický snímek, pod kterým čtrnáct "
        "jazyků vysvětluje totéž. Úvodní věta je také přepsaná. Od první verze říkala, že tato aplikace "
        "mění ukazatele akcií A ve videa, a nepohnula se, zatímco přibyly tři trhy — věta, která je "
        "stále pravdivá, se čte jako hotová. Teď říká čtyři věci: čtyři trhy — akcie A, Hongkong, USA a "
        "kryptoměny — animaci na výšku 9:16, exportované MP4 a kam ten soubor patří: Douyin, Kuaishou, "
        "Xiaohongshu, Kanály WeChat, TikTok, YouTube a Instagram.",
    "ru":
        "Руководство дополнено. Шесть глав о криптовалютах теперь каждая со своим рисунком, снятым в окне "
        "этого языка: в турецком руководстве турецкое окно, а не английский снимок, под которым "
        "четырнадцать языков объясняют одно и то же. Первая фраза тоже переписана. С первой версии она "
        "говорила, что это приложение превращает показатели акций A в видео, и не сдвинулась, пока "
        "добавлялись три рынка, — фраза, которая всё ещё верна, читается как законченная. Теперь она "
        "говорит четыре вещи: четыре рынка — акции A, Гонконг, США и криптовалюты — вертикальная анимация "
        "9:16, экспортируемый MP4 и куда этот файл должен попасть: Douyin, Kuaishou, Xiaohongshu, каналы "
        "WeChat, TikTok, YouTube и Instagram.",
    "tr":
        "Kılavuz tamamlandı. Kripto paralarla ilgili altı bölümün artık her birinin kendi görseli var ve "
        "o görsel o dilin kendi penceresinden alındı: Türkçe kılavuzda Türkçe bir pencere görünüyor, "
        "altında on dört dilin aynı şeyi anlattığı bir İngilizce ekran görüntüsü değil. Açılış cümlesi "
        "de yeniden yazıldı. İlk sürümden beri bu uygulamanın A hissesi göstergelerini videoya "
        "dönüştürdüğünü söylüyordu ve üç pazar eklendiği halde hiç değişmedi — hâlâ doğru olan bir cümle "
        "bitmiş gibi okunuyor. Şimdi dört şeyi söylüyor: dört pazar — A hisseleri, Hong Kong, ABD ve "
        "kripto paralar — 9:16 dikey animasyon, dışa aktarılan MP4 ve o dosyanın gitmesi gereken yer: "
        "Douyin, Kuaishou, Xiaohongshu, WeChat Kanalları, TikTok, YouTube ve Instagram.",
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
