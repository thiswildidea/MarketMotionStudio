# -*- coding: utf-8 -*-
r"""Debug 构建的订阅模拟开关：开 / 关 / 查。

`StoreSubscription.ReadSimulation()`（`#if DEBUG` 包裹）在启动时读一份
`LocalState\simulate-subscription.txt`：**文件在 = 已订阅**，文件内容被当成价钱显示。
Release 里这段被编译掉，所以这个开关只对 Debug 构建有效。

它解锁的是订阅买下的那两件事 —— 导出视频、去掉水印（关开关 + 把浓度从上限调下来）。

用法：
    python tools/simulate-subscription.py on [价钱]   # 默认 ¥28.00
    python tools/simulate-subscription.py off
    python tools/simulate-subscription.py status

注意：`verify-watermark-strength-lock.py` 的 finally 里会**无条件删掉**这个文件
（它对两种状态都做断言，跑完必须复位），跑过它之后要重新 on 一次。
"""
import os
import sys

PACKAGE = "8166Yxw.MarketMotionStudio_fzc58jprbah1t"
SIMULATION = os.path.join(
    os.environ.get("LOCALAPPDATA", ""), "Packages", PACKAGE, "LocalState",
    "simulate-subscription.txt")

DEFAULT_PRICE = "¥28.00"


def state():
    if not os.path.exists(SIMULATION):
        return False, None

    with open(SIMULATION, encoding="utf-8") as f:
        return True, f.read().strip()


def main(argv):
    action = argv[0] if argv else "status"

    if action == "status":
        on, shown = state()
        print("模拟文件：%s" % SIMULATION)
        print("状态：%s" % ("已订阅（Debug 模拟）" if on else "未订阅"))

        if on:
            print("价钱：%r%s" % (shown or "", "" if shown else "（空文件 → 卡片上仍显示 “—”）"))

        return 0

    if action == "on":
        price = argv[1] if len(argv) > 1 else DEFAULT_PRICE
        os.makedirs(os.path.dirname(SIMULATION), exist_ok=True)

        with open(SIMULATION, "w", encoding="utf-8") as f:
            f.write(price)

        print("已打开订阅模拟（价钱显示为 %r）" % price)
        print("记得**重启应用**：这份文件只在启动时读一次。")
        return 0

    if action == "off":
        if os.path.exists(SIMULATION):
            os.remove(SIMULATION)
            print("已关闭订阅模拟（文件已删）")
        else:
            print("本来就是关的（文件不在）")

        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
