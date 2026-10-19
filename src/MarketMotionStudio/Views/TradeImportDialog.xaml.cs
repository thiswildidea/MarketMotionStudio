using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace MarketMotionStudio.Views;

/// <summary>One parsed trade, already written out: the preview renders strings.</summary>
public sealed class ParsedRow(string line)
{
    public string Line { get; } = line;
}

/// <summary>
/// Imports a day's filled orders: a screenshot the system reads, or a list typed in, then a
/// preview of exactly what will be applied.
///
/// <para>
/// **Nothing is applied until it has been shown.** OCR on a table is good and not perfect — it
/// reads 48.10 correctly all morning and then finds a smudge — and a wrong share count that goes
/// straight into the book is a wrong video that nobody traces back to this dialog. So the
/// recognised text lands in an editable box, the parse is shown row by row, and the primary
/// button only becomes available once something has been read.
/// </para>
///
/// <para>
/// The day is asked for rather than assumed: the reader imports the day's orders after the close,
/// and an import made after midnight would otherwise file them under the wrong session.
/// </para>
/// </summary>
public sealed partial class TradeImportDialog : ContentDialog
{
    private readonly List<ParsedTrade> _parsed = [];

    public TradeImportDialog(DateOnly day)
    {
        InitializeComponent();

        Title = Strings.Get("PortfolioImportTitle");
        PrimaryButtonText = Strings.Get("PortfolioImportApply");
        CloseButtonText = Strings.Get("PortfolioDialogClose");

        Day.Date = new DateTimeOffset(day.ToDateTime(TimeOnly.MinValue), TimeSpan.Zero);
        Day.MaxYear = new DateTimeOffset(DateTime.Today.AddYears(1));

        IsPrimaryButtonEnabled = false;

        Note.Text = Strings.Get("PortfolioImportEmpty");
    }

    /// <summary>What the dialog will apply, in the day chosen.</summary>
    public IReadOnlyList<PortfolioTrade> Trades { get; private set; } = [];

    /// <summary>The day the trades belong to, as the picker has it.</summary>
    private string Chosen => Day.Date.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

    private async void OnPick(object sender, RoutedEventArgs e)
    {
        if (App.Window is not { } window)
        {
            return;
        }

        var picker = new Windows.Storage.Pickers.FileOpenPicker
        {
            SuggestedStartLocation = Windows.Storage.Pickers.PickerLocationId.PicturesLibrary,
            ViewMode = Windows.Storage.Pickers.PickerViewMode.Thumbnail,
        };

        foreach (var type in (string[])[" .png", ".jpg", ".jpeg", ".bmp"])
        {
            picker.FileTypeFilter.Add(type.Trim());
        }

        WinRT.Interop.InitializeWithWindow.Initialize(
            picker, WinRT.Interop.WindowNative.GetWindowHandle(window));

        if (await picker.PickSingleFileAsync() is not { } file)
        {
            return;
        }

        PickButton.IsEnabled = false;
        Note.Text = Strings.Get("PortfolioImportReading");

        try
        {
            var (rows, chinese) = await ScreenshotText.ReadAsync(file);

            Raw.Text = string.Join("\n", rows);

            Parse();

            if (!chinese)
            {
                Note.Text = Strings.Get("PortfolioImportNoChinese");
            }
        }
        catch (Exception ex)
        {
            Note.Text = Strings.Reason(ex);
        }
        finally
        {
            PickButton.IsEnabled = true;
        }
    }

    private void OnParse(object sender, RoutedEventArgs e) => Parse();

    /// <summary>
    /// Re-parses on every edit, so the count next to the button is never describing text that is
    /// no longer there. Cheap: a day's orders is a few dozen lines of regular expressions.
    /// </summary>
    private void OnRawChanged(object sender, TextChangedEventArgs e)
    {
        if (Raw.Text.Trim().Length > 0)
        {
            Parse();
        }
    }

    private void Parse()
    {
        var result = TradeText.Parse(Raw.Text);

        _parsed.Clear();
        _parsed.AddRange(result.Trades);

        Preview.ItemsSource = result.Trades
            .Select(t => new ParsedRow(Describe(t)))
            .ToList();

        Note.Text = result.Trades.Count == 0
            ? Strings.Get("PortfolioImportNothing")
            : Strings.Format("PortfolioImportParsed", result.Trades.Count, result.Skipped.Count);

        IsPrimaryButtonEnabled = result.Trades.Count > 0 && result.Skipped.Count == 0;
    }

    /// <summary>
    /// One row, written the way the table reads: direction, name and code, price times size,
    /// clock. It is the only chance the reader gets to see that the OCR read 5900 instead of
    /// 590.
    /// </summary>
    private string Describe(ParsedTrade trade)
    {
        var side = trade.Side == TradeSide.Buy
            ? Strings.Get("PortfolioImportBuy")
            : Strings.Get("PortfolioImportSell");

        var name = InstrumentNames.Display(trade.Code, trade.Name);

        return Strings.Format(
            "PortfolioImportRow",
            side,
            name,
            trade.Code.ToUpperInvariant(),
            trade.Price.ToString("0.###", CultureInfo.InvariantCulture),
            trade.Shares.ToString("#,##0", CultureInfo.InvariantCulture),
            trade.Time);
    }

    /// <summary>
    /// Applies on the primary button.
    ///
    /// **Any skipped row cancels the import.** A list where one of six rows could not be read is
    /// a book that will be five trades out of date, and the page has no way to say so afterwards
    /// — the arithmetic is right, the position is wrong. Better to refuse the import and let the
    /// reader fix the row than to apply the five.
    /// </summary>
    private void OnApply(ContentDialog sender, ContentDialogButtonClickEventArgs args)
    {
        var result = TradeText.Parse(Raw.Text);

        if (result.Trades.Count == 0 || result.Skipped.Count > 0)
        {
            args.Cancel = true;

            Note.Text = result.Trades.Count == 0
                ? Strings.Get("PortfolioImportNothing")
                : Strings.Format("PortfolioImportSkipped", result.Skipped.Count);

            return;
        }

        var day = Chosen;

        Trades = [.. result.Trades.Select(t =>
            new PortfolioTrade(day, t.Time, t.Code, t.Name, t.Side, t.Price, t.Shares))];
    }
}
