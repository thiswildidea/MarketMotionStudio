# -*- coding: utf-8 -*-
"""把商店文案（docs/store-listing.md，14 语言）的「此版本的新增功能」改到 1.0.14.0。

**这一栏是「换」不是「加」，历史留在 CHANGELOG.md。** 上一版那一栏说的是多标的画面上方会说出
「画面走到哪儿了」。那是真的，也已经交上去了（1.0.13.0，审核中）。接着往后加，这一栏就成了两件事
各说一半。

本版只有一件事：**手册搬到网页上了。** 14 种语言的手册既随应用一起提供，也在网页上有一份；应用里
打开的那份先取网页，取不到就用应用自带的。用户能感知的只有一句话 —— 往后手册的改动不必等下一个版
本才会生效。

**不提实现方式。** 取网页是多少秒超时、URL 长什么样、取回来的东西怎么校验才敢用、配图是逐字节比对
着同步过去的 —— 那都是代码的事，写出来等于让用户替我们查错。

**也不提具体的网址。** 商店文案里的网址会被当成广告位，而且它是会变的。

顺带一句：本版把手册里的配图全部重拍了一遍（旧的几张是半透明窗口下截的，桌面壁纸会透过窗口映在画
面上）。这是「图变清楚了」，不是新功能，所以只占一句，不单独成段。

**重音字母照写。** 德语的 ü/ä/ö/ß、法语的 é/ç/à、捷克的 ř/ž/ě/ů、波兰语的 ł/ż/ą/ę、土耳其语的
ğ/ı/ş/ü 是这个字的一部分，不是装饰；为了「保险」把它们写成 u/a/o/s/e/c/r/z/l/g 等于在商店里挂一句
拼错的德语。文件是 UTF-8，Python 3 源码默认就是 UTF-8，没有需要绕开的编码问题。

定位与幂等：每个语言段里第二个 `###` 小标题之后的第一段正文，整行比对。store-listing.md 是
**CRLF 无 BOM**，写完照原样写回（剥掉 `\r` 比对，否则每次都差一个 `\r`，幂等就成了空话）。

**脚本名由 manifest 的版本号算出 `10140`，不是取巧写成 `1140`。** `verify-docs.py` 把四段版本
号**全拼**当作文件名（`1.0.14.0` → 四段拼起来是 `10140`；写成 `1140` 是省掉了第三段的一位，那是
留给 `1.1.4.0` 的形状），算不出/找不到就大声失败。

用法：python tools\\port-store-listing-10140.py      （跑第二遍应当是「改了 0 条」）
"""

import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPO = pathlib.Path(__file__).resolve().parent.parent
LISTING = REPO / "docs" / "store-listing.md"

LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "fr", "it",
         "es", "pt-BR", "pl", "cs", "ru", "tr"]

# 商店这一栏的硬上限。本版只说一件事，比上一版长一点点（多了一句配图重拍），但每次换文案都要算一遍
# 最长的那一种语言：上限是按字符算的，德/意/葡一句能顶到中文的三倍长。
LIMIT = 1500

# 本版那一句。十四种语言同一种说法：**手册现在也在网页上，应用里打开的那份先取网页、取不到就用自带
# 的，所以手册往后的改动不必等下一个版本；本版也把手册里的配图重拍了一遍。**
NEWS = {
    "zh-Hans":
        "本版把 14 种语言的使用手册一并发布到网页上：手册既随应用一起提供，也在网页上有一份，应用里"
        "打开的那份先取网页，取不到就用应用自带的 —— 以后手册的改动不必等下一个版本才会生效。这一版"
        "也把手册里的配图全部重拍了一遍。",
    "zh-Hant":
        "本版把 14 種語言的使用手冊一併發布到網頁上：手冊既隨應用程式一起提供，也在網頁上有一份，應"
        "用程式裡打開的那份先取網頁，取不到就用應用程式自帶的 —— 以後手冊的改動不必等下一個版本才會"
        "生效。這一版也把手冊裡的配圖全部重拍了一遍。",
    "en-US":
        "This version publishes the manual for all 14 languages on the web as well: the manual ships "
        "with the app and also lives on the web, and the copy you open in the app is taken from the "
        "web when it can be, falling back to the one inside the app when it cannot — so changes to "
        "the manual no longer have to wait for the next version. The pictures in the manual have been "
        "retaken for this version too.",
    "ja":
        "今回のバージョンでは、14 言語のマニュアルをウェブにも公開しました。マニュアルはアプリに同梱"
        "されるとともにウェブ上にも置かれ、アプリで開くものはウェブから取得し、取得できない場合はア"
        "プリ内のものを使います。これにより、マニュアルの変更が次のバージョンを待たずに反映されるよ"
        "うになりました。また、マニュアル内の図版もすべて撮り直しました。",
    "ko":
        "이번 버전에서는 14개 언어의 설명서를 웹에도 함께 공개했습니다. 설명서는 앱에 포함되어 제공되는 "
        "동시에 웹에도 있으며, 앱에서 여는 설명서는 웹에서 가져오고 가져올 수 없으면 앱 안의 것을 "
        "사용합니다. 이제 설명서의 변경이 다음 버전을 기다리지 않아도 됩니다. 설명서의 그림도 이번 "
        "버전에서 모두 다시 캡처했습니다.",
    "de":
        "Diese Version veröffentlicht das Handbuch in allen 14 Sprachen auch im Web: Es wird mit der "
        "App geliefert und liegt zugleich im Web, und was in der App geöffnet wird, holt die App aus "
        "dem Web und greift nur, wenn das nicht gelingt, auf die eingebaute Kopie zurück. Änderungen "
        "am Handbuch müssen damit nicht mehr auf die nächste Version warten. Die Bilder im Handbuch "
        "wurden für diese Version ebenfalls neu aufgenommen.",
    "fr":
        "Cette version publie aussi le manuel dans les 14 langues sur le web : il est fourni avec "
        "l'application et se trouve en même temps en ligne, et celui que vous ouvrez dans "
        "l'application est pris sur le web lorsque c'est possible, à défaut c'est la copie intégrée "
        "qui est utilisée. Les modifications du manuel n'ont ainsi plus à attendre la version "
        "suivante. Les images du manuel ont également été refaites pour cette version.",
    "it":
        "Questa versione pubblica anche sul web il manuale in tutte le 14 lingue: il manuale è "
        "fornito con l'applicazione e si trova allo stesso tempo online, e quello che aprite "
        "nell'applicazione è preso dal web quando è possibile, altrimenti viene usata la copia "
        "incorporata. Le modifiche al manuale non devono così più attendere la versione successiva. "
        "Anche le immagini del manuale sono state rifatte per questa versione.",
    "es":
        "Esta versión publica también en la web el manual en los 14 idiomas: se entrega con la "
        "aplicación y a la vez está en línea, y el que se abre en la aplicación se toma de la web "
        "cuando es posible; si no, se usa la copia incluida. Así los cambios del manual ya no tienen "
        "que esperar a la siguiente versión. Las imágenes del manual también se han rehecho en esta "
        "versión.",
    "pt-BR":
        "Esta versão também publica na web o manual nos 14 idiomas: ele acompanha o aplicativo e ao "
        "mesmo tempo está online, e o que você abre no aplicativo é obtido da web quando possível; "
        "caso contrário, usa-se a cópia embutida. Assim, as alterações no manual não precisam mais "
        "esperar pela próxima versão. As imagens do manual também foram refeitas nesta versão.",
    "pl":
        "Ta wersja publikuje również w sieci podręcznik we wszystkich 14 językach: jest dostarczany "
        "z aplikacją i jednocześnie dostępny online, a ten otwierany w aplikacji jest pobierany z "
        "sieci, gdy się da, a w przeciwnym razie używana jest wbudowana kopia. Dzięki temu zmiany w "
        "podręczniku nie muszą czekać na następną wersję. Ilustracje w podręczniku również zostały "
        "w tej wersji wykonane od nowa.",
    "cs":
        "Tato verze zveřejňuje příručku ve všech 14 jazycích také na webu: je dodávána s aplikací a "
        "zároveň je dostupná online, a ta, kterou otevřete v aplikaci, se bere z webu, když to jde, "
        "jinak se použije vestavěná kopie. Změny v příručce tak nemusí čekat na další verzi. Obrázky "
        "v příručce byly pro tuto verzi rovněž pořízeny znovu.",
    "ru":
        "В этой версии руководство на всех 14 языках публикуется также в интернете: оно поставляется "
        "вместе с приложением и одновременно доступно онлайн; то, что открывается в приложении, "
        "берётся из интернета, когда это возможно, а иначе используется встроенная копия. Благодаря "
        "этому изменения в руководстве больше не должны ждать следующей версии. Иллюстрации в "
        "руководстве для этой версии тоже сделаны заново.",
    "tr":
        "Bu sürümde 14 dilin tümündeki kılavuz web'de de yayımlanıyor: kılavuz uygulamayla birlikte "
        "geliyor ve aynı zamanda çevrimiçi olarak da bulunuyor; uygulamada açılan, mümkün olduğunda "
        "web'den alınıyor, alınamadığında yerleşik kopya kullanılıyor. Böylece kılavuzdaki "
        "değişikliklerin bir sonraki sürümü beklemesi gerekmiyor. Kılavuzdaki görseller de bu sürüm "
        "için yeniden çekildi.",
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
