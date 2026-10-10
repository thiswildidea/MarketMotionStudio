# -*- coding: utf-8 -*-
"""把应用"看起来的样子"复位成默认，截完再按原样放回去。

为什么需要
    截图要拍的是**应用默认的样子**，而这台机器上攒着两次试验留下的偏好：

      * 窗口背景图（设置页「背景图」）—— 选上之后面板会一起变半透明
        （AppBackground.ApplySurfaces），于是那张图会出现在**每一张**截图里；
      * 帧背景（设置页「帧背景」）—— 预览、导出视频、封面都用它，默认是页
        面自带的那条深色渐变，改成别的颜色/图片之后，帮助文档里每一张配图的
        9:16 画面都跟着变。

    两个都是 10-07 那轮改外观时留下的。2026-10-10 重截帮助配图时，七十张图
    整扇窗都是那张壁纸、帧里是一团橙色漩涡 —— 看起来像"窗口没画背景"，其实
    只是偏好没改回去。

    规矩是自己的：「动了哪个偏好最后无条件改回」。所以这里把"原来是什么"
    落盘，用完 restore —— 复位是截图的必要条件，但这些是用户的设置。

用法：
  python tools/drive-look.py status    # 三处现在各是什么
  python tools/drive-look.py clean     # 复位成默认（先记下原来是什么）
  python tools/drive-look.py restore   # 按记下的放回去
"""

import json
import os
import subprocess
import sys
import time

import uiautomation as auto

APPID = "8166Yxw.MarketMotionStudio_fzc58jprbah1t!App"
EXE = "MarketMotionStudio.exe"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "artifacts", "look-before.json")

# 设置项在页脚、AutomationId 为空时按名称找；找的时刻界面可能还是别的语言，
# 所以把十四种都列上（与 store-screenshots.py 同一张表）。
SETTINGS_NAMES = [
    "设置", "設定", "Settings", "Nastavení", "Einstellungen", "Configuración",
    "Paramètres", "Impostazioni", "Ustawienia", "Configurações", "Ayarlar",
    "Параметры", "설정",
]

# 帧背景的种类下拉，顺序即 SettingsPage.FrameBackdropKinds（0=默认 1=颜色 2=图片）。
# 按下标选是因为 UIA 读不回 ComboBox 的选中项，只好选完看**副作用**：选“颜色”
# 会露出两个色板按钮，选“图片”会露出画廊，选“默认”两个都不在树里。
FRAME_DEFAULT = 0


def find(condition, root, depth=0, limit=25):
    if depth > limit:
        return None
    try:
        if condition(root):
            return root
    except Exception:
        return None
    try:
        for child in root.GetChildren():
            hit = find(condition, child, depth + 1, limit)
            if hit is not None:
                return hit
    except Exception:
        pass
    return None


def pattern(control, pattern_id):
    try:
        return control.GetPattern(pattern_id)
    except Exception:
        return None


def press(control):
    for which in (auto.PatternId.InvokePattern, auto.PatternId.SelectionItemPattern):
        handle = pattern(control, which)
        if handle is None:
            continue
        try:
            handle.Invoke() if which == auto.PatternId.InvokePattern else handle.Select()
            time.sleep(0.6)
            return True
        except Exception:
            pass
    try:
        control.Click(simulateMove=False, waitTime=0.6)
        return True
    except Exception:
        return False


def combo_pick(combo, index, timeout=8):
    handle = pattern(combo, auto.PatternId.ExpandCollapsePattern)
    if handle is None:
        return False
    try:
        handle.Expand()
    except Exception:
        return False
    deadline = time.time() + timeout
    while time.time() < deadline:
        items = [c for c in combo.GetChildren() if c.ControlTypeName == "ListItemControl"]
        if len(items) > index:
            select = pattern(items[index], auto.PatternId.SelectionItemPattern)
            if select is not None:
                select.Select()
                time.sleep(0.6)
                try:
                    handle.Collapse()
                except Exception:
                    pass
                return True
        time.sleep(0.4)
    try:
        handle.Collapse()
    except Exception:
        pass
    return False


def pids():
    result = subprocess.run(
        ["tasklist", "/FO", "CSV", "/FI", "IMAGENAME eq " + EXE], capture_output=True)
    text = result.stdout.decode("utf-8", "replace")
    return {
        int(row.split('","')[1].strip('"'))
        for row in text.splitlines()[1:]
        if EXE.lower() in row.lower()
    }


def window(timeout=40):
    deadline = time.time() + timeout
    while time.time() < deadline:
        for candidate in auto.GetRootControl().GetChildren():
            try:
                if candidate.ControlTypeName == "WindowControl" and candidate.ProcessId in pids():
                    return candidate
            except Exception:
                pass
        time.sleep(1)
    return None


def open_settings():
    """把应用带到设置页，交回窗口。已经开着就不再启动一个。"""
    if not pids():
        os.startfile(r"shell:AppsFolder\%s" % APPID)
        time.sleep(5)

    win = window()
    assert win is not None, "窗口未找到"

    win.SetActive()
    win.MoveWindow(60, 60, 1500, 940)
    time.sleep(1.5)

    for name in SETTINGS_NAMES:
        nav = find(lambda c: c.ControlTypeName == "ListItemControl" and c.Name == name, win)
        if nav is not None:
            press(nav)
            time.sleep(2)
            return win

    raise AssertionError("设置导航项未找到")


def id_of(win, automation_id):
    return find(lambda c: c.AutomationId == automation_id, win)


def selected(gallery):
    """(第几项, 项的名字)；没选中就是 (None, None)。

    画廊项是 Image，界面上只有"第几张"这个名字（SettingsBackgroundThumb /
    …WindowsThumb 带序号），文件路径没有暴露给 UIA。所以身份只能按位置记，
    再连同名字一起写下 —— 一个位置单独放着，下次列表里多一张图就指错了。
    """
    for index, item in enumerate(gallery.GetChildren()):
        handle = pattern(item, auto.PatternId.SelectionItemPattern)
        try:
            if handle is not None and handle.IsSelected:
                return index, item.Name
        except Exception:
            continue
    return None, None


def look(win):
    """三处现在各是什么：窗口背景图 / 帧背景种类 / 帧背景图。"""
    window_gallery = id_of(win, "BackgroundGallery")
    window_clear = id_of(win, "ClearBackgroundButton")
    combo = id_of(win, "FrameBackdropCombo")
    frame_gallery = id_of(win, "FramePictureGallery")
    colour_button = id_of(win, "TopColourButton")

    assert window_clear is not None, "ClearBackgroundButton 未找到（AutomationId 变了？）"
    assert combo is not None, "FrameBackdropCombo 未找到"

    # 种类看的是"哪一组控件在树里"：折叠的控件不进 UIA 树。
    kind = 2 if frame_gallery is not None else (1 if colour_button is not None else FRAME_DEFAULT)

    window_index, window_name = selected(window_gallery) if window_gallery is not None else (None, None)
    frame_index, frame_name = selected(frame_gallery) if frame_gallery is not None else (None, None)

    return {
        "window_picture": window_index,
        "window_picture_name": window_name,
        "frame_kind": kind,
        "frame_picture": frame_index,
        "frame_picture_name": frame_name,
    }


def describe(state):
    window = ("第 %d 项（%s）" % (state["window_picture"] + 1, state["window_picture_name"])
              if state["window_picture"] is not None else "没选")
    kinds = {0: "默认", 1: "颜色", 2: "图片"}
    frame = kinds[state["frame_kind"]]
    if state["frame_kind"] == 2:
        frame += "（第 %s 项）" % (state["frame_picture"] + 1
                                  if state["frame_picture"] is not None else "没选")
    return "窗口背景图 %s；帧背景 %s" % (window, frame)


def clean(win, state):
    """复位成默认，每一步都看副作用，不看点击返回值。

    Click 在矩形为空时（控件被滚出视野/面板重建）会静默跳过却照常返回成功，
    所以判据一律取"点完之后控件自己的状态"。
    """
    if state["window_picture"] is not None:
        press(id_of(win, "ClearBackgroundButton"))
        clear = id_of(win, "ClearBackgroundButton")
        for _ in range(10):
            if clear is not None and not clear.IsEnabled:
                break
            time.sleep(0.5)
        assert clear is not None and not clear.IsEnabled, "点了「清除」，清除按钮还是可用的 —— 背景图还在"

    if state["frame_kind"] != FRAME_DEFAULT:
        assert combo_pick(id_of(win, "FrameBackdropCombo"), FRAME_DEFAULT), "帧背景种类没选中「默认」"
        time.sleep(1)

        assert id_of(win, "FramePictureGallery") is None, "选了「默认」，但帧背景画廊还在树里"
        assert id_of(win, "TopColourButton") is None, "选了「默认」，但色板按钮还在树里"


def restore(win, state):
    """按记下的放回去，每一处都确认到位。"""
    if state["frame_kind"] != FRAME_DEFAULT:
        assert combo_pick(id_of(win, "FrameBackdropCombo"), state["frame_kind"]), "帧背景种类没选回去"
        time.sleep(1)

        group = "FramePictureGallery" if state["frame_kind"] == 2 else "TopColourButton"
        assert id_of(win, group) is not None, "帧背景选回去了，但 %s 没出来" % group

    if state["frame_picture"] is not None:
        gallery = id_of(win, "FramePictureGallery")
        items = gallery.GetChildren()
        want = state["frame_picture"]
        assert len(items) > want, "帧背景画廊里只剩 %d 项，原来那项（第 %d 项）不在了" % (len(items), want + 1)
        press(items[want])
        time.sleep(1)
        index, name = selected(gallery)
        assert index == want, "帧背景选回去的是第 %s 项，记下来的是第 %d 项" % (index, want + 1)
        assert name == state["frame_picture_name"], \
            "帧背景第 %d 项的名字变了：%r → %r" % (want + 1, state["frame_picture_name"], name)

    if state["window_picture"] is not None:
        gallery = id_of(win, "BackgroundGallery")
        items = gallery.GetChildren()
        want = state["window_picture"]
        assert len(items) > want, "窗口背景画廊里只剩 %d 项，原来那项（第 %d 项）不在了" % (len(items), want + 1)
        press(items[want])
        time.sleep(1)
        index, name = selected(gallery)
        assert index == want, "窗口背景选回去的是第 %s 项，记下来的是第 %d 项" % (index, want + 1)
        assert name == state["window_picture_name"], \
            "窗口背景第 %d 项的名字变了：%r → %r" % (want + 1, state["window_picture_name"], name)


def main():
    action = (sys.argv[1:] or ["status"])[0]
    win = open_settings()
    now = look(win)
    print("现在：", describe(now))

    if action == "status":
        return 0

    if action == "clean":
        with open(STATE, "w", encoding="utf-8") as handle:
            json.dump(now, handle, ensure_ascii=False, indent=2)

        clean(win, now)
        print("已复位成默认（原来是什么记在 %s）" % os.path.relpath(STATE, ROOT))
        print("复位后：", describe(look(win)))
        return 0

    if action == "restore":
        if not os.path.isfile(STATE):
            print("没记过原来是什么（%s 不在），什么都不做" % os.path.relpath(STATE, ROOT))
            return 0

        with open(STATE, encoding="utf-8") as handle:
            remembered = json.load(handle)

        restore(win, remembered)
        os.remove(STATE)
        print("已按原样放回：", describe(look(win)))
        return 0

    print("用法：status | clean | restore")
    return 1


if __name__ == "__main__":
    sys.exit(main())
