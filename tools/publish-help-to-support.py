# -*- coding: utf-8 -*-
"""把手册发布到支持站点：从包里那份复制到 MarketMotionStudio-Support/help/。

为什么要复制而不是两边各写一遍
    「一件事在三处说 = 只在一处写」。手册的正文写在
    src/MarketMotionStudio/Assets/Help/，工具（port-*-help.py 那一批）改的也是
    这里，判据 verify-docs.py 量的也是这里。站点上那份是它的副本，由本脚本
    生成 —— 于是"应用里看到的那句话"和"网站上看到的那句话"不可能不一样。

    应用取哪一份见 Pages/HelpDocument.cs：先取网站上这份，取不到用包里那份。

要发布哪些语言由资源文件算出来
    应用要读的是 resw 里 HelpDocument 那个键指向的文件名，14 种语言各一份。
    本脚本从 Strings/*/Resources.resw 里读出来 —— 不写死语言表，也不写死
    "14"这个数字：加一种语言、改一次文件名，这里跟着走。

用法：
  python tools/publish-help-to-support.py                 # 复制并核对（幂等）
  python tools/publish-help-to-support.py --dry-run       # 只说会做什么
  python tools/publish-help-to-support.py --prune         # 顺带删掉站点上多出来的
  python tools/publish-help-to-support.py --support=D:\\path\\to\\Repo
"""

import argparse
import os
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "MarketMotionStudio", "Assets", "Help")
STRINGS = os.path.join(ROOT, "src", "MarketMotionStudio", "Strings")
SUPPORT = r"D:\software\MarketMotionStudio-Support"
SITE_DIR = "help"

ARGS = None


def languages():
    """(语言目录, 文件名) —— 语言表从资源文件算，不写死。"""
    found = []

    for entry in sorted(os.listdir(STRINGS)):
        resw = os.path.join(STRINGS, entry, "Resources.resw")

        if not os.path.isfile(resw):
            continue

        # resw 是 XML；用 ElementTree 而不是正则，省得被换行/属性顺序绊住。
        try:
            key = ET.parse(resw).getroot().find(
                "./data[@name='HelpDocument']/value")
        except ET.ParseError as problem:
            sys.exit("  ! %s 读不动：%s" % (resw, problem))

        if key is None or not (key.text or "").strip():
            sys.exit("  ! %s 里没有 HelpDocument" % resw)

        found.append((entry, key.text.strip()))

    if not found:
        sys.exit("  ! 资源目录里没找到任何 HelpDocument")

    return found


def pictures(document):
    """文档里引用的图片名，按出现顺序，去重。"""
    names = []
    with open(document, encoding="utf-8-sig") as handle:
        for line in handle:
            line = line.strip()
            if not line.startswith("!["):
                continue
            cut = line.find("](")
            if cut < 0 or not line.endswith(")"):
                continue
            name = line[cut + 2:-1].strip().replace("\\", "/")
            if name and name not in names:
                names.append(name)

    return names


def picture_file(help_root, language, name):
    """文档里写的 media/x.png 落在哪 —— 先看本语言目录，再看公共目录。

    与 HelpDocument.PictureFile 同一套规则：文档里写一个名字，图片按文档自己
    的语言取，于是十四份文档共用一份写法。规则要一致，因为站点上的路径是
    这里算出来的、应用那边是同一套算法拼出来的 —— 两边差一步，站点上就有
    四张图永远没人取。
    """
    cut = name.find("/")
    localized = (name[:cut + 1] + language + "/" + name[cut + 1:]) if cut > 0 else None

    for candidate in (localized, name):
        if not candidate:
            continue

        found = os.path.join(help_root, *candidate.split("/"))

        if os.path.isfile(found):
            return found, candidate

    return None, None


def same(first, second):
    if not os.path.isfile(second):
        return False

    if os.path.getsize(first) != os.path.getsize(second):
        return False

    with open(first, "rb") as a, open(second, "rb") as b:
        while True:
            left, right = a.read(65536), b.read(65536)
            if left != right:
                return False
            if not left:
                return True


def copy(source, destination, label, plan):
    if same(source, destination):
        return 0

    plan.append(label)
    if ARGS.dry_run:
        return os.path.getsize(source)

    os.makedirs(os.path.dirname(destination), exist_ok=True)
    shutil.copyfile(source, destination)
    return os.path.getsize(source)


def main():
    site = os.path.join(ARGS.support, SITE_DIR)
    media = os.path.join(SRC, "media")
    plan = []
    moved = 0
    wanted = set()

    if not os.path.isdir(ARGS.support):
        sys.exit("  ! 站点仓库不在：%s（--support= 可以指到别处）" % ARGS.support)

    for language, name in languages():
        document = os.path.join(SRC, name)

        if not os.path.isfile(document):
            sys.exit("  ! %s 说要读 %s，包里没有" % (language, name))

        wanted.add(name)
        moved += copy(document, os.path.join(site, name), name, plan)

        # 图片：文档点名了才算数，没点名的留在这儿也不发（否则站点上会慢慢
        # 攒下一堆没人引用的截图，而"这图还有用没有"没人答得上来）。
        for reference in pictures(document):
            found, relative = picture_file(SRC, language, reference)

            if found is None:
                sys.exit("  ! %s 引用了 %s，但 %s 里找不到这张图"
                         % (name, reference, language))

            wanted.add(relative)
            moved += copy(found, os.path.join(site, *relative.split("/")),
                          relative, plan)

    # 站点上多出来的：说了才算，删要有 --prune。不声不响地留着，下次改文档时
    # 就分不清"这张图是旧的"还是"这张图还没发布"。
    extra = []
    for folder, _, files in os.walk(site):
        for entry in files:
            relative = os.path.relpath(os.path.join(folder, entry),
                                       site).replace("\\", "/")
            if relative not in wanted:
                extra.append(relative)

    for relative in sorted(extra):
        print("  - 站点上多出来的：%s%s" % (relative, "（已删）" if ARGS.prune else "（留着，--prune 才删）"))
        if ARGS.prune and not ARGS.dry_run:
            os.remove(os.path.join(site, relative))

    print("%s%d 个文件，%d 处改动（共 %d 种语言）"
          % ("[dry-run] " if ARGS.dry_run else "", len(wanted), len(plan),
             len(languages())))

    for label in plan:
        print("  + %s" % label)

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--support", default=SUPPORT)
    parser.add_argument("--dry-run", dest="dry_run", action="store_true")
    parser.add_argument("--prune", action="store_true")
    ARGS = parser.parse_args()
    sys.exit(main())
