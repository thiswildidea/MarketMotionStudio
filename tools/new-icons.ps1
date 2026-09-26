<#
    Generates every image the package manifest declares, from one drawing routine.

    Run from the repository root:

        powershell -ExecutionPolicy Bypass -File tools\new-icons.ps1

    Why a script rather than checked-in artwork: the manifest names ten logos and
    MSIX resolves each one separately across scale and target-size qualifiers, so
    the set is thirty-odd files that must stay in family. A script keeps them one
    edit apart instead of thirty.

    The mark is three ascending bars on a mid-tone rounded body, and each of those
    choices answers a failure the shell this app is built on ran into:

    - **Mid-tone body, contrast on the inside.** A mark that relies on white
      disappears on a light taskbar; one that relies on a dark tone disappears on a
      dark one. A mid slate body with bright bars inside survives both.
    - **The subject fills the canvas.** An icon whose subject occupies a fifth of
      its own artwork is three pixels of drawing at 16 px.
    - **Real alpha.** Every file is written as 32-bit PNG with a transparent
      surround. A generator asked for transparency that paints a checkerboard
      instead produces a file that looks right in a preview and tiles once it is an
      icon.
    - **Unplated variants are generated.** Without them the taskbar sets the icon
      on an accent-coloured plate, which reads as a coloured square with something
      small in the middle.

    No unqualified base file is written for the manifest logos. MSIX resolves
    `Assets\Square44x44Logo.png` through the qualifiers beside it, and shipping both
    a bare file and a scale-100 file makes the two a duplicate pair.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Drawing

$assets = Join-Path $PSScriptRoot '..\src\MarketMotionStudio\Assets'
$assets = [System.IO.Path]::GetFullPath($assets)
New-Item -ItemType Directory -Force -Path $assets | Out-Null

# The body, and the three bars. Kept here rather than in the drawing routine so the
# palette is one edit and matches Render\Palette.cs by eye.
$body = [System.Drawing.Color]::FromArgb(255, 0x35, 0x50, 0x7A)
$bars = @(
    [System.Drawing.Color]::FromArgb(255, 0x2A, 0xC4, 0xD4),
    [System.Drawing.Color]::FromArgb(255, 0xF5, 0x9E, 0x2B),
    [System.Drawing.Color]::FromArgb(255, 0xE8, 0x3A, 0x3A)
)

function New-Mark {
    param([int]$Width, [int]$Height, [switch]$NoBody)

    $bmp = New-Object System.Drawing.Bitmap($Width, $Height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.Clear([System.Drawing.Color]::Transparent)

    # The mark is square and centred; a wide tile is the same drawing with more
    # transparent space either side, never a stretched one.
    $side = [Math]::Min($Width, $Height)
    $inset = [Math]::Max(1, [int]($side * 0.04))
    $box = $side - (2 * $inset)
    $ox = [int](($Width - $box) / 2)
    $oy = [int](($Height - $box) / 2)

    if (-not $NoBody) {
        $radius = [Math]::Max(2, [int]($box * 0.22))
        $path = New-Object System.Drawing.Drawing2D.GraphicsPath
        $d = $radius * 2
        $path.AddArc($ox, $oy, $d, $d, 180, 90)
        $path.AddArc($ox + $box - $d, $oy, $d, $d, 270, 90)
        $path.AddArc($ox + $box - $d, $oy + $box - $d, $d, $d, 0, 90)
        $path.AddArc($ox, $oy + $box - $d, $d, $d, 90, 90)
        $path.CloseFigure()

        $brush = New-Object System.Drawing.SolidBrush($body)
        $g.FillPath($brush, $path)
        $brush.Dispose()
        $path.Dispose()
    }

    # Three bars of rising height, on a shared baseline inside the body.
    $pad = $box * 0.20
    $innerLeft = $ox + $pad
    $innerWidth = $box - (2 * $pad)
    $baseline = $oy + $box - $pad
    $innerHeight = $box - (2 * $pad)

    $gap = $innerWidth * 0.14
    $barWidth = ($innerWidth - (2 * $gap)) / 3
    $heights = @(0.42, 0.70, 1.00)

    for ($i = 0; $i -lt 3; $i++) {
        $h = $innerHeight * $heights[$i]
        $x = $innerLeft + ($i * ($barWidth + $gap))
        $brush = New-Object System.Drawing.SolidBrush($bars[$i])
        $g.FillRectangle($brush, [float]$x, [float]($baseline - $h), [float]$barWidth, [float]$h)
        $brush.Dispose()
    }

    $g.Dispose()
    return $bmp
}

function Save-Mark {
    param([string]$Name, [int]$Width, [int]$Height, [switch]$NoBody)

    $bmp = New-Mark -Width $Width -Height $Height -NoBody:$NoBody
    $path = Join-Path $assets $Name
    $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
    "  {0,-52} {1}x{2}" -f $Name, $Width, $Height
}

"Writing to $assets"

# Square44x44Logo — the icon. Scale variants, then the target sizes the taskbar,
# Start and Alt+Tab draw, each also unplated.
foreach ($s in @(100, 125, 150, 200, 400)) {
    $px = [int](44 * $s / 100)
    Save-Mark "Square44x44Logo.scale-$s.png" $px $px
}

foreach ($t in @(16, 24, 32, 48, 256)) {
    Save-Mark "Square44x44Logo.targetsize-$t.png" $t $t
    Save-Mark "Square44x44Logo.targetsize-${t}_altform-unplated.png" $t $t
}

# Tiles and the store logo — artwork rather than icon, but the same mark: one file
# that survives 16 px needs no second drawing.
foreach ($s in @(100, 200)) {
    Save-Mark "Square71x71Logo.scale-$s.png"   ([int](71 * $s / 100))  ([int](71 * $s / 100))
    Save-Mark "Square150x150Logo.scale-$s.png" ([int](150 * $s / 100)) ([int](150 * $s / 100))
    Save-Mark "Square310x310Logo.scale-$s.png" ([int](310 * $s / 100)) ([int](310 * $s / 100))
    Save-Mark "Wide310x150Logo.scale-$s.png"   ([int](310 * $s / 100)) ([int](150 * $s / 100))
    Save-Mark "StoreLogo.scale-$s.png"         ([int](50 * $s / 100))  ([int](50 * $s / 100))
    Save-Mark "SplashScreen.scale-$s.png"      ([int](620 * $s / 100)) ([int](300 * $s / 100))
}

# Read by literal path and by ms-appx URI rather than resolved from the manifest,
# so these two are unqualified. The title-bar image is drawn at 20 effective pixels
# and supplied at 40 so a 200% display has something to downscale from.
Save-Mark "TitleBarLogo.png" 40 40

# The window's own icon. A correct manifest does not reach Alt+Tab or Task View:
# those read the window, which needs an .ico handed to AppWindow.SetIcon.
$icoSizes = @(16, 24, 32, 48, 64, 128, 256)
$pngs = @()

foreach ($s in $icoSizes) {
    $bmp = New-Mark -Width $s -Height $s
    $ms = New-Object System.IO.MemoryStream
    $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
    $pngs += , $ms.ToArray()
    $ms.Dispose()
    $bmp.Dispose()
}

# PNG-compressed entries (the Vista .ico form). Writing BMP entries by hand is the
# alternative and it gets the alpha wrong far more easily.
$icoPath = Join-Path $assets 'AppIcon.ico'
$fs = [System.IO.File]::Create($icoPath)
$bw = New-Object System.IO.BinaryWriter($fs)

$bw.Write([uint16]0)                     # reserved
$bw.Write([uint16]1)                     # type: icon
$bw.Write([uint16]$icoSizes.Count)

$offset = 6 + (16 * $icoSizes.Count)

for ($i = 0; $i -lt $icoSizes.Count; $i++) {
    $s = $icoSizes[$i]
    # 256 is recorded as 0: the field is one byte and 256 does not fit.
    $bw.Write([byte]($(if ($s -ge 256) { 0 } else { $s })))
    $bw.Write([byte]($(if ($s -ge 256) { 0 } else { $s })))
    $bw.Write([byte]0)                   # palette count
    $bw.Write([byte]0)                   # reserved
    $bw.Write([uint16]1)                 # colour planes
    $bw.Write([uint16]32)                # bits per pixel
    $bw.Write([uint32]$pngs[$i].Length)
    $bw.Write([uint32]$offset)
    $offset += $pngs[$i].Length
}

foreach ($p in $pngs) { $bw.Write($p) }

$bw.Dispose()
$fs.Dispose()
"  {0,-52} {1} sizes" -f 'AppIcon.ico', $icoSizes.Count

"Done."
