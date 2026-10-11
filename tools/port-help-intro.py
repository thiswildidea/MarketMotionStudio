# -*- coding: utf-8 -*-
r"""把 14 份手册的开篇那句「只有 A 股」改成「四个市场，发给竖屏平台」。

**为什么。** 手册第一句是读者看到的第一句话，它一直写着「这个应用把 **A 股市场**的指标
做成手机竖屏视频」—— 那是 1.0.0.0 的话。此后加了港股、美股，又加了第四个市场加密货币，
而这句话一个字没动：它读起来仍然通顺，仍然对，只是**把应用说小了三倍**。商店文案
（`docs/store-listing.md` 的 Description）早就写了四个市场和 TikTok/Shorts/Reels，
手册却还停在一个市场，两处对不上。

**改成什么。** 三件事说全，不新增术语：

1. 数据是**股票市场（A 股、港股、美股）与虚拟货币**的指标 —— 不再是「A 股市场」。
2. 输出是**手机竖屏（9:16）动画视频**，导出 **MP4**。
3. 导出的东西**直接发**到竖屏平台：抖音、快手、小红书、视频号，以及 TikTok、YouTube、
   Instagram。这句话是用户真正要知道的那件事 —— 它是给「做竖屏内容的人」用的工具。

**整行替换，不追加。** 原来那一行本身就是要改的那句，所以按行整句换掉（前两行是标题和
空行，不动）。这与「手册只追加不重写」的规矩不冲突：那条规矩管的是**别去重写别人斟酌过
的译文**，而这一句是**事实变了**，不是措辞不好。

**平台名各语言照抄原文。** 抖音/快手/小红书/视频号在拉丁字母语言里写成 Douyin、
Kuaishou、Xiaohongshu、WeChat Channels（专有名词不译），日韩用原文加注。中文两份用中文名。
TikTok / YouTube / Instagram 全语言统一原文。

**幂等靠新句的标记词**：第二次跑时旧句已经不在了，脚本按新句中那句话认出「换过了」并跳过；
两边都找不到才算出错。

BOM **照抄原文** —— 这 14 份实测**不带** BOM（`port-crypto-search-help.py` 的注释已经记过
一次，别再加）。

用法：python tools\port-help-intro.py
"""
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Assets\Help")

# 每份：(原来那一句, 换成的句子)。两句都必须是文件里的**整行**。
RULES = {
    "en-US": (
        "This app turns A-share market indicators into vertical videos for phones. You pick a period, look at the preview until it reads well, and export an MP4. Nothing else has to be installed.",
        "This app turns stock-market indicators — China A-shares, Hong Kong and the United States — and cryptocurrency into vertical (9:16) animated videos for phones. You pick a period, look at the preview until it reads well, and export an MP4 ready to post straight to Douyin, Kuaishou, Xiaohongshu, WeChat Channels, TikTok, YouTube and Instagram. Nothing else has to be installed.",
    ),
    "zh-Hans": (
        "这个应用把 A 股市场的指标做成手机竖屏视频。选好区间，看预览直到读起来顺，然后导出 MP4。不需要再装任何东西。",
        "这个应用把股票市场（A 股、港股、美股）和虚拟货币的行情指标做成手机竖屏（9:16）动画视频。选好区间，看预览直到读起来顺，然后导出 MP4，直接发到抖音、快手、小红书、视频号以及 TikTok、YouTube、Instagram 上。不需要再装任何东西。",
    ),
    "zh-Hant": (
        "這個應用程式把 A 股市場的指標做成手機直式影片。選好區間，看預覽直到讀起來順，然後匯出 MP4。不需要再裝任何東西。",
        "這個應用程式把股票市場（A 股、港股、美股）與虛擬貨幣的行情指標做成手機直式（9:16）動畫影片。選好區間，看預覽直到讀起來順，然後匯出 MP4，直接發到抖音、快手、小紅書、視頻號以及 TikTok、YouTube、Instagram 上。不需要再裝任何東西。",
    ),
    "ja": (
        "このアプリは A 株市場の指標をスマートフォン向けの縦型動画にします。期間を選び、読みやすくなるまでプレビューを見て、MP4 として書き出します。ほかに何もインストールする必要はありません。",
        "このアプリは、株式市場（中国 A 株、香港、米国）と暗号資産の指標をスマートフォン向けの縦型（9:16）アニメーション動画にします。期間を選び、読みやすくなるまでプレビューを見て MP4 として書き出せば、抖音（Douyin）、快手（Kuaishou）、小紅書（Xiaohongshu）、視頻号（WeChat Channels）、TikTok、YouTube、Instagram にそのまま投稿できます。ほかに何もインストールする必要はありません。",
    ),
    "ko": (
        "이 앱은 A주 시장 지표를 휴대폰용 세로 영상으로 만듭니다. 기간을 고르고, 잘 읽힐 때까지 미리 보기를 확인한 뒤 MP4로 내보냅니다. 따로 설치할 것은 없습니다.",
        "이 앱은 주식 시장(중국 A주, 홍콩, 미국)과 암호화폐 지표를 휴대폰용 세로형(9:16) 애니메이션 영상으로 만듭니다. 기간을 고르고, 잘 읽힐 때까지 미리 보기를 확인한 뒤 MP4로 내보내면 더우인(Douyin), 콰이서우(Kuaishou), 샤오홍슈(Xiaohongshu), 웨이신 채널(視頻号), TikTok, YouTube, Instagram에 바로 게시할 수 있습니다. 따로 설치할 것은 없습니다.",
    ),
    "de": (
        "Diese App macht aus Kennzahlen des A-Aktien-Markts hochformatige Videos für das Telefon. Sie wählen einen Zeitraum, betrachten die Vorschau, bis sie sich gut liest, und exportieren eine MP4-Datei. Mehr muss nicht installiert werden.",
        "Diese App macht aus Kennzahlen des Aktienmarkts — A-Aktien, Hongkong und USA — und aus Kryptowährungen hochformatige (9:16) Animationsvideos für das Telefon. Sie wählen einen Zeitraum, betrachten die Vorschau, bis sie sich gut liest, und exportieren eine MP4-Datei, die sich direkt auf Douyin, Kuaishou, Xiaohongshu, WeChat-Kanälen, TikTok, YouTube und Instagram posten lässt. Mehr muss nicht installiert werden.",
    ),
    "es": (
        "Esta aplicación convierte indicadores del mercado de acciones A en vídeos verticales para el móvil. Elija un periodo, mire la vista previa hasta que se lea bien y exporte un MP4. No hace falta instalar nada más.",
        "Esta aplicación convierte indicadores del mercado de acciones —A, Hong Kong y Estados Unidos— y de criptomonedas en vídeos animados verticales (9:16) para el móvil. Elija un periodo, mire la vista previa hasta que se lea bien y exporte un MP4 listo para publicar directamente en Douyin, Kuaishou, Xiaohongshu, Canales de WeChat, TikTok, YouTube e Instagram. No hace falta instalar nada más.",
    ),
    "fr": (
        "Cette application transforme des indicateurs du marché des actions A en vidéos verticales pour téléphone. Vous choisissez une période, vous regardez l'aperçu jusqu'à ce qu'il se lise bien, puis vous exportez un MP4. Rien d'autre n'est à installer.",
        "Cette application transforme des indicateurs du marché des actions — A, Hong Kong et États-Unis — et des cryptomonnaies en vidéos animées verticales (9:16) pour téléphone. Vous choisissez une période, vous regardez l'aperçu jusqu'à ce qu'il se lise bien, puis vous exportez un MP4 prêt à publier directement sur Douyin, Kuaishou, Xiaohongshu, les canaux WeChat, TikTok, YouTube et Instagram. Rien d'autre n'est à installer.",
    ),
    "it": (
        "Questa app trasforma gli indicatori del mercato delle azioni A in video verticali per il telefono. Scegli un periodo, guardi l'anteprima finché si legge bene, ed esporti un MP4. Non serve installare altro.",
        "Questa app trasforma gli indicatori del mercato azionario — azioni A, Hong Kong e Stati Uniti — e delle criptovalute in video animati verticali (9:16) per il telefono. Scegli un periodo, guardi l'anteprima finché si legge bene, ed esporti un MP4 pronto da pubblicare direttamente su Douyin, Kuaishou, Xiaohongshu, Canali WeChat, TikTok, YouTube e Instagram. Non serve installare altro.",
    ),
    "pt-BR": (
        "Este aplicativo transforma indicadores do mercado de ações A em vídeos verticais para o celular. Você escolhe um período, olha a prévia até que ela se leia bem e exporta um MP4. Nada mais precisa ser instalado.",
        "Este aplicativo transforma indicadores do mercado de ações —ações A, Hong Kong e Estados Unidos— e de criptomoedas em vídeos animados verticais (9:16) para o celular. Você escolhe um período, olha a prévia até que ela se leia bem e exporta um MP4 pronto para publicar direto no Douyin, Kuaishou, Xiaohongshu, Canais do WeChat, TikTok, YouTube e Instagram. Nada mais precisa ser instalado.",
    ),
    "pl": (
        "Ta aplikacja zamienia wskaźniki rynku akcji A w pionowe filmy na telefon. Wybierasz okres, patrzysz na podgląd, aż da się go dobrze odczytać, i eksportujesz plik MP4. Nic więcej nie trzeba instalować.",
        "Ta aplikacja zamienia wskaźniki rynku akcji — akcji A, Hongkongu i Stanów Zjednoczonych — oraz kryptowalut w pionowe (9:16) filmy animowane na telefon. Wybierasz okres, patrzysz na podgląd, aż da się go dobrze odczytać, i eksportujesz plik MP4 gotowy do publikacji od razu na Douyin, Kuaishou, Xiaohongshu, kanałach WeChat, TikToku, YouTube i Instagramie. Nic więcej nie trzeba instalować.",
    ),
    "cs": (
        "Tato aplikace mění ukazatele trhu akcií A na svislá videa pro telefon. Vyberete období, prohlédnete si náhled, dokud se dobře nečte, a exportujete MP4. Nic dalšího instalovat netřeba.",
        "Tato aplikace mění ukazatele akciového trhu — akcií A, Hongkongu a Spojených států — a kryptoměn ve svislá (9:16) animovaná videa pro telefon. Vyberete období, prohlédnete si náhled, dokud se dobře nečte, a exportujete MP4 připravené k přímému publikování na Douyin, Kuaishou, Xiaohongshu, kanálech WeChat, TikToku, YouTube a Instagramu. Nic dalšího instalovat netřeba.",
    ),
    "ru": (
        "Это приложение превращает показатели рынка акций A в вертикальные видео для телефона. Вы выбираете период, смотрите предпросмотр, пока он не станет читаться, и экспортируете MP4. Ничего больше устанавливать не нужно.",
        "Это приложение превращает показатели фондового рынка — акций A, Гонконга и США — и криптовалют в вертикальные (9:16) анимированные видео для телефона. Вы выбираете период, смотрите предпросмотр, пока он не станет читаться, и экспортируете MP4, готовый к публикации сразу в Douyin, Kuaishou, Xiaohongshu, каналах WeChat, TikTok, YouTube и Instagram. Ничего больше устанавливать не нужно.",
    ),
    "tr": (
        "Bu uygulama A hisse piyasasının göstergelerini telefon için dikey videolara dönüştürür. Bir dönem seçer, iyi okunana kadar ön izlemeye bakar ve MP4 olarak verirsiniz. Başka hiçbir şey kurmanız gerekmez.",
        "Bu uygulama borsa göstergelerini — A hisseleri, Hong Kong ve ABD — ve kripto paraları telefon için dikey (9:16) animasyon videolara dönüştürür. Bir dönem seçer, iyi okunana kadar ön izlemeye bakar ve Douyin, Kuaishou, Xiaohongshu, WeChat Kanalları, TikTok, YouTube ve Instagram'da doğrudan paylaşabileceğiniz bir MP4 olarak verirsiniz. Başka hiçbir şey kurmanız gerekmez.",
    ),
}

def main():
    switched = 0
    failed = 0

    for tag, (old, new) in RULES.items():
        path = ROOT / f"help-{tag}.md"

        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig")

        lines = text.split("\n")

        if new in lines:
            print(f"{tag:8} already switched")
            continue

        hit = None
        for i, line in enumerate(lines):
            if line.strip() == old:
                hit = i
                break

        if hit is None:
            print(f"{tag:8} !! neither the old line nor the new one is here")
            failed += 1
            continue

        lines[hit] = new
        out = "\n".join(lines)

        path.write_bytes(out.encode("utf-8-sig") if had_bom else out.encode("utf-8"))

        print(f"{tag:8} switched (line {hit + 1})")
        switched += 1

    print(f"\n{switched} switched, {failed} failed, {len(RULES)} languages")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
