# -*- coding: utf-8 -*-
r"""验证水印**进到文件里**：取数 → 导出封面 PNG（开 / 关各一张）→ 量纹理。

为什么单独跑这一趟：`verify-watermark.py` 量的是窗口里那块预览面，而封面走的是
`FrameExporter` —— **共享设备**上的一个离屏 `CanvasRenderTarget`，1:1、无变换。水印那一层是
按设备缓存的，所以这两条路径用的是两份缓存，其中一份建不起来（尺寸、dpi、设备换代）时画面
上什么也看不出来：`Watermark.Draw` 会退回逐帧画那一百多个字，文件仍然对，只是导出慢得不像
话。这一趟就是来证明那份缓存真的建起来了，顺便确认导出件与预览是同一幅画面。

判据与预览同一套（`grain_array`）：封面没有窗口边框，是一整幅 1080×1920 的帧，所以按行取中位
数这一步在这儿更干净——同一行同色，唯一的偏离就是画上去的东西。

收尾一定要复位：开关回开、文字回默认。这一个脚本留在「关」上，下一个验水印的脚本就会对着
一张没有水印的画面找水印。

**这一趟要有输出文件夹才跑得动。** 应用是「第一次导出时问一次，之后记住」，而那一次问的是系统
的「选择文件夹」——它在本机 UIA 里报不出控件坐标，按钮 `Invoke()`、回车、Esc 全不进去（只有
WM_CLOSE 关得掉，可那一次 `await` 就永远不返回了）。所以没设置过输出文件夹时，脚本会说一声
跳过，而不是把一个没过的事报成失败；在应用里手动导出一次之后重跑即可。

用法：python tools\verify-watermark-export.py
"""
import importlib.util
import os
import re
import sys
import time

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SRC = os.path.join(REPO, "src", "MarketMotionStudio")

sys.path.insert(0, HERE)

_vfb = importlib.util.spec_from_file_location("vfb", os.path.join(HERE, "verify-framebackdrop.py"))
vfb = importlib.util.module_from_spec(_vfb)
_vfb.loader.exec_module(vfb)

_vw = importlib.util.spec_from_file_location("vw", os.path.join(HERE, "verify-watermark.py"))
vw = importlib.util.module_from_spec(_vw)
_vw.loader.exec_module(vw)

DEFAULT_TEXT = "周期留白"
LOG = os.path.join(
    os.environ["LOCALAPPDATA"],
    r"Packages\8166Yxw.MarketMotionStudio_fzc58jprbah1t\LocalState\crash.log")


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


def wait_status(window, before, keywords, seconds=150):
    deadline = time.time() + seconds

    while time.time() < deadline:
        time.sleep(2)

        for line in texts(window):
            if line not in before and any(k in line for k in keywords):
                return line

    return None


def cover_path(status):
    """封面已保存的状态行里那个路径。

    状态行是「… 名字.png … 1080 × 1920 … D:\\某个文件夹」，所以取最后一处盘符开头、
    以 .png 收尾的片段。拼路径而不是猜文件名：输出文件夹是用户选的。
    """
    if not status:
        return None

    found = re.findall(r"[A-Za-z]:\\[^\s，,（）()]*\.png", status)

    return found[-1] if found else None


def picker(window):
    """系统那个「选择文件夹」对话框，没弹出来就是 None。"""
    return vfb.find(
        lambda c: c.ClassName == "#32770" and c.ControlTypeName == "WindowControl", window)


def dismiss(dialog):
    """把那个对话框关掉。

    没有 `Close()`，而它的「选择文件夹」/「取消」两个按钮在 UIA 里报出来的矩形是
    `(0,0,0,0)` —— `Invoke()` 因此走不通（退回鼠标点击也点不动），回车与 Esc 一样进不去。
    只有 WM_CLOSE 有效。

    **关掉它并不能让导出继续。** 产品那边等的是 `PickSingleFolderAsync`，窗口被这样关掉
    它不会返回，于是封面的 `RunAsync` 一直挂着、按钮从此是灰的。所以这一趟到此为止，让
    脚本带着一句说明退出，而不是接着往下量一堆已经没意义的数。
    """
    if dialog is None:
        return

    import ctypes

    ctypes.windll.user32.PostMessageW(dialog.NativeWindowHandle, 0x0010, 0, 0)
    time.sleep(2)


def frame_grain(path):
    im = Image.open(path).convert("RGB")

    return vw.grain_array(np.asarray(im, dtype=np.int16))


def main():
    pids = vfb.app_pids()

    if not pids:
        os.startfile(r"shell:AppsFolder\%s" % vfb.APPID)
        time.sleep(6)

    window = vfb.wait_window()
    assert window is not None, "窗口未找到"

    window.SetActive()
    window.MoveWindow(60, 60, 1500, 940)
    time.sleep(1.5)

    # 摆到已知状态：开 + 默认那句话。
    vfb.goto_settings(window)
    vw.settle(window, True, DEFAULT_TEXT)

    # ---- 取数：封面要有一份数据才让导出
    vfb.goto_first_page(window)
    before = set(texts(window))
    vfb.invoke_click(vfb.require(window, "FetchButton"))
    print("取数…")
    status = wait_status(window, before, ("交易日", "失败", "错误", "超时", "过长"))

    assert status, "取数没等到结果"
    print("  取数:", status)

    # ---- 开着：导出封面
    #
    # **输出文件夹没设置过时，这里会弹出系统的「选择文件夹」** —— 那是产品的设计（第一次
    # 导出由人点一次，之后记住），但对自动化是一堵墙，见 dismiss()。所以先看它有没有弹出来：
    # 弹了就说明这一趟跑不了，明说跳过。在这里报「封面里没有水印」会是彻头彻尾的假话。
    before = set(texts(window))
    started = time.time()
    vfb.invoke_click(vfb.require(window, "CoverButton"))

    for _ in range(8):
        time.sleep(0.5)

        if picker(window) is not None:
            dismiss(picker(window))
            print()
            print("跳过：输出文件夹还没设置过。")
            print("      第一次导出要有人在那个系统对话框里点一次文件夹，应用之后会记住它；")
            print("      而那个对话框 UIA 点不动（见 dismiss 的注释）。")
            print("      在应用里手动导出一次（封面或视频）之后，重跑本脚本即可。")
            return 0

    said = wait_status(window, before, (".png", "封面", "失败", "错误"), 90)
    took = time.time() - started

    on_path = cover_path(said)
    print("  存封面（开）:", said)

    check = vw.check

    check("封面导出报出了文件路径", on_path is not None, said or "没有状态行")

    if on_path is None:
        return

    on = frame_grain(on_path)

    check("封面里带着水印", on > vw.GRAIN_ON,
          "纹理占 {:.3%}，用时 {:.1f}s".format(on, took))

    # ---- 关掉：再导一张
    vfb.goto_settings(window)
    vw.settle(window, False, DEFAULT_TEXT)
    vfb.goto_first_page(window)

    before = set(texts(window))
    vfb.invoke_click(vfb.require(window, "CoverButton"))
    said = wait_status(window, before, (".png", "封面", "失败", "错误"), 90)

    off_path = cover_path(said)
    print("  存封面（关）:", said)

    check("关掉之后导出的封面是另一张", off_path is not None and off_path != on_path,
          str(off_path))

    if off_path is not None and off_path != on_path:
        off = frame_grain(off_path)

        check("关掉的封面上一格水印都没有", off < vw.GRAIN_OFF,
              "纹理占 {:.4%}".format(off))

    # ---- 那一层按设备缓存的整层没有建失败
    #
    # 建失败不会让画面出错：`Watermark.Draw` 退回逐帧画那一百多个字，文件照样对。
    # 所以只能从日志上看。
    if os.path.exists(LOG):
        with open(LOG, "rb") as handle:
            lines = handle.read().decode("utf-8", "replace").splitlines()

        bad = [line for line in lines if line.strip().startswith("watermark:")]

        check("水印那一层在每个设备上都建起来了", not bad, "; ".join(bad[-2:]))
    else:
        print("  （没有 crash.log，跳过那一层缓存的断言）")

    # ---- 收尾：开关回开
    #
    # 时长与分辨率一个字都没动过：封面是一帧，改它们省不下什么，倒是会在跳过的那条路上
    # 留下一份改过的偏好。凡是脚本改了的东西，都要有人负责改回去 —— 最简单的是别改。
    vfb.goto_settings(window)
    vw.settle(window, True, DEFAULT_TEXT)

    print()
    print("FAILED:", len(vw.FAILED))

    for label in vw.FAILED:
        print("  ✗", label)

    return 1 if vw.FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
