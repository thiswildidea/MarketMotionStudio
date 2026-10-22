using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace MarketMotionStudio.Views;

/// <summary>One row of the preview, already formatted: the list renders strings, not records.</summary>
public sealed class ParsedRow(string line)
{
    public string Line { get; } = line;
}

/// <summary>
/// Imports a day's filled orders from a broker workbook, or a list typed in, then a
/// preview of exactly what will be applied.
///
/// <para>
/// **Nothing is applied until it has been shown.** A wrong share count that goes straight into
/// the book is a wrong video that nobody traces back to this dialog. So the read text lands in
/// an editable box, the parse is shown row by row, and the primary button only becomes available
/// once something has been read.
/// </para>
///
/// <para>
/// **A row without a 买入 / 卖出 word is not importable here.** The workbook always carries the
/// direction in its own column, so a direction-less row means text typed or pasted by hand —
/// and a direction the page guessed would be a position that never existed. Such rows are shown
/// in the preview and hold the import until the reader adds the word to the text itself.
/// </para>
///
/// <para>
/// The day is asked for rather than assumed: the reader imports the day's orders after the close,
/// and an import made after midnight would otherwise file them under the wrong session.
/// </para>
/// </summary>
public sealed partial class TradeImportDialog : ContentDialog
{
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

    private void OnParse(object sender, RoutedEventArgs e) => Parse();

    /// <summary>
    /// Reads a broker's order workbook. The rows land in the same editable box a reader types in,
    /// so from here on there is exactly one path: parse, preview, apply — whatever the source was.
    /// </summary>
    private async void OnPickSheet(object sender, RoutedEventArgs e)
    {
        if (App.Window is not { } window)
        {
            return;
        }

        var picker = new Windows.Storage.Pickers.FileOpenPicker
        {
            SuggestedStartLocation = Windows.Storage.Pickers.PickerLocationId.DocumentsLibrary,
            ViewMode = Windows.Storage.Pickers.PickerViewMode.List,
        };

        picker.FileTypeFilter.Add(".xlsx");

        WinRT.Interop.InitializeWithWindow.Initialize(
            picker, WinRT.Interop.WindowNative.GetWindowHandle(window));

        if (await picker.PickSingleFileAsync() is not { } file)
        {
            return;
        }

        SheetButton.IsEnabled = false;
        Note.Text = Strings.Get("PortfolioImportReading");

        try
        {
            var lines = await TradeSheet.ReadAsync(file);

            if (lines.Count == 0)
            {
                Note.Text = Strings.Get("PortfolioImportNothing");
                return;
            }

            Raw.Text = string.Join("\n", lines);

            Parse();
        }
        catch (Exception ex)
        {
            Note.Text = Strings.Reason(ex);
        }
        finally
        {
            SheetButton.IsEnabled = true;
        }
    }

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

        var rows = new List<ParsedRow>();

        foreach (var t in result.Trades)
        {
            rows.Add(new ParsedRow(Describe(t)));
        }

        foreach (var block in result.Incomplete)
        {
            // Shown so the reader can see which lines are holding the import back. Without a
            // direction there is nothing to apply, and the note below says what is missing.
            rows.Add(new ParsedRow(block));
        }

        Preview.ItemsSource = rows;

        Note.Text = BuildNote(result);
        IsPrimaryButtonEnabled = CanApply(result);
    }

    /// <summary>Whether the primary button may apply: something parsed, nothing unreadable, and
    /// no row missing its direction.</summary>
    private bool CanApply(TradeParse result) =>
        result.Trades.Count > 0
        && result.Skipped.Count == 0
        && result.Incomplete.Count == 0;

    private string BuildNote(TradeParse result)
    {
        if (result.Trades.Count == 0 && result.Incomplete.Count == 0)
        {
            return Strings.Get("PortfolioImportNothing");
        }

        var note = Strings.Format("PortfolioImportParsed", result.Trades.Count, result.Skipped.Count);

        if (result.Incomplete.Count > 0)
        {
            note += $"（有 {result.Incomplete.Count} 行缺买卖方向，补上才能导入）";
        }

        return note;
    }

    /// <summary>
    /// One row, written the way the table reads: direction, name and code, price times size,
    /// clock. It is the only chance the reader gets to see that the import read 5900 instead of
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

        // A direction-less row has nobody to ask any more — the preview shows it, the note says
        // what is missing, and applying a trade whose side the page guessed would be inventing a
        // position. The reader adds the word to the text and the gate opens.
        if (result.Incomplete.Count > 0)
        {
            args.Cancel = true;
            Note.Text = $"有 {result.Incomplete.Count} 行缺买卖方向，补上才能导入";
            return;
        }

        Trades = [.. result.Trades.Select(t =>
            new PortfolioTrade(Chosen, t.Time, t.Code, t.Name, t.Side, t.Price, t.Shares))];
    }
}
