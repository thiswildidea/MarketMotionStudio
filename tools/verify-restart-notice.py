# -*- coding: utf-8 -*-
r"""「换市场 / 换语言之后要重启」这句话，出来的时候看得见。

报的是：设置页里改了市场或语言，提示条**有时看不到**，像没生效。真因不是没画，是它画在**页面
最后一张卡片下面**——市场和语言是头两张卡，提示条在另外四张之后，改完那一眼根本不在同一屏。
现在它被钉在页面**最顶上**，不跟着滚动走，而且带着「立即重启」。

这一条判据验四件事，每件都要在**画面上**量到，源码里写对而画面没动是完全可能的：

1. 改市场 → 条子贴在窗口**顶部**，而且不在滚动区里；
2. 条子上写着「市场会在应用重启后生效。」，右边有「立即重启」；
3. 往下滚一屏之后，条子**还在原处**（位置不动，这才是「固定在最顶端」）；
4. 改语言 → 文案换成语言那一句。

**位置问控件，不问像素。** 条子有 UIA 节点，`BoundingRectangle` 就是它的位置，而且「在顶部」
判的是**比例**（< 窗口高的 20%）不是某个坐标：条子高度随语言和换行变，写死一个 y 是一条会被改
一次忘一次的东西。（早先这里扫「横贯窗口的浅灰带」，结果每次都答 `y=0` —— 窗口自己的顶边框就是
那么一条，「画在上半部」于是在**任何**情况下都通过，包括条子根本没画出来的时候。）

**「钉住」是双向的**，两条缺一条都说明不了问题：页面得**真滚了**（拿滚动区**里面**的市场下拉量，
它得往上走过几十像素），而条子得**没动**。只验前者，什么都没钉住也通过；只验后者，「滚动根本
没发生」会让它稳稳通过。

源码那半边（同一件事在 XAML 里怎么摆的）也读一遍：条子在 `ScrollViewer` **外面**才可能不跟着滚。

用法：python tools\verify-restart-notice.py
"""
import os
import sys
import time

sys.argv = [sys.argv[0]]
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import winui  # noqa: E402

XAML = os.path.join(REPO, "src", "MarketMotionStudio", "Pages", "SettingsPage.xaml")
CODE = os.path.join(REPO, "src", "MarketMotionStudio", "Pages", "SettingsPage.xaml.cs")

MARKET = "市场会在应用重启后生效。"
LANGUAGE = "语言会在应用重启后生效。"
RESTART = "立即重启"

# 这一台机器上界面是**日语**（实测导航项叫「設定」），所以不能按中文文案断言。
# 认的是**结构**：条子上有字、字里**没有**另一个设置项的名字、条子动过（内容换了）。
# 具体是哪一句由 `Note` 一处决定，源码那半边已经判过（见下）。

results = []


def check(name, ok, note=""):
    results.append((name, ok))
    print(f"  {'✓' if ok else '✗'} {name}" + (f"  — {note}" if note else ""))


def report():
    failed = [n for n, ok in results if not ok]

    print()

    if failed:
        print(f"{len(failed)} 项未通过：" + "、".join(failed))
    else:
        print(f"全部通过（{len(results)} 项）")

    return 0 if not failed else 1


def texts(win, limit=4000):
    return [c.Name for c in winui.find_all(win, lambda c: c.Name, limit=limit) if c.Name]


def bar_texts(win):
    """提示条里那几行字。按 AutomationId 认，不按位置。"""
    bar = winui.find(win, lambda c: c.AutomationId == "RestartNotice")

    if bar is None:
        return None, []

    return bar, texts(bar)


def goto_settings(win):
    """切到设置页。

    **按 `AutomationId` 认，不按名字。** 导航项的名字跟着界面语言变（实测这一台是日语，
    项名是「設定」），所以按名字找就得列一列语言，而列漏一种就是「找不到导航项」——
    一个和被测代码毫无关系的失败。`NavSettingsItem` 是它在 XAML 里就定下的，和语言无关。

    **点它走 `winui.invoke_click`，不是 `GetInvokePattern()`。** 导航项在 UIA 里是
    `ListItemControl`，答的是 `SelectionItemPattern`：只试 Invoke 就是一下都没点着，
    而失败的样子是「导航里没有设置页」—— 控件每一次都在，点不动而已。
    """
    item = winui.find(win, lambda c: c.AutomationId == "NavSettingsItem")

    if item is None:
        return False

    if not winui.invoke_click(item, settle=0.8):
        return False

    # 点完导航不等于这一页的控件都建好了。等真正的控件出现，而不是睡一个猜出来的时长。
    deadline = time.time() + 30

    while time.time() < deadline:
        if winui.find(win, lambda c: c.AutomationId == "RestartNotice") is not None:
            return True

        time.sleep(0.4)

    return False


def pick(win, combo_id, wanted):
    """在下拉里选一项。返回是否真的选到了。"""
    combo = winui.find(win, lambda c: c.AutomationId == combo_id)

    if combo is None:
        return False

    return winui.combo_pick(win, combo, wanted)


def snapshot(win, name):
    """设置页的一张图。

    **走 `winui.shot`，不是 `winui.capture`。** `capture` 要图里有块画布才认账（它本来是给
    预览画面用的），而设置页没有画布 —— 用它就是重试四次然后报「抓不到设置页」，
    页面一直都在。这里认的是「这张图是本窗口的尺寸」。
    """
    from PIL import Image

    path = os.path.join(REPO, "artifacts", name)

    if not winui.shot(win, path):
        return None

    return Image.open(path).convert("RGB")


def pick_index(win, combo_id, index):
    """按**位置**选下拉里的一项，返回选到的那一项的文本。

    这一页上界面语言可能是日语或别的语言（实测这一台是日语），所以不能按中文项名选。
    位置是稳定的：市场和语言两项的数量与顺序由代码写定，不随语言变。
    """
    combo = winui.find(win, lambda c: c.AutomationId == combo_id)

    if combo is None:
        return None

    labels = winui.combo_labels(win, combo)

    if index >= len(labels):
        return None

    return labels[index] if winui.combo_pick(win, combo, labels[index]) else None


def top_of(win, control):
    """控件的顶边在**窗口里**的 y（不是屏幕坐标）。量不到返回 None。

    **量矩形，不扫像素。** 早先这里扫的是「横贯窗口的浅灰带」，结果每一次都答 `y=0` ——
    窗口自己的顶边框就是那么一条，于是「条子画在窗口上半部」在**任何**情况下都通过，
    包括条子根本没画出来的时候。条子是有 UIA 节点的，位置就该问它；只有预览画布那种
    没有节点的东西才需要去数像素。
    """
    if control is None:
        return None

    try:
        return control.BoundingRectangle.top - win.BoundingRectangle.top
    except Exception:  # noqa: BLE001
        return None


def main():
    xaml = open(XAML, encoding="utf-8").read()
    code = open(CODE, encoding="utf-8").read()

    print("源码")

    # 结构判据：条子在 ScrollViewer **外面**。写成它在 StackPanel 末尾时，它就跟着滚走了 ——
    # 那时「固定在顶端」这条要求等于没做，而画面上前几帧看起来一模一样。
    scroller = xaml.split("<ScrollViewer", 1)

    check("提示条不在滚动区里面（它是钉在顶上的）",
          len(scroller) == 2 and "RestartNotice" not in scroller[1].split("</ScrollViewer>")[0],
          "RestartNotice 在 ScrollViewer 内" if len(scroller) < 2 else "")

    check("提示条在滚动区之前（页面第一条）",
          "RestartNotice" in xaml.split("<ScrollViewer", 1)[0])

    # 一个判断十七处提问：条子的样子只由 `Note` 一处决定，按钮的可视与否也是。
    check("按钮的可视与否只在一处决定（和那句话绑在一起）",
          code.count("ActionButton.Visibility") == 1,
          f"{code.count('ActionButton.Visibility')} 处")

    check("市场与语言都走这一处",
          'Strings.Get("SettingsMarketRestart.Text"), restart: true' in code
          and 'Strings.Get("SettingsLanguageRestart.Text"), restart: true' in code)

    check("重启失败也走这一处（按钮跟着收起来）",
          'Note(InfoBarSeverity.Error, Strings.Format("SettingsRestartFailed", failure));' in code)

    print("\n真机")

    win = winui.launch(winui.EXE)

    if win is None:
        check("应用起得来", False)
        return report()

    check("应用起得来", True)

    if not goto_settings(win):
        check("导航里找得到设置页（按 AutomationId）", False)
        return report()

    check("导航里找得到设置页（按 AutomationId）", True)

    bar = winui.find(win, lambda c: c.AutomationId == "RestartNotice")

    check("提示条这个控件找得到（打一开始就在树里）", bar is not None)

    if bar is None:
        return report()

    # 初始：没改过任何东西，条子应当是关着的 —— 一个一进设置页就弹「要重启」的条子，
    # 会让人以为设置坏了。
    _, opened = bar_texts(win)

    check("一进页面条子是关着的", not opened, f"已有内容：{opened[:2]}")

    initial = snapshot(win, "verify-restart-notice-initial.png")

    # ---- 改市场 -------------------------------------------------------------
    #
    # 不选「港股」这个名字（语言一变就对不上），改成**选到别的某一项**：
    # `MarketCombo` 的第一项就是当前市场，所以选第 2 项一定是「换了一个」。
    options = winui.combo_labels(win, winui.find(win, lambda c: c.AutomationId == "MarketCombo"))

    check("市场下拉里至少有两个市场可选", len(options) >= 2, f"{options}")

    chosen = pick_index(win, "MarketCombo", 1)

    check("市场下拉换成了另一项", chosen is not None and chosen != options[0] if options else False,
          f"选到 {chosen!r}（原来 {options[0] if options else '?'!r}）")

    time.sleep(1.2)

    _, lines = bar_texts(win)
    joined = " ".join(lines)

    check("改市场后条子出来了", bool(lines), f"{lines[:3]}")
    check("条子上的字不是空的", len(joined.strip()) > 4, joined[:80])

    image = snapshot(win, "verify-restart-notice-market.png")

    check("抓得到设置页", image is not None)

    # 「在最顶端」这一半：条子的顶边离窗口顶边很近。
    #
    # 判的是**比例不是坐标**：条子多高随语言和换行变，写死一个 y 就是一条会被改一次忘一次
    # 的东西。20% 是「一眼就看得见」的意思 —— 它原来是页面最后一张卡片，在另外四张之后。
    bar_top = top_of(win, bar)
    tall = None

    try:
        tall = win.BoundingRectangle.bottom - win.BoundingRectangle.top
    except Exception:  # noqa: BLE001
        tall = None

    check("条子贴在窗口顶部（不滚下去就看得见）",
          bar_top is not None and tall and bar_top < 0.20 * tall,
          f"条子顶边 y={bar_top}，窗口高 {tall}")

    # 条子上那个按钮：按 `InvokePattern` 存在的按钮找，且它的父级就是这条 InfoBar。
    buttons = [c for c in winui.find_all(bar, lambda c: c.ControlTypeName == "ButtonControl",
                                         limit=20)]

    check("条子上带着一个按得动的按钮（立即重启）", len(buttons) >= 1,
          f"{[c.Name for c in buttons]}")
    check("那个按钮是可见的（不是留了个空位）",
          bool(buttons) and buttons[0].IsOffscreen is False,
          f"IsOffscreen={buttons[0].IsOffscreen}" if buttons else "")

    # ---- 滚动之后还在原处 ---------------------------------------------------
    #
    # 「固定在最顶端」这一半。两条一起才说明它是钉住的，而不是「恰好一开始在上边」：
    # 画面**确实滚了**（内容变了），而条子还在同一行。
    #
    # 滚动容器**按「能滚」找，不按名字找**：设置页那个滚动区在 UIA 里是 PaneControl、
    # 名字是空的，按 `AutomationId` 或 `ScrollViewerControl` 找都找不着 —— 找不着就等于
    # 没滚，于是「滚动之后条子还在原处」会在一条根本没滚过的页面上通过。
    #
    # 拿**市场下拉**当「在里面」的那个：条子自己现在是滚动区的**外面**（这正是这次改动
    # 的目的），拿它去找滚动区必然一个也找不着，而那会把「真钉住了」读成「找不到滚动区」。
    inside = winui.find(win, lambda c: c.AutomationId == "MarketCombo")
    scroller = winui.scrollable(win, inside=inside)
    combo_before = top_of(win, inside)

    check("页面里找得到装得下市场下拉的那个滚动层", scroller is not None)

    scrolled = False

    if scroller is not None:
        try:
            pattern = scroller.GetPattern(winui.auto.PatternId.ScrollPattern)

            if pattern is not None:
                pattern.SetScrollPercent(-1, 70)
                time.sleep(1.5)
                scrolled = True
        except Exception:  # noqa: BLE001
            scrolled = False

    check("设置页滚得动（滚到 70%）", scrolled)

    after = snapshot(win, "verify-restart-notice-scrolled.png")

    check("滚动后抓得到画面", after is not None and image is not None)

    # 双向验，两条缺一条都说明不了「钉住」：
    #
    # 1. **页面确实滚了** —— 用滚动区**里面**的市场下拉量：它得往上走过几十像素。
    #    判它比判「两帧平均亮度差了多少」实在：亮度差是个没有对照的阈值，页面里九成是
    #    面板，差 6 个点也可能只是标题换了一行。
    # 2. **条子没跟着走** —— 同一个条子的顶边，前后差在两个像素以内。
    #
    # 只验第 2 条时，「滚动根本没发生」会让这条稳稳通过；只验第 1 条则什么都没钉住也通过。
    combo_after = top_of(win, inside)
    bar_after = top_of(win, bar)

    check("页面确实滚了（滚动区里的市场下拉往上走了）",
          combo_before is not None and combo_after is not None
          and abs(combo_after - combo_before) >= 40,
          f"市场下拉 y {combo_before} → {combo_after}")

    _, still = bar_texts(win)

    check("滚动之后条子的字还在（没被滚出去）", bool(still), f"{still[:3]}")

    check("条子没跟着滚（前后同一个 y）",
          bar_top is not None and bar_after is not None and abs(bar_after - bar_top) <= 2,
          f"条子 y {bar_top} → {bar_after}")

    # ---- 改语言（条子换成另一句） -------------------------------------------
    #
    # 不判具体是哪一句（这一台界面是日语，中文原文对不上），判的是**它换过了** ——
    # `Note` 那一处传的是 `SettingsLanguageRestart.Text`，源码那半边已经判过。
    before_text = " ".join(bar_texts(win)[1])
    langs = winui.combo_labels(win, winui.find(win, lambda c: c.AutomationId == "LanguageCombo"))

    if len(langs) >= 2 and pick_index(win, "LanguageCombo", 1):
        time.sleep(1.2)
        after_text = " ".join(bar_texts(win)[1])

        check("改语言后条子的字换了一句（不是市场那一句了）",
              bool(after_text) and after_text != before_text,
              f"{before_text[:40]!r} → {after_text[:40]!r}")

        check("换成语言那一句之后，按钮还在（重启同样管用）",
              winui.find(bar, lambda c: c.ControlTypeName == "ButtonControl") is not None)

        # 复位：语言也改回第一项（`LanguageCombo` 第一项是「跟随 Windows」）。
        pick_index(win, "LanguageCombo", 0)
        time.sleep(0.8)
    else:
        check("语言下拉里至少有两项可选", False, f"{langs}")

    # 复位：滚回去、市场改回原来那一项。
    if scroller is not None:
        try:
            scroller.GetPattern(winui.auto.PatternId.ScrollPattern).SetScrollPercent(-1, 0)
            time.sleep(0.8)
        except Exception:  # noqa: BLE001
            pass

    if options:
        pick_index(win, "MarketCombo", 0)
        time.sleep(0.8)

    winui.kill(winui.EXE)

    return report()


if __name__ == "__main__":
    sys.exit(main())
