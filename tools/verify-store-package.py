# -*- coding: utf-8 -*-
r"""拆包核验商店上传包：版本、架构、以及「该在里面的东西是不是真的在里面」。

为什么不能只看「文件存在 + 大小差不多」：

* `PackageSuccessfullyCreated` 说的是**打包这一步做完了**，不是说做出来的东西带着当前源码。
  中间产物（`Upload` / `ForBundle` / `*.appxrecipe`）没清就重编，上传包照旧生成、尺寸照旧、文件名
  照旧，而里面装的是哪一版完全看不出来。**这里不拆包核验，上一轮那个包就会被当成这一轮的。**
* 「版本号」分布在三处：manifest、CHANGELOG 首条、上传包里**每个内包**的 Identity。前两处归
  `verify-docs.py`，第三处只能拆包：`msixupload` → `msixbundle` → 每个 `msix` → `AppxManifest.xml`。
* 符号缺失会让上传包**没有 `.appxsym`**。这不影响上架（只关系到 Store 还原崩溃堆栈），但它是
  「这次构建走了哪条路」的一条证据 —— 所以下面**把它打印出来**，而不是假装看不见。

包是怎么分层的（这次实测，别再猜）：上传包里只有 1 个 bundle；bundle 里 **6 个** `msix` ——
2 个架构包（`ProcessorArchitecture="x64"/"arm64"`，各 181 项：应用本体、14 份手册、70 张帮助插图、
`resources.pri`、Win2D 原生 dll、`runtimeconfig.json` / `deps.json`）+ 4 个资源包
（`ResourceId="split.scale-100/125/150/400"`，只装按比例分的那一版图标）。bundle 清单在
`AppxMetadata/AppxBundleManifest.xml`，不在根上。

用法：python tools\verify-store-package.py [上传包路径]
"""
import io
import pathlib
import re
import sys
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
MANIFEST = ROOT / "src" / "MarketMotionStudio" / "Package.appxmanifest"

# 包名**从 manifest 的版本号算出来，不写死**：写死的那一版在版本号前进之后会一声不响地
# 去验上一个包，而那个包**每一项都是对的**（它就是照着当时的 manifest 编的）—— 只有
# 「Identity 都写着 manifest 那个版本」这一条会对不上，于是看起来像「包编错了」，
# 真因却是脚本在看别的文件。实测 1.0.6.0 那次就是这样。
DEFAULT = ROOT / "artifacts" / ("MarketMotionStudio_%s_x64_arm64_bundle.msixupload"
                                % re.search(
                                    r'<Identity[^>]*Version="([^"]+)"',
                                    MANIFEST.read_text(encoding="utf-8-sig")).group(1))

SCALES = ["split.scale-100", "split.scale-125", "split.scale-150", "split.scale-400"]
ARCHS = ["x64", "arm64"]
HELP_DOCS = 14
HELP_MEDIA = 70

PASSED = []
FAILED = []


def check(what, ok, note=""):
    line = "  %s %s" % ("√" if ok else "×", what)

    if note:
        line += "  — %s" % note

    print(line, flush=True)
    (PASSED if ok else FAILED).append(what)


def version():
    text = MANIFEST.read_text(encoding="utf-8-sig")
    hit = re.search(r'<Identity[^>]*Version="([^"]+)"', text)
    assert hit, "manifest 里没有 Identity Version"
    return hit.group(1)


def nested(zip_root, name):
    """把嵌套的 zip 读出来对着看，不落到磁盘。"""
    return zipfile.ZipFile(io.BytesIO(zip_root.read(name)))


def member(container, name):
    return container.read(name).decode("utf-8-sig", errors="replace")


def main(argv):
    path = pathlib.Path(argv[1]) if len(argv) > 1 else DEFAULT
    want = version()

    print("上传包：%s" % path.name)
    print("manifest 里的版本：%s" % want, flush=True)

    if not path.exists():
        print("  × 文件不存在 — %s" % path)
        return 1

    size = path.stat().st_size
    print("大小：%.1f MB / %.1f MiB" % (size / 1e6, size / 2 ** 20), flush=True)
    check("大小对得上这类包的量级（两个架构包里各有整套 Win2D 运行时，>100MB）",
          size > 100 * 10 ** 6, "%.1f MB" % (size / 1e6))

    with zipfile.ZipFile(path) as upload:
        bundles = [n for n in upload.namelist() if n.endswith(".msixbundle")]
        symbols = [n for n in upload.namelist() if n.endswith(".appxsym")]

        check("上传包里只有一个 bundle", len(bundles) == 1, ", ".join(bundles) or "没有")
        print("  · 符号包：%s" % (", ".join(symbols) if symbols else "没有（这次构建不含符号）"))

        bundle = nested(upload, bundles[0])
        layout = member(bundle, "AppxMetadata/AppxBundleManifest.xml")
        packages = [n for n in bundle.namelist() if n.endswith(".msix")]

        check("bundle 里装着 6 个内包（2 架构 + 4 个 scale 资源包）", len(packages) == 6,
              "%d 个" % len(packages))
        check("bundle 清单登记的包数与 bundle 里实际的 .msix 数一致",
              len(re.findall(r'<Package\s', layout)) == len(packages),
              "清单 %d 条 / 实际 %d 个" % (len(re.findall(r'<Package\s', layout)), len(packages)))

        versions = []
        arch_package = {}
        resource_ids = []

        for name in packages:
            inner = nested(bundle, name)
            manifest = member(inner, "AppxManifest.xml")
            identity = re.search(r"<Identity[^>]*/?>", manifest).group(0)
            versions.append(re.search(r'Version="([^"]+)"', identity).group(1))

            arch = re.search(r'ProcessorArchitecture="([^"]+)"', identity)
            resource = re.search(r'ResourceId="([^"]+)"', identity)

            if arch:
                arch_package[arch.group(1)] = (name, inner)
            else:
                resource_ids.append((resource.group(1) if resource else "?", inner))

            print("  · %-46s %s" % (pathlib.Path(name).name,
                                    arch.group(1) if arch else resource.group(1)))

    check("每个内包的 Identity 都写着 manifest 那个版本",
          set(versions) == {want}, "%s（%d 个内包）" % ("/".join(sorted(set(versions))), len(versions)))
    # 两边都排序再比：字典的键不保证就是写出来的那个顺序。
    check("架构包正好是 x64 与 arm64 各一个", sorted(arch_package) == sorted(ARCHS),
          " ".join(sorted(arch_package)))
    check("资源包正好是那四个 scale",
          sorted(r[0] for r in resource_ids) == SCALES, " ".join(sorted(r[0] for r in resource_ids)))

    for arch in ARCHS:
        name, inner = arch_package[arch]
        names = [n for n in inner.namelist() if not n.startswith("[")]
        docs = [n for n in names if n.startswith("Assets/Help/help-") and n.endswith(".md")]
        media = [n for n in names if n.startswith("Assets/Help/media/") and n.endswith(".png")]
        canvas = [n for n in names if n.lower().endswith("microsoft.graphics.canvas.dll")
                  and arch in n.lower()]
        runtime = [n for n in names if n.endswith(("runtimeconfig.json", "deps.json"))]

        check("%s 包有 %d 份帮助手册" % (arch, HELP_DOCS), len(docs) == HELP_DOCS,
              "%d 份" % len(docs))
        check("%s 包有 %d 张帮助插图" % (arch, HELP_MEDIA), len(media) == HELP_MEDIA,
              "%d 张" % len(media))
        check("%s 包有 resources.pri" % arch, "resources.pri" in names)
        check("%s 包带自己的 Win2D 原生 dll" % arch, bool(canvas),
              canvas[0] if canvas else "没有")
        # 这两个缺掉就是那个著名的坑：Rebuild 先清、复制回去时在锁住的 exe 上失败，
        # 然后 apphost 说没装 .NET —— 而那句话是假的。
        check("%s 包有 runtimeconfig.json 与 deps.json" % arch, len(runtime) == 2,
              ", ".join(pathlib.Path(n).name for n in runtime))
        check("%s 包装着应用本体" % arch, "MarketMotionStudio.dll" in names
              and "MarketMotionStudio.exe" in names)

    for resource_id, inner in resource_ids:
        names = [n for n in inner.namelist() if not n.startswith("[")]
        assets = [n for n in names if n.startswith("Assets/")]

        check("%s 包里装着按比例分的资产" % resource_id, bool(assets) and "resources.pri" in names,
              "%d 项资产" % len(assets))

    print("\n%s" % ("全部通过" if not FAILED else "%d 项失败" % len(FAILED)))

    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
