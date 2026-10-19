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
    /// The rows on the screenshot, top to bottom, or an empty list when the engine reads nothing.
    /// </summary>
    /// <param name="file">The image the reader picked.</param>
    /// <param name="chinese">Whether the Chinese recogniser was the one used.</param>
    public static async Task<(IReadOnlyList<string> Rows, bool Chinese)> ReadAsync(StorageFile file)
    {
        using var stream = await file.OpenAsync(FileAccessMode.Read);

        var decoder = await BitmapDecoder.CreateAsync(stream);

        using var bitmap = await decoder.GetSoftwareBitmapAsync();

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

        return (TradeText.Rows(words), engine.RecognizerLanguage.LanguageTag.StartsWith("zh", StringComparison.OrdinalIgnoreCase));
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
