using System;
using System.Collections.Generic;
using System.Runtime.InteropServices.WindowsRuntime;
using Windows.Globalization;
using Windows.Graphics.Imaging;
using Windows.Media.Ocr;
using Windows.Storage;
using Windows.Storage.Streams;

namespace MarketMotionStudio.Market;

/// <summary>
/// Reads the text off a screenshot of a broker's order list.
///
/// <para>
/// **Windows' own OCR, not a service.** The picture is a phone screenshot of an account's trades;
/// sending it anywhere would be sending somebody's positions to somebody else. The engine ships
/// with the system, and this is the only place in this app that uses it.
/// </para>
///
/// <para>
/// **Chinese first, then whatever the machine has.** The broker app these screenshots come from
/// prints 买入 and 卖出 whatever language this app is running in, so the recogniser is asked for
/// Simplified Chinese and falls back to the profile's languages only when that pack is absent —
/// in which case the numbers and the codes still read, the names do not, and the caller is told.
/// </para>
///
/// <para>
/// The rows come back as text, not as trades: reading a table into a position is
/// <see cref="TradeText"/>'s job, and keeping the two apart is what lets the same parser serve a
/// pasted list from a phone that has no screenshot at all.
/// </para>
/// </summary>
public static class ScreenshotText
{
    /// <summary>
    /// The width the recogniser does best at, in pixels.
    ///
    /// Not a guess and not a taste: measured on the day's own order list, cropped to 307×235 —
    /// which is what a snip of a phone screenshot on a desktop actually is — the engine read
    /// **zero** trades at its own size, three at twice the size, and two at three times. Below
    /// about 10 px of text height it reads the decimal point as a middle dot, the colon of a
    /// clock as a semicolon, and Chinese names as other Chinese names; at 2× the same picture
    /// reads cleanly. Above that the strokes thicken and it starts misreading digits again.
    /// </summary>
    private const double TargetWidth = 700;

    /// <summary>How far up it is worth going: past this the strokes merge and it reads worse.</summary>
    private const int MaxFactor = 3;

    /// <summary>
    /// The rows on the screenshot, top to bottom, or an empty list when the engine reads nothing.
    /// </summary>
    /// <param name="file">The image the reader picked.</param>
    /// <param name="chinese">Whether the Chinese recogniser was the one used.</param>
    public static async Task<(IReadOnlyList<string> Rows, bool Chinese)> ReadAsync(StorageFile file)
    {
        using var stream = await file.OpenAsync(FileAccessMode.Read);

        var decoder = await BitmapDecoder.CreateAsync(stream);

        var factor = Factor((int)decoder.PixelWidth);
        var (words, chinese) = await WordsAndLanguage(decoder, factor);
        var rows = TradeText.Rows(words);

        // **A row the engine read without its 买入 / 卖出 is the commonest thing it loses**, and
        // it is lost for a reason: on these lists the direction word is the only *coloured* text
        // on a dark background, and the recogniser drops coloured text on dark far more readily
        // than white. When a row is unusable for want of that word, the picture is read again with
        // everything but the colour wiped to white — on white the word comes through — and the
        // words are put back on their rows by band. The bigger (2×) reading is kept only as a
        // fallback for the rare list where the colour mask finds nothing.
        if (TradeText.Incomplete(rows))
        {
            var sides = await RecoverSides(decoder, factor);

            rows = sides.Count > 0
                ? TradeText.Attach(TradeText.RowBoxes(words), sides)
                : TradeText.Merge(rows, (await Recognise(decoder, Math.Min(factor * 2, MaxFactor * 2))).Rows);
        }

        return (rows, chinese);
    }

    /// <summary>The words on the picture at <paramref name="factor"/>, with the boxes they sat in.</summary>
    private static async Task<(IReadOnlyList<OcrWord> Words, bool Chinese)> WordsAndLanguage(
        BitmapDecoder decoder, int factor)
    {
        using var bitmap = await Scaled(decoder, factor);

        var engine = Engine();

        if (engine is null)
        {
            throw new InvalidOperationException(Install());
        }

        var result = await engine.RecognizeAsync(bitmap);

        var words = new List<OcrWord>();

        foreach (var line in result.Lines)
        {
            foreach (var word in line.Words)
            {
                var box = word.BoundingRect;

                words.Add(new OcrWord(word.Text, box.X, box.Y, box.Height));
            }
        }

        return (words, engine.RecognizerLanguage.LanguageTag.StartsWith("zh", StringComparison.OrdinalIgnoreCase));
    }

    /// <summary>One pass: the picture at <paramref name="factor"/>, read into rows.</summary>
    private static async Task<(IReadOnlyList<string> Rows, bool Chinese)> Recognise(
        BitmapDecoder decoder, int factor)
    {
        var (words, chinese) = await WordsAndLanguage(decoder, factor);

        return (TradeText.Rows(words), chinese);
    }

    /// <summary>
    /// The direction words the colour mask can recover, banded by the row they sat in.
    ///
    /// The masked picture is the same one the first reading used, only with every pixel that is
    /// not clearly coloured painted white; coloured text on white is what the recogniser reads
    /// cleanly, and the direction words are the only coloured text a broker's order list carries.
    /// <see cref="TradeText.Attach"/> needs the bands, so this returns rows rather than plain text.
    /// </summary>
    private static async Task<IReadOnlyList<TradeText.TextRow>> RecoverSides(BitmapDecoder decoder, int factor)
    {
        try
        {
            using var bitmap = await Scaled(decoder, factor);

            using var masked = ColorMask(bitmap);

            var engine = Engine();

            if (engine is null)
            {
                return [];
            }

            var result = await engine.RecognizeAsync(masked);

            var words = new List<OcrWord>();

            foreach (var line in result.Lines)
            {
                foreach (var word in line.Words)
                {
                    var box = word.BoundingRect;

                    words.Add(new OcrWord(word.Text, box.X, box.Y, box.Height));
                }
            }

            return TradeText.RowBoxes(words);
        }
        catch (Exception)
        {
            // The mask is a bonus recovery, never worth blocking the import over: an image the
            // colour pass cannot read simply falls back to the bigger (2×) reading.
            return [];
        }
    }

    /// <summary>
    /// A copy of the bitmap with every pixel that is not clearly coloured painted white.
    ///
    /// **Kept as a second reading, not a replacement.** The first reading reads the names, the
    /// codes, the prices and the clocks — everything white on the broker's dark list — and this
    /// one only ever adds the direction words, which are the part the first one drops. A pixel
    /// survives when it is saturated (a real colour, not white text and not the dark background)
    /// and bright enough to be text rather than a faint ghost. Measured on the day's own list:
    /// this reading recovered all seven direction words where the first reading found one.
    /// </summary>
    private static SoftwareBitmap ColorMask(SoftwareBitmap source)
    {
        var width = (int)source.PixelWidth;
        var height = (int)source.PixelHeight;
        var output = new SoftwareBitmap(BitmapPixelFormat.Bgra8, width, height, BitmapAlphaMode.Premultiplied);

        // **Read and write through `SoftwareBitmap` itself.** The `IMemoryBufferReference`
        // buffer/stream extensions this projection ships without are not needed: `CopyToBuffer`
        // pulls the pixels into a byte array (via the `byte[]` `AsBuffer` overload that *is*
        // present) and `CopyFromBuffer` pushes them back, both in the bitmap's own BGRA order.
        int pitch;

        using (var probe = source.LockBuffer(BitmapBufferAccessMode.Read))
        {
            pitch = probe.GetPlaneDescription(0).Stride;
        }

        var bytes = new byte[pitch * height];
        source.CopyToBuffer(bytes.AsBuffer());

        var result = new byte[bytes.Length];

        for (var y = 0; y < height; y++)
        {
            var row = y * pitch;

            for (var x = 0; x < width; x++)
            {
                var i = row + (x * 4);
                var b = bytes[i];
                var g = bytes[i + 1];
                var r = bytes[i + 2];

                var max = Math.Max(r, Math.Max(g, b));
                var min = Math.Min(r, Math.Min(g, b));
                var sat = max == 0 ? 0.0 : (max - min) / (double)max;

                var o = row + (x * 4);

                // Keep only a real colour that is bright enough to be text; everything else —
                // white names, dark background, grey anti-aliasing — becomes white.
                if (sat > 0.35 && max > 90)
                {
                    result[o] = b;
                    result[o + 1] = g;
                    result[o + 2] = r;
                }
                else
                {
                    result[o] = 255;
                    result[o + 1] = 255;
                    result[o + 2] = 255;
                }

                result[o + 3] = 255;
            }
        }

        output.CopyFromBuffer(result.AsBuffer());

        return output;
    }

    /// <summary>How far up the picture is blown before it is handed to the engine.</summary>
    private static int Factor(int width) =>
        width <= 0 ? 1 : Math.Clamp((int)Math.Round(TargetWidth / width), 1, MaxFactor);

    /// <summary>
    /// The picture blown up to a size the recogniser can read, or as it came when it is already
    /// that size.
    ///
    /// **A cropped screenshot is the ordinary input and the worst case.** A phone screenshot is
    /// 1080 wide and the engine reads it as it stands; a 300-pixel snip of one is below the
    /// engine's floor, and the failure is silent — it returns text, just wrong text ("48.10" as
    /// "4 & 10", "13:55:22" as "13 ： 55 ： 22"), which the parser then refuses row by row until
    /// the dialog says it read nothing at all. Scaling up is the whole fix: nothing else about
    /// the picture is changed, no threshold, no inversion — measured, inverting a dark
    /// screenshot makes the names worse.
    /// </summary>
    private static async Task<SoftwareBitmap> Scaled(BitmapDecoder decoder, int factor)
    {
        var width = (int)decoder.PixelWidth;
        var height = (int)decoder.PixelHeight;

        if (factor <= 1 || width <= 0 || height <= 0)
        {
            return await decoder.GetSoftwareBitmapAsync();
        }

        var transform = new BitmapTransform
        {
            ScaledWidth = (uint)(width * factor),
            ScaledHeight = (uint)(height * factor),
            InterpolationMode = BitmapInterpolationMode.Fant,
        };

        return await decoder.GetSoftwareBitmapAsync(
            BitmapPixelFormat.Bgra8, BitmapAlphaMode.Premultiplied, transform,
            ExifOrientationMode.IgnoreExifOrientation, ColorManagementMode.DoNotColorManage);
    }

    /// <summary>
    /// The recogniser to use: Simplified Chinese when it is installed, otherwise the machine's own
    /// languages, otherwise the first language the engine admits to having.
    /// </summary>
    private static OcrEngine? Engine()
    {
        try
        {
            return OcrEngine.TryCreateFromLanguage(new Language("zh-Hans"))
                ?? OcrEngine.TryCreateFromUserProfileLanguages()
                ?? (OcrEngine.AvailableRecognizerLanguages.Count > 0
                    ? OcrEngine.TryCreateFromLanguage(OcrEngine.AvailableRecognizerLanguages[0])
                    : null);
        }
        catch (Exception)
        {
            // A machine with no recogniser at all is a machine where this feature cannot work,
            // and the caller says so in the reader's language rather than showing an exception.
            return null;
        }
    }

    /// <summary>What to tell someone whose Windows has no OCR pack.</summary>
    private static string Install() => Localization.Strings.Get("PortfolioImportNoOcr");
}
