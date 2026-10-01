# -*- coding: utf-8 -*-
"""验证播放条：图标按钮的播放/暂停切换、位置的时钟写法、播完之后再按能重头放。

这个脚本跑真实 UI，因为这三件事都只在真实应用里成立或不成立：

1. 按钮是图标（▶/⏸），没有一个字可读。UIA 拿不到字形，但拿得到按钮的
   AutomationProperties.Name —— 而它和字形由同一个 SetPlaybackState 写，名字跟着状态
   走就说明字形也走了。名字停在「播放」而进度在动，就是字形没换。
2. 位置写成 m:ss（"0:00 / 1:15"）而不是秒数。断的是格式，所以读 ScrubText 的文本。
3. 取数完成后页面停在最后一帧，此时按播放若什么都不做，就是「按钮坏了」的样子。按下
   之后位置必须回到起点并重新走起来。

用法：
    python tools/verify-transport.py
"""
import os
import re
import subprocess
import time

import uiautomation as auto

APPID = "8166Yxw.MarketMotionStudio_fzc58jprbah1t!App"
EXE = "MarketMotionStudio.exe"
OUT = r"D:\software\MarketMotionStudio\artifacts"

PRIVATE = re.compile(r"[\ue000-\uf8ff]")

# "0:00 / 1:15" —— 钟点写法：分钟不补零，秒补两位，两侧各一段。
CLOCK = re.compile(r"^\d+:[0-5]\d / \d+:[0-5]\d$")

failures = []


def find(cond, root, depth=0, limit=25):
    if depth > limit:
        return None
    try:
        if cond(root):
            return root
    except Exception:
        return None
    try:
        for ch in root.GetChildren():
            r = find(cond, ch, depth + 1, limit)
            if r is not None:
                return r
    except Exception:
        pass
    return None


def byid(root, aid):
    return find(lambda c: c.AutomationId == aid, root)


def pat(ctrl, pattern_id):
    try:
        return ctrl.GetPattern(pattern_id)
    except Exception:
        return None


def invoke_click(ctrl):
    p = pat(ctrl, auto.PatternId.InvokePattern)
    if p is not None:
        try:
            p.Invoke()
            time.sleep(0.4)
            return True
        except Exception:
            pass
    try:
        ctrl.Click(simulateMove=False, waitTime=0.4)
        return True
    except Exception:
        return False


def app_pids():
    p = subprocess.run(["tasklist", "/FO", "CSV", "/FI", "IMAGENAME eq " + EXE],
                       capture_output=True)
    pids = set()
    for line in p.stdout.decode("utf-8", "replace").splitlines()[1:]:
        parts = [x.strip('"') for x in line.split('","')]
        if len(parts) >= 2 and parts[0].lower() == EXE.lower():
            pids.add(int(parts[1]))
    return pids


def launch():
    subprocess.run(["taskkill", "/IM", EXE, "/F"], capture_output=True)
    time.sleep(2)
    os.startfile(r"shell:AppsFolder\%s" % APPID)
    deadline = time.time() + 45
    while time.time() < deadline:
        if app_pids():
            for w in auto.GetRootControl().GetChildren():
                if w.ProcessId in app_pids() and w.Name:
                    time.sleep(3)
                    return w
        time.sleep(1)
    return None


def label(win, aid):
    c = byid(win, aid)
    return c.Name if c is not None else None


def position(win):
    """进度条当前值，读不到时返回 None。"""
    sc = byid(win, "Scrub")
    if sc is None:
        return None
    p = pat(sc, auto.PatternId.RangeValuePattern)
    if p is None:
        return None
    try:
        return p.Value
    except Exception:
        return None


def set_position(win, ratio):
    sc = byid(win, "Scrub")
    p = pat(sc, auto.PatternId.RangeValuePattern)
    if p is None:
        return False
    try:
        lo, hi = p.Minimum, p.Maximum
        p.SetValue(lo + (hi - lo) * ratio)
        time.sleep(0.8)
        return True
    except Exception:
        return False


def wait_ready(win, timeout=240):
    deadline = time.time() + timeout
    while time.time() < deadline:
        pb = byid(win, "PlayButton")
        if pb is not None and pb.IsEnabled:
            return True
        time.sleep(2)
    return False


def check(name, ok, detail=""):
    print(f"  {'✓' if ok else '✗'} {name}{'  ' + detail if detail else ''}")
    if not ok:
        failures.append(name)


def says_play(text):
    """按钮名字是「播放」而不是「暂停」——不认语言，比长度：两者一般长，所以只判不同。"""
    return text is not None


def main():
    win = launch()
    assert win is not None, "窗口未找到"

    print("取数（市场成交额，启动页）…")
    fetch = byid(win, "FetchButton")
    assert fetch is not None, "找不到取数按钮"
    invoke_click(fetch)
    assert wait_ready(win), "取数没有让播放按钮可用"

    resting = label(win, "PlayButton")
    text = label(win, "ScrubText")
    print(f"\n静止状态：按钮「{resting}」 位置「{text}」")

    check("位置是钟点写法", bool(text) and bool(CLOCK.match(text)), f"得到「{text}」")

    # 取数后停在最后一帧，此时按播放应当从头放——不能什么都不发生。
    before = position(win)
    invoke_click(byid(win, "PlayButton"))
    time.sleep(1.2)

    during = label(win, "PlayButton")
    check("按下后按钮变成暂停", during != resting, f"「{resting}」→「{during}」")

    moved = position(win)
    check("按下后位置从头走起", moved is not None and moved < 0.5, f"{before:.3f} → {moved:.3f}")

    time.sleep(2.0)
    ticked = position(win)
    running_text = label(win, "ScrubText")
    check("播放中位置在推进", ticked is not None and ticked > moved,
          f"{moved:.3f} → {ticked:.3f}  位置「{running_text}」")

    # ---- 暂停 ------------------------------------------------------------------
    invoke_click(byid(win, "PlayButton"))
    time.sleep(0.6)

    paused_label = label(win, "PlayButton")
    check("暂停后按钮变回播放", paused_label == resting, f"「{paused_label}」")

    held = position(win)
    time.sleep(2.0)
    still = position(win)
    check("暂停后位置不再推进", held is not None and still is not None and abs(still - held) < 1e-6,
          f"{held:.3f} → {still:.3f}")

    # ---- 继续：回到暂停前的那个位置，而不是重头 ---------------------------------
    invoke_click(byid(win, "PlayButton"))
    time.sleep(2.0)
    resumed = position(win)
    check("再按播放从暂停处继续，不是重头", resumed is not None and resumed > still,
          f"{still:.3f} → {resumed:.3f}")
    check("继续时按钮又是暂停", label(win, "PlayButton") != resting)

    # ---- 拖动之后按播放，要从拖到的那一帧继续 -----------------------------------
    invoke_click(byid(win, "PlayButton"))  # 停下
    time.sleep(0.4)
    set_position(win, 0.5)
    mid = position(win)
    time.sleep(0.5)
    invoke_click(byid(win, "PlayButton"))
    time.sleep(0.6)
    carried = position(win)
    check("拖动后按播放从拖到的那一帧继续",
          None not in (mid, carried) and abs(carried - mid) < 0.06,
          f"拖到 {mid:.3f} → 播放后 {carried:.3f}")
    invoke_click(byid(win, "PlayButton"))  # 停下
    time.sleep(0.4)

    # ---- 拖到末尾，再按播放应当重头 ---------------------------------------------
    set_position(win, 1.0)

    end_text = label(win, "ScrubText")
    print(f"\n拖到末尾：位置「{end_text}」")
    check("末尾位置两侧是同一个钟点",
          bool(end_text) and CLOCK.match(end_text) and end_text.split(" / ")[0] == end_text.split(" / ")[1])

    invoke_click(byid(win, "PlayButton"))
    time.sleep(1.5)
    restarted = position(win)
    check("在末尾按播放会重头", restarted is not None and restarted < 0.5, f"{restarted:.3f}")
    check("重头时按钮是暂停", label(win, "PlayButton") != resting)

    time.sleep(1.0)
    os.makedirs(OUT, exist_ok=True)
    shot = os.path.join(OUT, "verify-transport.png")
    try:
        # 指针要先挪开：按钮上的 tooltip 会浮在按钮上方，截进去就成了「多了一个按钮」，
        # 而它恰恰是这次要写进画面的东西之一——留到人眼确认时反而认错。
        auto.SetCursorPos(4, 700)
        time.sleep(1.5)
        win.SetFocus()
        time.sleep(1)
        ok = win.CaptureToImage(shot)
        print(f"\n截图：{shot}（{os.path.exists(shot)}）")
    except Exception as e:
        print(f"\n截图失败：{e!r}")

    print()
    if failures:
        print(f"失败 {len(failures)} 项：" + " / ".join(failures))
    else:
        print("全部通过")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
