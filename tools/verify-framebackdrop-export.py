# -*- coding: utf-8 -*-
"""验证「动画背景」会进到文件里：图片模式 → 取数 → 导出封面 PNG + 最短 MP4。

封面走 FrameExporter（共享设备、离屏渲染），MP4 走编码器自己的设备与媒体线程——
两者都会用到 Backdrop 的图片解码与裁剪，所以两条路径都要跑。
用法：python tools/verify-framebackdrop-export.py
"""
import os
import sys
import time

import uiautomation as auto

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module

v = import_module("verify-framebackdrop")

KIND_PICTURE = 2


def texts(root, depth=0, limit=22, out=None):
    out = [] if out is None else out
    if depth > limit:
        return out
    try:
        if root.Name:
            out.append(root.Name)
    except Exception:
        pass
    try:
        for ch in root.GetChildren():
            texts(ch, depth + 1, limit, out)
    except Exception:
        pass
    return out


def wait_status(win, before, keywords, seconds=120):
    deadline = time.time() + seconds
    while time.time() < deadline:
        time.sleep(2)
        for t in texts(win):
            if t not in before and any(k in t for k in keywords):
                return t
    return None


def main():
    win = v.wait_window(20)
    if win is None:
        os.startfile(r"shell:AppsFolder\%s" % v.APPID)
        time.sleep(6)
        win = v.wait_window(30)
    assert win is not None, "窗口未找到"
    win.SetActive()
    win.MoveWindow(60, 60, 1500, 940)
    time.sleep(1.5)

    # ---- 背景设成一张图片
    v.goto_settings(win)
    v.scroll_settings(win, 45)
    print("kind ->", v.combo_select(v.require(win, "FrameBackdropCombo"), KIND_PICTURE))
    time.sleep(1.2)

    gallery = v.require(win, "FramePictureGallery")
    items = gallery.GetChildren()
    assert items, "动画背景画廊为空"
    v.invoke_click(items[0])
    time.sleep(1.5)
    v.set_slider(v.require(win, "FrameDimSlider"), 60)
    print("backdrop =", items[0].Name)

    # ---- 取数
    v.goto_first_page(win)
    before = set(texts(win))
    fetch = v.require(win, "FetchButton")
    v.invoke_click(fetch)
    print("fetching...")
    status = wait_status(win, before, ("交易日", "失败", "错误", "超时", "过长"), 150)
    print("fetch:", status)

    # ---- 最短时长 + 最小分辨率，让导出便宜
    v.set_slider(v.require(win, "DurationSlider"), 10)
    v.combo_select(v.require(win, "ResolutionCombo"), 0)
    time.sleep(1)

    # ---- 封面 PNG
    before = set(texts(win))
    v.invoke_click(v.require(win, "CoverButton"))
    status = wait_status(win, before, ("PNG", "封面", "失败", "错误"), 90)
    print("cover:", status)

    # ---- 最短 MP4
    before = set(texts(win))
    v.invoke_click(v.require(win, "ExportButton"))
    print("exporting...")
    status = wait_status(win, before, ("MP4", "导出", "失败", "错误", "取消"), 240)
    print("export:", status)

    # ---- 还原：时长/分辨率回默认，背景回「默认」（图片留在最近列表里）
    v.set_slider(v.require(win, "DurationSlider"), 90)
    v.combo_select(v.require(win, "ResolutionCombo"), 1)

    v.goto_settings(win)
    v.scroll_settings(win, 45)
    print("kind ->", v.combo_select(v.require(win, "FrameBackdropCombo"), 0))

    log = os.path.join(
        os.environ["LOCALAPPDATA"],
        r"Packages\8166Yxw.MarketMotionStudio_fzc58jprbah1t\LocalState\crash.log")
    print("--- last crash.log lines ---")
    try:
        with open(log, "rb") as f:
            tail = f.read().decode("utf-8", "replace").splitlines()[-12:]
        for line in tail:
            print("   ", line)
    except Exception as e:
        print("   ", e)

    print("OK" if status else "EXPORT STATUS NOT SEEN")


if __name__ == "__main__":
    main()
