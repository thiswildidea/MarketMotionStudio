# -*- coding: utf-8 -*-
r"""截图期间把桌面换成纯色，截完换回来。

为什么需要
    主窗口是 Mica（MainWindow.xaml 里的 <Window.SystemBackdrop>），窗口底色
    是"壁纸模糊 + 一层薄色" —— 于是**桌面壁纸会透进每一张截图**。以前几轮没
    人发现，只是因为那几天桌面恰好是纯色（旧图的导航栏底色 (249,241,236)、
    内容卡片 (252,248,246) 就是那个纯色透出来的样子）。

    2026-10-10 重截时桌面是 Spotlight 轮换来的粉彩图（壁纸路径在
    …\IrisService\ 缓存下，会自己换），七张图整扇窗都是粉的，连"预览卡片"
    的边都看不出来。所以这件事得显式做掉，不能指望运气。

    图片内容会跟着桌面变，还有一个后果：同一套图今天截和明天截底色不一样 ——
    十四种语言的帮助文档看起来就不像一套。纯色壁纸同时也把这件事钉住了。

用法：
  python tools/plain-wallpaper.py on      # 换成纯色，并记下原来那张的路径
  python tools/plain-wallpaper.py off     # 换回原来那张
  python tools/plain-wallpaper.py status  # 现在是什么状态
"""

import ctypes
import json
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAIN = os.path.join(ROOT, "artifacts", "plain-wallpaper.png")
STATE = os.path.join(ROOT, "artifacts", "wallpaper-before.json")

# SPI_SETDESKWALLPAPER / SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
SET_WALLPAPER = 20
BROADCAST = 3

# 壁纸颜色：取旧图底色的均值（导航栏 (249,241,236) 与卡片 (252,248,246)），
# Mica 再叠一层薄色，出来和旧图同一个观感。数字是照着旧图定的，不是估的 ——
# 换一次壁纸等于给所有已发布的图换底色，没必要。
COLOUR = (248, 243, 239)


def apply(path):
    if not ctypes.windll.user32.SystemParametersInfoW(SET_WALLPAPER, 0, path, BROADCAST):
        sys.exit("  ! 换壁纸失败：%s" % path)


def current():
    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop") as key:
        return winreg.QueryValueEx(key, "WallPaper")[0]


def write_plain():
    image = Image.new("RGB", (1920, 1080), COLOUR)
    image.save(PLAIN)
    return PLAIN


def main():
    action = (sys.argv[1:] or ["status"])[0]
    remembered = None

    if os.path.isfile(STATE):
        with open(STATE, encoding="utf-8") as handle:
            remembered = json.load(handle)

    if action == "on":
        before = current()

        if remembered and remembered.get("plain") == before:
            print("已经是纯色了（%s）" % before)
            return 0

        with open(STATE, "w", encoding="utf-8") as handle:
            json.dump({"plain": PLAIN, "was": before}, handle, ensure_ascii=False, indent=2)

        apply(write_plain())
        print("桌面 → 纯色 %s（原来那张记在 %s）" % (COLOUR, os.path.relpath(STATE, ROOT)))
        return 0

    if action == "off":
        if not remembered:
            print("没记过原来那张（%s 不在），什么都不做" % os.path.relpath(STATE, ROOT))
            return 0

        was = remembered.get("was")

        if not was or not os.path.isfile(was):
            print("原来那张壁纸已经不在了（%s）—— 留着纯色，Spotlight 会自己换下一张" % was)
            os.remove(STATE)
            return 0

        apply(was)
        os.remove(STATE)
        print("桌面 → 换回 %s" % was)
        return 0

    now = current()
    print("现在是 %s" % now)
    print("纯色截图状态：%s" % ("开" if remembered and now == remembered.get("plain") else "关"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
