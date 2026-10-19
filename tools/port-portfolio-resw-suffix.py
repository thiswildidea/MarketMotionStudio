# -*- coding: utf-8 -*-
r"""把「实时持仓收益」那几条属性后缀写错的 resw 键改对。

**为什么现在才看出来。** `x:Uid` 不会自己去找同名的裸键 —— 它只认 `名字.属性`，而且
**属性名必须是那个控件真有的那一个**。两处都错过，症状也一样：键数对得上，十四份的键顺序
也对得上，编译不报错，运行时那一句**干脆不显示**。区别在于写错属性名的那种更凶：

  * 裸键（`PortfolioDialogHint`）用在 TextBlock 的 `x:Uid` 上 → 那一句不显示。
  * `...Content` 用在 **ToggleSwitch** 上 → **整页打不开**。`ToggleSwitch` 没有 `Content`
    属性，XAML 加载器抛 `XamlParseException: Unable to resolve property 'Content' while
    processing properties for Uid 'PortfolioPnlAutoRefresh'`，`Frame.Navigate` 整趟失败，
    窗口留在上一页 —— 而导航项的选中态照常移过去，看起来像「点了没反应」。

第二种是这一页第一次真机跑才发现的：`verify-resw-uids.py` 认的是「有没有带后缀的同名键」，
它答「有」（`PortfolioPnlAutoRefresh.Content`），可那个后缀这个控件不认。判据补不上这一条
（属性名要看控件类型，而那个类型在 XAML 里），所以留在注释里：**ToggleSwitch 用 `.Header`**，
同一个键在 `SettingsWatermarkToggle` 上就是 `.Header`。

**改的是键名不是值**：值是已经逐语言斟酌过的，而这次要修的是「界面上取不到它」。键在原位
改名，所以十四份的键顺序（`434ae7c5f1cf` 那个哈希）不受影响。

用法：python tools\port-portfolio-resw-suffix.py
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "fr", "it",
         "es", "pt-BR", "pl", "cs", "ru", "tr"]

# 裸键 → 补 `.Text`（用在 TextBlock 的 x:Uid 上）。
BARE = ["PortfolioDialogHint", "PortfolioDialogAdd", "PortfolioImportHint"]

# `.Content` → `.Header`（用在 ToggleSwitch 的 x:Uid 上）。
WRONG_PROPERTY = [("PortfolioPnlAutoRefresh.Content", "PortfolioPnlAutoRefresh.Header")]

PATTERN = re.compile(r'(<data name=")(%s)(")' % "|".join(BARE))


def main():
    changed = 0

    for lang in LANGS:
        path = ROOT / lang / "Resources.resw"
        raw = path.read_bytes()

        if not raw.startswith(b"\xef\xbb\xbf"):
            sys.exit("%s 没有 BOM —— 编码已经不是原先那一种，先查清楚再写" % path)

        # resw 是 **LF 带 BOM**（README「设 14 语言」那条也是这么记的）。这里不猜：
        # 文件里要是混进了 CR，说明换行已经被别的工具改过，写回去只会把两种换行混在一起。
        text = raw.decode("utf-8-sig")

        if "\r" in text:
            sys.exit("%s 里混进了 CR —— 换行已经不是 LF，先查清楚再写" % path)

        after, hits = PATTERN.subn(lambda m: m.group(1) + m.group(2) + ".Text" + m.group(3), text)

        for old, new in WRONG_PROPERTY:
            count = after.count('<data name="%s">' % old)

            if count == 0:
                continue

            after = after.replace('<data name="%s">' % old, '<data name="%s">' % new)
            hits += count

        if hits:
            path.write_bytes(b"\xef\xbb\xbf" + after.encode("utf-8"))
            # 校验：BOM 在、LF 在、三个裸键一个都不剩
            reread = path.read_bytes()
            check = reread.decode("utf-8-sig")

            if not reread.startswith(b"\xef\xbb\xbf") or "\r" in check:
                sys.exit("%s 的换行或 BOM 被改坏了" % path)

            for key in BARE:
                if '<data name="%s">' % key in check:
                    sys.exit("%s 里还剩裸键 %s" % (path, key))

            changed += 1
            print("%-9s %d 处改名" % (lang, hits))
        else:
            print("%-9s 已经是带后缀的（跳过）" % lang)

    print("\n改了 %d 份" % changed)


if __name__ == "__main__":
    main()
