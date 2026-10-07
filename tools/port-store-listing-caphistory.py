"""把商店文案（docs/store-listing.md，14 语言）的说明段补到**第十八页**。

应用里现在是十八页，而商店文案的图表页清单停在十七页 —— 市值历程这一页从来没进过商店。
在这个仓库里这不算新事：第十七页（债市固收）也是上线一年后才由 `port-store-listing-1050.py`
补进去的，理由写在那个脚本的头里。补的不是「本版新增」，而是**商店说得出的话得和应用里有
的东西对上** —— 清单写着十七页、末尾缺一页，比「还差一页没写」更容易被当成谎话。

清单的顺序是历史上一次次上架时追加出来的，**不是导航顺序**，所以新的一页追加在末尾，不动
前面十七条。

为什么不是一个 `-1090.py`
------------------------
按仓库的老规矩，版本号那几个脚本（`-1050` … `-1080`）是一次性的，除了改说明段还要**换掉**
「此版本的新增功能」那一栏。而那一栏是**换**不是加，必须在 manifest 版本号与 CHANGELOG
一起动的那一轮里写 —— 文案不能先于匹配的包上传。现在还没到那一轮，所以在这里只碰说明段的
三行（清单、标题、功能条），把「新增功能」留给那一轮自己的脚本。

**一个位置只有一个 owner。** 这里的三行与「新增功能」那一栏不是同一行，所以分工不冲突；
将来那轮脚本跑到这里时会发现标题已经是「十八大图表页」（`elif new not in` 这一条），
跳过而不报错 —— 这是幂等，不是巧合。

数字词不在这里手写第二份
------------------------
「十七」「十八」怎么说，各语言各有一套词（日语是 `17 つの`、德语是 `Siebzehn`），写错了
标题就变成「十八大图表页十七页」这类自相矛盾的句子，而十四份里只有一两个语言错的时候,
肉眼是看不出来的。所以这里 **不写「十七」**，而是从上一轮的 owner —— `port-store-listing-1050.py`
的 `HEADING` / `FEATURE` 两张表 —— 按路径加载进来取它的 `new`（那一轮的「十七」）作为锚，
只在这里提供目的地（「十八」）。同一个数字词因此只有一个地方写得出来。

**描述不另写。** 这一页的说明从 14 份 help-*.md 的同一章首段取 —— 那是项目自己翻的、和界面
一致的说法。顺带一个好处：手册那一章的开头刚刚改成「也可以同时画几家公司」，商店这边的
说明跟着一起说了多标的这件事，不用再写一套。

定位与幂等：清单按页面名查重；标题与功能条按整行精确替换（某语言的措辞与脚本不一致时报错，
而不是留下一个旧数字）；store-listing.md 是 **CRLF**，写完照原样写回。

用法：python tools\\port-store-listing-caphistory.py      （跑第二遍应当是 0 处改动）
"""

import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from listingtext import HELP, LANGS, LISTING, dash_of, page_name  # noqa: E402

# 上一轮的 owner：它是「页清单补到十七」那件事的唯一事实来源。文件名带连字符，只能按路径
# 加载；**清 argv 再加载**，否则它会把本脚本的命令行参数当成自己的（见 tools/ 的那些坑）。
_argv = sys.argv
sys.argv = [sys.argv[0]]

_spec = importlib.util.spec_from_file_location(
    "port_store_listing_1050", os.path.join(HERE, "port-store-listing-1050.py"))
_prev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prev)

sys.argv = _argv

assert sorted(_prev.HEADING) == sorted(LANGS), "上一轮的标题表缺语言"
assert sorted(_prev.FEATURE) == sorted(LANGS), "上一轮的功能条表缺语言"

PAGE = "NavCapHistory"
CHAPTER = None          # 在 main() 里从导航算出来；见 listingtext.chapter_of。

# 目的地：十七 → 十八。锚是上一轮那两个表的 new（「十七」），所以这里只写增量那一半。
HEADING = {
    "zh-Hans": "十八大图表页",
    "zh-Hant": "十八大圖表頁",
    "en-US": "Eighteen chart pages",
    "ja": "18 つのチャートページ",
    "ko": "18가지 차트 페이지",
    "de": "Achtzehn Diagrammseiten",
    "fr": "Dix-huit pages de graphiques",
    "it": "Diciotto pagine di grafici",
    "es": "Dieciocho páginas de gráficos",
    "pt-BR": "Dezoito páginas de gráficos",
    "pl": "Osiemnaście stron wykresów",
    "cs": "Osmnáct stránek s grafy",
    "ru": "Восемнадцать страниц с графиками",
    "tr": "On sekiz grafik sayfası",
}

FEATURE = {
    "zh-Hans": "十八种图表",
    "zh-Hant": "十八種圖表",
    "en-US": "Eighteen charts",
    "ja": "18 種類のチャート",
    "ko": "18가지 차트",
    "de": "Achtzehn Diagramme",
    "fr": "Dix-huit graphiques",
    "it": "Diciotto grafici",
    "es": "Dieciocho gráficos",
    "pt-BR": "Dezoito gráficos",
    "pl": "Osiemnaście wykresów",
    "cs": "Osmnáct grafů",
    "ru": "Восемнадцать графиков",
    "tr": "On sekiz grafik",
}

# 中文那条清单用双破折号、前后不留空；其余语言用一个破折号、前后各留一个空格 —— 已有的
# 十七条就是这么写的，新加的这条不能看着像另一种文件抄来的。破折号本身抄这一段自己第一条。
DASH = {"zh-Hans": "——", "zh-Hant": "——"}

# 功能条里名字之间的分隔符。
COMMA = {"zh-Hans": "、", "zh-Hant": "、", "ja": "、", "ko": "、"}

EXPECTED = 17           # 补之前清单里应当正好十七条。


def intro(lang, chapter):
    """这一章的开场段 —— 商店清单里那一条说明。

    不写第六套 14 句：它们在 14 份 help-*.md 里已经有了。**取整段不取整句**，因为这一章的
    开场现在有两句，第二句说的正是「也可以同时画几家公司」—— 截到第一个句号会把这一版刚
    做出来的能力又删回去。
    """
    text = (HELP / f"help-{lang}.md").read_text(encoding="utf-8")
    body = re.split(r"(?m)^## ", text)[chapter + 1]
    lines = body.split("\n")[1:]
    at = 0

    while at < len(lines) and (not lines[at].strip() or lines[at].lstrip().startswith("![")):
        at += 1

    said = []

    while at < len(lines):
        line = lines[at].strip()

        if not line or line.startswith("- ") or line.startswith("• "):
            break

        said.append(line)
        at += 1

    joiner = "" if lang in ("zh-Hans", "zh-Hant", "ja") else " "
    said = re.sub(r"\*\*(.+?)\*\*", r"\1", joiner.join(said))

    # 清单里那十七条一条也不带句末句号，新加的这条也不能带。
    return said.strip().rstrip("。．.").rstrip()


def main():
    chapter = __import__("listingtext").chapter_of(PAGE)
    raw = LISTING.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        print("× store-listing.md 带着 BOM —— 商店文案不能带，先去掉再跑")
        return 1

    # CRLF 要原样写回：同一份文件里两种行尾，上传时看不出来，diff 里看得出来。
    crlf = b"\r\n" in raw
    lines = raw.decode("utf-8").replace("\r\n", "\n").split("\n")
    heads = [i for i, s in enumerate(lines) if s.startswith("## ")]

    if len(heads) != 14:
        print(f"× 数到 {len(heads)} 个语言段，应当是 14")
        return 1

    changed = 0

    for n, lang in enumerate(LANGS):
        start = heads[n]
        end = heads[n + 1] if n + 1 < len(heads) else len(lines)
        name = page_name(lang, PAGE)
        done = []

        bullets = [i for i in range(start, end) if lines[i].startswith("• ")]

        # 十七条是补之前、十八条是补之后，两个都合法 —— 这是幂等脚本自己第二次跑时的样子。
        # 写成「必须 17」的话第二遍会自己把自己判死；写成「不限」的话清单缺一条也照样通过。
        if len(bullets) not in (EXPECTED, EXPECTED + 1):
            print(f"× {lang}: 说明段有 {len(bullets)} 条，应当是 {EXPECTED} 或 {EXPECTED + 1} 条")
            return 1

        at = bullets[-1]

        # 标题在清单**前面**，所以要在插入之前认清楚：插进去的那一条会顶掉「往回找第一行」
        # 这种定位办法。
        title = at

        while lines[title].lstrip().startswith("•"):   # 跳过整条清单
            title -= 1

        while not lines[title].strip():                # 再跳过清单与标题之间的空行
            title -= 1

        if not any(lines[i].startswith(f"• {name}") for i in bullets):
            dash = DASH.get(lang) or f" {dash_of(lines[bullets[0]])} "
            lines.insert(at + 1, f"• {name}{dash}{intro(lang, chapter)}")
            changed += 1
            done.append("说明段 +1")

            # 插入把这一段撑长了一行，段尾的边界必须重算 —— 否则段末的「产品功能」
            # 那些行会落到边界外面，看上去就像这一语言没有功能条。
            heads = [i for i, s in enumerate(lines) if s.startswith("## ")]
            start = heads[n]
            end = heads[n + 1] if n + 1 < len(heads) else len(lines)

        # 标题：十七 → 十八。锚从上一轮那张表来，不是从这里写进去的「十七」。
        anchor = _prev.HEADING[lang][1]

        if anchor in lines[title]:
            lines[title] = lines[title].replace(anchor, HEADING[lang])
            changed += 1
            done.append("标题")
        elif HEADING[lang] not in lines[title]:
            print(f"× {lang}: 标题行「{lines[title]}」里既没有 {anchor!r} 也没有 {HEADING[lang]!r}")
            return 1

        # 功能条：十七种 → 十八种，末尾补上这一页的名字。
        anchor = _prev.FEATURE[lang][1]
        hit = [i for i in range(start, end)
               if lines[i].startswith("- ") and anchor in lines[i]]

        if hit:
            comma = COMMA.get(lang, ", ")
            lines[hit[0]] = lines[hit[0]].replace(anchor, FEATURE[lang]) + comma + name
            changed += 1
            done.append("功能条")
        elif not any(lines[i].startswith("- ") and FEATURE[lang] in lines[i]
                     for i in range(start, end)):
            print(f"× {lang}: 功能条里找不到 {anchor!r}")
            return 1

        # 段号会因为插入而位移，所以按标题重新定位一次。
        heads = [i for i, s in enumerate(lines) if s.startswith("## ")]
        print(f"· {lang}: {' / '.join(done) or '（已是十八页）'}")

    LISTING.write_bytes(("\r\n" if crlf else "\n").join(lines).encode("utf-8"))
    print(f"\n改了 {changed} 处（跑第二遍应当是 0）")

    return 0


if __name__ == "__main__":
    sys.exit(main())
