# -*- coding: utf-8 -*-
"""帮助手册改成"先取网站上那份，取不到用包里那份"：三件事分别证明。

为什么三层都要
    只读源码证明不了它真的走了网络那条路；只看真机又证明不了站点上那份与包里
    那份是同一份（两边都画得出来，画的却不是同一本，谁也不知道）。所以：

    一、站点上确实有应用会去取的那 14 份文档和它们点名的每一张图，而且与包里
        那份**逐字节相同**。这是"一处写、两处对得上"那条；少了它，网站上少一
        句多一句没人发现。

    二、代码里确实是"先取网站、取不到用包里那份"，而且包内那份还在（离线兜底
        的材料没被搬走）。

    三、真机：把包内那份**藏起来**，帮助页仍然画得出整本手册**和它的配图**。
        这一条是"先取网站"的实证 —— 只读源码证明不了它真的走了那条路。先量
        一遍基准，藏起来再量一遍，两次数出来的字与图必须一样；量完立刻放回。

用法：
  python tools/verify-help-online.py                # 一 + 二（不需要应用在跑）
  python tools/verify-help-online.py --on-machine   # 再加真机那一段
"""

import importlib.util
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "src", "MarketMotionStudio", "Pages", "HelpDocument.cs")
HELP = os.path.join(ROOT, "src", "MarketMotionStudio", "Assets", "Help")
STRINGS = os.path.join(ROOT, "src", "MarketMotionStudio", "Strings")
AWAY = ".away-verify-help-online"

PASSED = []
FAILED = []


def load(path):
    """按路径加载，不复制别人脚本里的常量。"""
    name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    loaded = importlib.util.module_from_spec(spec)
    saved, sys.argv = sys.argv, [name]

    try:
        spec.loader.exec_module(loaded)
    finally:
        sys.argv = saved

    return loaded


def check(ok, what):
    (PASSED if ok else FAILED).append(what)
    return ok


def get(url, timeout=30):
    request = urllib.request.Request(url, headers={"User-Agent": "MarketMotionStudio/0.1"})

    with urllib.request.urlopen(request, timeout=timeout) as answer:
        return answer.status, answer.headers.get("Content-Type", ""), answer.read()


def resw(folder, key):
    """一个资源键，某个语言下的值。"""
    path = os.path.join(STRINGS, folder, "Resources.resw")
    node = ET.parse(path).getroot().find("./data[@name='%s']/value" % key)
    return (node.text or "").strip() if node is not None else None


def nav_names(key):
    """导航项的本地化名字 —— 十四个都取上，界面停在哪一种语言都能找到。"""
    names = []

    for folder in sorted(os.listdir(STRINGS)):
        if not os.path.isdir(os.path.join(STRINGS, folder)):
            continue
        value = resw(folder, key)
        if value and value not in names:
            names.append(value)

    return names


def source_checks():
    """二：顺序与兜底，读源码定。"""
    text = open(SOURCE, encoding="utf-8-sig").read()

    found = re.search(r'private const string Remote = "([^"]+)"', text)
    check(found is not None, "HelpDocument.cs 里找不到 Remote")
    remote = found.group(1) if found else None

    check(re.search(r"RemoteWait = TimeSpan\.FromSeconds\((\d+)\)", text) is not None,
          "找不到取网站的超时（RemoteWait）")

    fetch = text.find("await PublishedAsync(")
    packed = text.find('Path.Combine(AppContext.BaseDirectory, "Assets", "Help"')
    check(fetch > 0 and packed > 0 and fetch < packed,
          "源码里取网站那段没有排在读包内那份之前")

    check("File.Exists(path) ? await File.ReadAllTextAsync(path) : null" in text,
          "取不到网站时读包内那份这一句不在了")
    check("if (Readable(text))" in text, "没有对取回来的内容做是不是文档的判断")
    check("if (_published)" in text and "_published = true;" in text,
          "配图没有跟着文档的来源走（_published）")

    return remote


def site_checks(remote):
    """一：站点上那份与包里那份逐字节相同，图也都在。"""
    publish = load(os.path.join(ROOT, "tools", "publish-help-to-support.py"))
    languages = publish.languages()

    documents = 0
    pictures = 0

    for language, name in languages:
        packed = open(os.path.join(HELP, name), "rb").read()

        try:
            status, kind, body = get(remote + name)
        except urllib.error.HTTPError as problem:
            check(False, "%s 站点上取不到：HTTP %s" % (name, problem.code))
            continue
        except Exception as problem:  # noqa: BLE001
            check(False, "%s 站点上取不到：%s" % (name, type(problem).__name__))
            continue

        check(status == 200, "%s 站点上回的 %s" % (name, status))
        check("html" not in kind.lower(), "%s 站点上回的是一页 HTML（%s）" % (name, kind))
        check(body.replace(b"\r\n", b"\n") == packed.replace(b"\r\n", b"\n"),
              "%s 站点上那份与包内那份不一样" % name)
        documents += 1

        for reference in publish.pictures(os.path.join(HELP, name)):
            found, relative = publish.picture_file(HELP, language, reference)

            if not check(found is not None, "%s 引用的 %s 包里没有" % (name, reference)):
                continue

            try:
                status, kind, body = get(remote + relative)
            except Exception as problem:  # noqa: BLE001
                check(False, "%s 站点上取不到：%s" % (relative, type(problem).__name__))
                continue

            check(status == 200, "%s 站点上回的 %s" % (relative, status))
            check("image" in kind.lower(), "%s 站点上回的不是图片（%s）" % (relative, kind))
            check(len(body) == os.path.getsize(found),
                  "%s 站点上那张 %d 字节，包里那张 %d 字节"
                  % (relative, len(body), os.path.getsize(found)))
            pictures += 1

    print("站点：%d 份文档、%d 张图与包内那份逐字节相同" % (documents, pictures))
    return documents, pictures


def deployed():
    """已注册的那个松散布局里的 Assets/Help。"""
    base = os.path.join(ROOT, "src", "MarketMotionStudio", "bin")

    for path, _, _ in os.walk(base):
        if os.path.basename(path) == "Help" and os.path.isfile(
                os.path.join(path, "..", "..", "AppxManifest.xml")):
            return os.path.abspath(path)

    return None


def hide(help_folder, document, picture_folder):
    """把包内那份挪开，返回怎么放回去。"""
    moved = []

    for relative in (document, os.path.join("media", picture_folder)):
        source = os.path.join(help_folder, relative)
        if os.path.exists(source):
            os.rename(source, source + AWAY)
            moved.append(source)

    return moved


def unhide(moved):
    for source in moved:
        if os.path.exists(source + AWAY):
            os.rename(source + AWAY, source)


def counts(winui, win):
    """帮助页上的字与图各有多少 —— 手册没画出来时只剩一句话。"""
    text = len(winui.find_all(win, lambda c: c.ControlTypeName == "TextControl"))
    images = len(winui.find_all(win, lambda c: c.ControlTypeName == "ImageControl"))
    return text, images


def press_nav(auto, winui, win, candidates, what):
    """候选名字里**点得动的那一个** —— 点到就走。

    设置项没有 AutomationId（页脚项在 UIA 里就是空的），只能按名字找，于是十四种语言
    的名字都列上。界面只可能是其中一种，其余十三种都不在树上 —— 所以是「点到第一个在
    的就走」，不是「每一个都要点到」。

    头一版写成了挨个要求它们全在：候选表按 resw 目录的顺序列，捷克语 'Nastavení' 排
    第一，界面不是捷克语 —— 于是真机段报「帮助页没打开」，底下两条「段数/图数对不上」
    根本没机会跑（2026-10-10 头一次跑）。改成「点到就走」时又差点写成只点一次：那样只
    点了设置页就返回，帮助页根本没去 —— 所以这里是**一趟点一个**，由调用方点两回。
    """
    for wanted in candidates:
        item = None

        for _ in range(8):
            item = winui.find(
                win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == wanted)

            if item is not None:
                break

            time.sleep(2)

        if item is None:
            continue

        # 名字在读之前就取成了值：控件一消失，读 Name 会抛 COMError，而失败分支
        # 里抛异常会把"失败了"这句话本身也吞掉。
        for pattern_id in (auto.PatternId.InvokePattern, auto.PatternId.SelectionItemPattern):
            try:
                handle = item.GetPattern(pattern_id)
            except Exception:  # noqa: BLE001
                handle = None

            if handle is None:
                continue

            try:
                handle.Invoke() if pattern_id == auto.PatternId.InvokePattern else handle.Select()
                time.sleep(3)
                return True
            except Exception:  # noqa: BLE001
                pass

        try:
            item.Click(simulateMove=False, waitTime=0.5)
            time.sleep(3)
            return True
        except Exception:  # noqa: BLE001
            print("  ! 导航项点不动：%r" % wanted)
            return False

    print("  ! %s：%d 个候选名字一个都不在树上（%s…）" % (what, len(candidates), candidates[:3]))
    return False


def open_help(auto, winui, win, names):
    """去设置页再回帮助页：同一页不重建，回来的那一趟才会重新读文档。"""
    return (press_nav(auto, winui, win, nav_names("NavSettingsLabel.Text"), "设置页")
            and press_nav(auto, winui, win, names, "帮助页"))


def ensure_language(auto, winui, win):
    """把界面设成简体中文并重启。返回重启后的窗口。

    这一趟要看的正是 `help-zh-Hans.md`，所以界面**必须**是简体中文 —— 界面停在别的语言
    上时，帮助页读的是另一种手册，藏起来的那份根本没人读，于是「藏起来之后段数没变」
    照样通过，而它什么也没证明。语言改完要重启才生效，所以这里自己重启一次。
    """
    if not press_nav(auto, winui, win, nav_names("NavSettingsLabel.Text"), "设置页"):
        return None

    combo = winui.find(win, lambda c: c.AutomationId == "LanguageCombo")

    if combo is None:
        print("  ! 设置页里没有 LanguageCombo")
        return None

    print("语言下拉选了：%r" % winui.combo_pick(win, combo, "简体中文"))

    return winui.launch("MarketMotionStudio.exe")


def machine_checks():
    """三：藏起包内那份，帮助页仍然画得出整本手册和它的配图。"""
    auto = importlib.import_module("uiautomation")
    winui = load(os.path.join(ROOT, "tools", "winui.py"))
    help_folder = deployed()

    if not check(help_folder is not None, "找不到已注册布局里的 Assets/Help"):
        return

    names = nav_names("NavHelp.Content")
    check(len(names) >= 13, "NavHelp.Content 只取到 %d 个名字" % len(names))

    document = resw("zh-Hans", "HelpDocument")
    language = document[len("help-"):-len(".md")]
    print("真机：%s，文档 %s，配图目录 %s" % (help_folder, document, language))

    win = winui.launch("MarketMotionStudio.exe")

    if not check(win is not None, "应用没起来"):
        return

    # 界面必须先切到简体中文：藏起来的是 help-zh-Hans.md，界面停在别的语言上时这一段
    # 量的就是另一本手册，断言照样过而什么也没证明。切完自己重启一次。
    win = ensure_language(auto, winui, win)
    title = resw("zh-Hans", "AppDisplayName")

    if not check(win is not None, "没能切到简体中文"):
        return

    check(win.Name == title,
          "窗口标题是 %r，简体中文应当是 %r —— 量的不是这一本手册" % (win.Name, title))

    check(open_help(auto, winui, win, names), "帮助页没打开")

    base_text, base_images = counts(winui, win)
    print("基准（包内那份还在）：%d 段文字、%d 张图" % (base_text, base_images))
    check(base_text > 30, "基准只有 %d 段文字 —— 手册本来就没画出来" % base_text)
    check(base_images >= 5, "基准只有 %d 张图 —— 手册的配图本来就没画出来" % base_images)

    winui.capture(win, os.path.join(ROOT, "artifacts", "help-online-1-baseline.png"))

    moved = hide(help_folder, document, language)
    check(len(moved) == 2, "只藏起了 %d 处（应当两处：文档与配图目录）" % len(moved))
    print("藏起：" + "、".join(os.path.basename(m) for m in moved))

    try:
        win = winui.launch("MarketMotionStudio.exe")
        check(win is not None, "藏起包内那份之后应用没起来")

        if win is not None:
            check(open_help(auto, winui, win, names), "帮助页没打开（藏起来之后）")

            # 失败分支里不读控件的名字/属性：那一刻面板可能已经不在了。
            text, images = counts(winui, win)
            print("藏起包内那份之后：%d 段文字、%d 张图" % (text, images))

            check(text == base_text,
                  "藏起来之后有 %d 段文字，基准是 %d 段 —— 手册是从包里读的，不是网站上" % (text, base_text))
            check(images == base_images,
                  "藏起来之后有 %d 张图，基准是 %d 张 —— 配图不是从网站上取的" % (images, base_images))

            winui.capture(win, os.path.join(ROOT, "artifacts", "help-online-2-packaged-hidden.png"))
    finally:
        unhide(moved)

    print("放回：" + "、".join(os.path.basename(m) for m in moved))

    win = winui.launch("MarketMotionStudio.exe")

    if win is not None and open_help(auto, winui, win, names):
        text, images = counts(winui, win)
        print("放回之后：%d 段文字、%d 张图" % (text, images))
        check(text == base_text, "放回之后文字数与基准不同（%d vs %d）" % (text, base_text))
        check(images == base_images, "放回之后图数与基准不同（%d vs %d）" % (images, base_images))


def main():
    remote = source_checks()
    print("源码：Remote = %s" % remote)

    if remote:
        site_checks(remote)

    if "--on-machine" in sys.argv:
        machine_checks()

    print("%d 项通过，%d 项失败" % (len(PASSED), len(FAILED)))

    for what in FAILED:
        print("  ! %s" % what)

    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
