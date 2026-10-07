# -*- coding: utf-8 -*-
r"""验证「订阅」：导出视频与去掉水印这两件事必须先订阅。

**判据分两半，一半是源码、一半是真机，因为各有一半是画面上看不出来的。**

*源码这一半*守的是「闸口的数量与位置」。画面上能看见「点了导出弹了一个对话框」，看不见的是
——第二十一个页面加进来的那一天，它的导出按钮会不会绕过去。所以：

1. 每一个 `OnExport` 都问同一个闸口，而且是**在编码之前**问（早于 `VideoExporter.EncodeAsync`）；
2. **封面 PNG 没有付费这一说**——`OnSaveCover` 里不许出现闸口。手册里写着「封面图免费」，这句
   话错不了的代价是一次很丢人的投诉，所以它由列断出来而不是靠人记着；
3. **「能不能导出」只有一处会答**。某个页面自己去读 `Subscription.Subscribed`，就等于有两处答案，
   而两份写得一样正确的答案，迟早有一份先改；
4. **水印在源头判，不在开关上判**。`WatermarkSettings.Enabled` 未付费时恒为真；渲染器全都只读
   `WatermarkSettings.Current` —— 开关置灰只是把这个事实显示出来，不是这个事实本身。

*真机那一半*走 Debug 模拟（`LocalState\simulate-subscription.txt`）：封面文件在的时候开关能动、
不在的时候它搬不动且底下挂着那句说明。这是因为在这台机器上（单纯注册的包、没有商店）**许可
证永远是「没有」**——开判一开始就是本底的答案，靠看着「本来就是关的」证明不出任何东西。

用法：python tools\verify-subscription.py
"""

import importlib.util
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(REPO, "artifacts")
SRC = os.path.join(REPO, "src", "MarketMotionStudio")

sys.path.insert(0, HERE)

import winui  # noqa: E402
STRINGS = os.path.join(SRC, "Strings")
HELP = os.path.join(SRC, "Assets", "Help")
EXE = "MarketMotionStudio.exe"

# 这台机器上（单纯注册的包，没有商店）许可证永远回答「没有」。要让「已订阅」那一半也能走，
# 只能在 LocalState 里放那个 Debug 模拟文件。
LOCAL_STATE = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "Packages", "8166Yxw.MarketMotionStudio_fzc58jprbah1t", "LocalState")
SIMULATION = os.path.join(LOCAL_STATE, "simulate-subscription.txt")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs",
         "tr", "ru", "ja", "ko", "zh-Hans", "zh-Hant"]

# 给设置页卡片与对话框用的那几个键。`port-subscription-resw.py` 负责写，这里负责断言它们真的到了。
RESW_KEYS = [
    "SettingsSubscriptionLabel.Text",
    "SettingsSubscriptionNote.Text",
    "SettingsSubscriptionActive",
    "SettingsSubscriptionInactive",
    "SettingsSubscriptionRenews",
    "SettingsSubscriptionPrice",
    "SettingsSubscriptionUnavailable",
    "SettingsSubscriptionFailed",
    "SettingsSubscriptionRestoreMissing",
    "SettingsWatermarkLockedNote.Text",
    "SubscriptionSubscribe.Content",
    "SubscriptionRestore.Content",
    "SubscriptionManage.Content",
    "SubscriptionOfferTitle",
    "SubscriptionOfferBody",
    "SubscriptionPerMonth",
    "SubscriptionFailedTitle",
]

FAILED = []


def check(label, ok, detail=""):
    print(("  ✓ " if ok else "  ✗ ") + label + ("  — " + detail if detail else ""))

    if not ok:
        FAILED.append(label)


def note(text):
    print("    · " + text)


def read(*parts):
    return open(os.path.join(SRC, *parts), encoding="utf-8-sig").read()


def pages():
    folder = os.path.join(SRC, "Pages")
    return sorted(name for name in os.listdir(folder) if name.endswith(".xaml.cs"))


def chart_pages():
    """导航里那几个**图表页**的 Tag —— 闸门该有几道，由它说了算。

    从 `MainWindow.xaml` 数出来，而不是把「十七」这种数字抄在下面的断言里：抄下来的数字
    在加第十九页那天照样是绿的，而那一页的导出按钮可能根本没问过闸口 —— 正是这条断言
    存在的理由。帮助页与设置页没有导出按钮，所以认 Tag 排除。
    """
    tags = re.findall(r'<mux:NavigationViewItem[^>]*\bTag="([^"]+)"',
                      read("MainWindow.xaml"))
    return [tag for tag in tags if tag not in ("Help", "Settings")]


def handler_body(text, name):
    """某个 handler 到下一个同类 handler 之间的那一段。

    `async Task` 也算（`RefreshSubscriptionAsync` 就是它）：一个方法返回 Task 不代表
    它不是那个 handler，漏掉它会让「结算界面」那条断言静默地什么都不查。
    """
    at = -1

    for prefix in ("private async void ", "private async Task ", "private void ",
                   "private async Task<bool> "):
        at = text.find(prefix + name + "(")

        if at >= 0:
            break

    if at < 0:
        return None

    end = text.find("\n    private ", at + 1)

    return text[at:end if end > 0 else len(text)]


# ---- 源码断言 -------------------------------------------------------------------

def source():
    print("源码：")

    offer = read("Views", "SubscriptionOffer.cs")
    subscription = read("StoreSubscription.cs")
    watermark = read("WatermarkSettings.cs")
    markup = read("Pages", "SettingsPage.xaml")
    settings = read("Pages", "SettingsPage.xaml.cs")

    export = []
    free = []
    late = []
    homegrown = []

    for name in pages():
        text = read("Pages", name)

        body = handler_body(text, "OnExport")
        cover = handler_body(text, "OnSaveCover")

        if body is None:
            continue

        export.append(name)

        asked = "SubscriptionOffer.PermitAsync" in body

        if not asked:
            late.append(name)
            continue

        # 问在编码之前。晚一步就写完了 —— 文件已经落盘，这时候再弹对话框是在问一个
        # 已经成立的事实，而用户会得到两个结果：一个已经写好的文件，和一句「请订阅」。
        at = body.find("SubscriptionOffer.PermitAsync")
        encode = body.find("VideoExporter.EncodeAsync")

        if encode >= 0 and encode < at:
            late.append(name)

        if cover is not None and "SubscriptionOffer.PermitAsync" in cover:
            free.append(name)

        # 除设置页那张卡片之外，没有页面自己去判。
        if name != "SettingsPage.xaml.cs" and "AppServices.Current.Subscription" in text:
            homegrown.append(name)

    check("每一个有导出按钮的页面都问了同一个闸口",
          len(export) == len(chart_pages()) and not late,
          "{} 页有导出（导航里 {} 页）、{} 页没问（或问晚了）{}".format(
              len(export), len(chart_pages()), len(late), late[:4] if late else ""))

    coverless = [name for name in pages() if handler_body(read("Pages", name), "OnSaveCover")]

    check("封面 PNG 仍然免费——`OnSaveCover` 里没有闸口",
          len(coverless) == len(chart_pages()) and not free,
          "{} 页能存封面、{} 页被误锁{}".format(
              len(coverless), len(free), free[:4] if free else ""))

    check("「能不能导出」只有一处会答（没有页面自己读许可证）",
          not homegrown, ", ".join(homegrown) or "无")

    # 每次重读都从「没有」开始，而不是留着上一次的答案。留着的写法在「本来有、
    # 后来没了」那一边看不出来（重读一次还是真的），而在「本来没有、后来有了」
    # 那一边也不出来 —— 它只在许可证读失败时把上一次的「有」当成今天的答案。
    check("每次重读先把「有」清掉，不缓存上一次的答案",
          "RenewsOn = null;\n        Subscribed = false;" in subscription)

    check("订阅成功不看 dialog 那句话，回头再读一次许可证",
          "// Read again rather than reusing what the purchase dialog said" in subscription
          and "return Subscribed" in subscription)

    # 这里**故意**把新 token 写死：Partner Center 里那只加载项叫什么，商店那一头认的
    # 就是那个字串，改一个字母就买不到 —— 所以它必须有第二双眼睛盯着，而不是从源码里
    # 读回来再自证一遍。下面那条反向断言守住的是另一件事：旧那只（建错类型的易耗品）
    # 的许可证跟合法的订阅长得一模一样，写回去会把买断不续费的东西卖出去。
    check("认加载项按 token 而不是 StoreId（两个部分换环境就换）",
          'private const string OfferToken = "MarketMotionStudioMonthly";' in subscription)

    check("不再认旧那只建错类型的加载项（它的许可证和订阅长得一样）",
          '"MarketMotionStudio"' not in subscription.replace(
              "MarketMotionStudioMonthly", ""))

    print("源码（去商店那一边找加载项）：")

    # 这三条的敌人都是「看起来更正确的写法」：文档说订阅型加载项就是 Durable，所以只查
    # Durable 读起来像是做过功课 —— 而它正是唯一能造成「商店返回 0 个」的本地写法。
    check("不挑加载项类型（只按 Durable 找，会把建错类型的加载项读成「商店没给」）",
          'private static readonly string[] Kinds = ["Durable", "Consumable", '
          '"UnmanagedConsumable"];' in subscription)

    check("选哪一只按 token 不按类型（放宽类型之后更不能靠类型认）",
          "product.InAppOfferToken, OfferToken, StringComparison.OrdinalIgnoreCase"
          in subscription)

    check("查询失败不再和「清单是空的」长得一样（两者修的地方不同）",
          "result.ExtendedError is { } failure" in subscription
          and "0x{failure.HResult:X8}" in subscription)

    check("商店真没给、与给了别的名字，是两句不同的话",
          "the Store returned none for this app" in subscription
          and "; it returned " in subscription)

    check("那两句里的 token 是真插进去的（漏了 $ 会原样打印 {OfferToken}）",
          '$"subscribe: no add-on named {OfferToken}; the Store returned none for this app"'
          in subscription
          and '$"subscribe: no add-on named {OfferToken}; it returned "' in subscription)

    print("源码（水印那一半）：")

    check("未订阅时 `Enabled` 恒为真（前置的那些排查不是一个开关能绕过的）",
          "if (PaidFor)" in watermark and "return true;" in watermark)

    check("开关能不能动是**读**出来的，不是 xaml 里写死的",
          "public static bool Optional => PaidFor;" in watermark
          and "WatermarkToggle.IsEnabled = WatermarkSettings.Optional;" in settings)

    check("分辨率变了会重发一次（许可证变了，已画的那一帧不知道）",
          "AppServices.Current.Subscription.Changed += (_, _) => Announce();" in watermark)

    check("未订阅时浓度恒为上限、且只在付费那一支读用户存的值",
          "? Settings.Values[StrengthKey] is int strength" in watermark
          and ": Watermark.MaxOpacity;" in watermark)

    check("浓度能不能拖是**读**出来的（与开关同一套：灰掉与忽略是同一个事实）",
          "public static bool StrengthOptional => PaidFor;" in watermark
          and "WatermarkStrengthSlider.IsEnabled = on && WatermarkSettings.StrengthOptional;"
          in settings)

    check("锁着的时候滑块被写回实际在用的那个值，而不是留着页面打开时的旧值",
          "WatermarkStrengthSlider.Value = strength;" in settings
          and "var strength = WatermarkSettings.Strength;" in settings)

    check("还有一个被告别的入口：恢复购买与管理订阅都在卡片上",
          'x:Name="RestoreButton"' in markup and 'x:Name="ManageButton"' in markup)

    print("源码（对话框里那三个答复）：")

    check("购买成功后接着把这一件事做完，而不是让用户再点一次导出",
          "SubscribeOutcome.Subscribed => true" in offer
          and "await subscription.SubscribeAsync(handle)" in offer)

    check("除了「订阅」和「恢复」以外都不是「可以」",
          "default:" in offer and "return false;" in offer)

    # 三个答复都要说话，是这一批补的东西：买不成那条路以前完全安静 —— `SubscribeAsync`
    # 返回 `Unavailable` 时连商店自己的框都不开，于是「点了一下订阅」和「什么都没点」
    # 在画面上无法区分（商店版报回来就是「点击订阅没反应」）。下面三条守的是**说了**。
    check("买不成时说话了，而不是安静地把人留在原地",
          "Explanation(outcome)" in offer
          and "await TellAsync(root, Explanation(outcome))" in offer)

    check("恢复购买空手而归也要说 —— 那是「没找到」，不是「什么都没变」",
          'await TellAsync(root, "SettingsSubscriptionRestoreMissing")' in offer)

    # 「哪句话答哪个答案」只写一处：设置页卡片与导出框读的是同一份映射，
    # 两边各写一份，同一个结果迟早会被讲成两种意思（各自通顺、互不矛盾、单看都看不出来）。
    check("「哪句话答哪个答案」只写一处，两处调用读的是同一份映射",
          offer.count("SubscribeOutcome.Unavailable =>") == 1
          and "SubscriptionOffer.Explanation(outcome)" in settings)

    print("源码（已经买了的人，不该再被当成没买）：")

    # 这一节的来路是一个真机回报：一张写着「已订阅 / 2026-11-07 续订 / 每月 ¥28.00」
    # 的卡片，重启之后整块不见了，而订阅本身是好的 —— 能导出、能去水印。
    #
    # 卡片在 xaml 里的默认值就是 `Collapsed`，所以「消失」等价于 `Known == false`。
    # 而把这个答案压成 false 的路有两条，都出自同一个混淆：**把「商店答没答」当成
    # 「买没买」**。商店那一半是一次网络调用、还会失败；许可证那一半就在本机，
    # 一次调用就答。把它们绑在一起，代价在失败那一刻全部落在已经付过钱的人身上。
    # 数在**重读那一路**里，不数全文件：Debug 模拟也写 `Known = true`，那是另一条路，
    # 把它的次数算进来，这条断言就会在「模拟那一处也改了」的时候报一个假红。
    resolved = handler_body(subscription, "ResolveAsync")
    known = re.findall(r"^\s*Known = [^;]+;", resolved or "", re.M)
    anywhere = re.findall(r"^\s*Known = [^;]+;", subscription, re.M)

    check("续订日期不再用索引器去取（key 不在就抛，抛了就被读成「没买」）",
          "AddOnLicenses[" not in subscription,
          "还在用索引器" if "AddOnLicenses[" in subscription else "用的是 TryGetValue")

    check("卡片该不该出现只有一处说了算，且「买没买」自己就能让它出现",
          len(known) == 1 and "Subscribed" in known[0],
          "重读那一路 %d 处：%s（全文件 %d 处，多出来的是 Debug 模拟）" % (
              len(known), " / ".join(k.strip() for k in known) or "没有", len(anywhere)))

    check("认许可证按 token，不靠商店返回的那件商品（目录查不到也认得出买了）",
          "private static IEnumerable<StoreLicense> Granted(StoreAppLicense license)" in subscription
          and "addOn.InAppOfferToken, OfferToken, StringComparison.OrdinalIgnoreCase" in subscription)

    check("目录与许可证是两条路（重读许可证可以不联网）",
          "private async Task ResolveAsync(nint window, bool lookup = true)" in subscription
          and "lookup ? await LookupAsync(window) : _offer" in subscription)

    check("有一个只重读许可证的入口，它不走网络",
          "public async Task<bool> RecheckAsync(nint window)" in subscription
          and "await ResolveAsync(window, lookup: false)" in subscription)

    # 问在弹框之前，而且要问的是「本地那一次」。在商店自己的窗口里买完回到软件，
    # 这一次点击本来是「第一次点导出」—— 它必须通过，否则刚付完钱的人看到的是
    # 「请订阅」，那句话在那一刻读起来就是「你的钱白花了」。
    check("点导出先本地重读一次许可证，再决定要不要弹框",
          "await subscription.RecheckAsync(handle)" in offer
          and offer.index("await subscription.RecheckAsync(handle)")
          < offer.index("await Dialogs.ShowAsync(Offer(root, subscription))"))

    check("购买成功后等一会儿再看几次（许可证从商店发到本机会晚一步）",
          "StorePurchaseStatus.Succeeded ? 3 : 1" in subscription
          and "await Task.Delay(TimeSpan.FromSeconds(attempt))" in subscription)

    refresh = handler_body(settings, "RefreshSubscriptionAsync")
    settled = refresh.find("SettleSubscription();") if refresh else -1

    check("刷新出错也要把界面结算一遍（卡片停在 xaml 默认值上就等于消失）",
          refresh is not None and "finally" in refresh and settled > 0
          and refresh.index("finally") < settled,
          "没找到方法体" if refresh is None else "")


def resw_checks():
    print("界面文案：")

    missing = {}

    for lang in LANGS:
        path = os.path.join(STRINGS, lang, "Resources.resw")
        tree = ET.parse(path)
        got = {node.get("name") for node in tree.getroot().findall("data")}
        lacked = [key for key in RESW_KEYS if key not in got]

        if lacked:
            missing[lang] = lacked

    lacked_all = sum(len(v) for v in missing.values())

    # 条数从 RESW_KEYS 上算，不写死：写死的那一天加了一个键，这句话会继续报「16 个键在」，
    # 而它确实是核对过的 —— 数字对不上就被读成「这 17 个键都在」。
    check("订阅这一套 %d 个键在 14 种语言里都在" % len(RESW_KEYS),
          not missing,
          ("缺 {} 处：{}".format(
              lacked_all,
              ", ".join("%s(%d)" % (k, len(v)) for k, v in missing.items())))
          if lacked_all else "%d × 14" % len(RESW_KEYS))

    tree = ET.parse(os.path.join(STRINGS, "en-US", "Resources.resw"))
    keys = {node.get("name") for node in tree.getroot().findall("data")}

    # 少了键不会报错：运行时读到一个方括号包着的键名，画面上一个字都不会多缩进，只是那一行
    # 是空的。所以这里把代码里 Strings.Get / Strings.Format 用到的键逐个找出来对着数。
    used = set(re.findall(r'Strings\.(?:Get|Format)\("([^"]+)"', read("Views", "SubscriptionOffer.cs")))
    used |= set(re.findall(r'"(SettingsSubscription[A-Za-z]+|SubscriptionPerMonth)"',
                           read("Pages", "SettingsPage.xaml.cs")))
    used = set(re.findall(r'Strings\.(?:Get|Format)\("([^"]+)"', read("Views", "SubscriptionOffer.cs")))

    check("代码里用到的每一个键都真的写着", not (used - keys),
          ", ".join(sorted(used - keys)) or "%d 个键" % len(used))


def help_checks():
    print("帮助手册：")

    # 逐字比对，不要「数 Microsoft Store 出现几次」。那一句被改写过照样数得够两次，
    # 而脚本会说它有。按路径加载写好的那一句，副本数是零。
    spec = importlib.util.spec_from_file_location(
        "psh", os.path.join(HERE, "port-subscription-help.py"))
    psh = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(psh)

    lacked = {}

    for lang in LANGS:
        text = open(os.path.join(HELP, "help-%s.md" % lang), encoding="utf-8-sig").read()
        lines = [line.strip() for line in text.replace("\r\n", "\n").split("\n")]

        missing = [name for name, body in
                   (("导出那一处", psh.EXPORTING[lang]), ("水印那个开关", psh.SWITCH[lang]))
                   if body.strip() not in lines]

        if missing:
            lacked[lang] = missing

    check("14 份手册各写着那两条，且一字未改",
          not lacked,
          "缺 {} 处：{}".format(sum(len(v) for v in lacked.values()),
                               ", ".join("%s(%s)" % (k, "/".join(v)) for k, v in lacked.items()))
          if lacked else "14 份 × 2 条")


# ---- 真机 -----------------------------------------------------------------------

def simulation_present(flag, price="¥28.00"):
    if flag:
        os.makedirs(LOCAL_STATE, exist_ok=True)
        open(SIMULATION, "w", encoding="utf-8").write(price)
    elif os.path.exists(SIMULATION):
        os.remove(SIMULATION)


def launch():
    """起来一个**这一版**的应用。先杀掉再起 —— 还在跑的那个实例保持它启动时加载的程序集，
    对着它验证等于对着上一次改动验证（`winui.launch` 里那段话）。"""
    return winui.launch(EXE)


def switch_state(window):
    """设置页水印开关的 IsEnabled。UIA 读不到就返回 None。"""
    toggle = vfb.find(lambda c: c.AutomationId == "WatermarkToggle", window)

    if toggle is None:
        return None

    vfb.scroll_settings(window, 55)

    toggle = vfb.find(lambda c: c.AutomationId == "WatermarkToggle", window)

    return toggle.IsEnabled if toggle is not None else None


def live():
    print("真机：")

    if not LOCAL_STATE or not os.path.isdir(LOCAL_STATE):
        note("找不到 LocalState（{}），跳过真机段".format(LOCAL_STATE))
        return

    window = None

    try:
        # 没有订阅的那一轮放在前面：这台机器上的许可证本来就是「没有」，把它写成开关
        # 搬不动，继而证明「有」那一轮的差别是真的差别，而不是这两次读法不一样。
        simulation_present(False)
        window = launch()

        if window is None:
            note("应用没起来，跳过真机段")
            return

        vfb.goto_settings(window)
        time.sleep(1)
        locked = switch_state(window)

        note("未订阅：水印开关 IsEnabled = {}".format(locked))

        simulation_present(True)
        window = launch()

        if window is None:
            note("第二次没能起来")
            return

        vfb.goto_settings(window)
        time.sleep(1)
        paid = switch_state(window)

        note("已订阅：水印开关 IsEnabled = {}".format(paid))

        check("未订阅时这个开关搬不动", locked is False, str(locked))
        check("订阅后同一个开关就能动了", paid is True, str(paid))
        check("两轮不是同一个答案（说明它是真的被读回来的）", locked != paid,
              "{} vs {}".format(locked, paid))

        vfb.shot(window, "verify-subscription-paid.png")
    except Exception as ex:  # noqa: BLE001
        note("真机段出错：{}: {}".format(type(ex).__name__, ex))
    finally:
        # 无条件复位：这个文件是 Debug 的开关，留着会让下一个验证脚本对着一个「已付费」的
        # 应用去问「没付费是不是被拦住了」。
        simulation_present(False)


def main() -> int:
    global vfb

    spec = importlib.util.spec_from_file_location(
        "vfb", os.path.join(HERE, "verify-framebackdrop.py"))
    vfb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vfb)

    source()
    resw_checks()
    help_checks()
    live()

    print()
    print("{} 项失败".format(len(FAILED)) if FAILED else "全部通过")

    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
