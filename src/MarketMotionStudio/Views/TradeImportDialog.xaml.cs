using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace MarketMotionStudio.Views;

/// <summary>
/// One line of the filed-trades table, already formatted.
///
/// **Formatted here rather than in the template** because a `DataTemplate` cannot call
/// `Strings.Get`: the direction word and the number formats are the dialog's business, and the
/// table's is to lay them out in columns. It is also what keeps the header and the rows from
/// disagreeing about what a column means.
/// </summary>
/// <param name="Number">Its place in the record, 1-based, oldest first.</param>
public sealed class TradeRow(
    string number,
    string day,
    string time,
    string side,
    string display,
    string price,
    string shares)
{
    public string Number { get; } = number;

    public string Day { get; } = day;

    public string Time { get; } = time;

    public string Side { get; } = side;

    /// <summary>
    /// The name, and **not called `Name`**: a `{x:Bind Name}` on a `TextBlock` resolves against
    /// `FrameworkElement.Name` first, and the compiler crashes on the ambiguity rather than
    /// reporting it (`Xaml Internal Error WMC9999`, with a message about missing resources that
    /// has nothing to do with the cause).
    /// </summary>
    public string Display { get; } = display;

    public string Price { get; } = price;

    public string Shares { get; } = shares;
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
        CloseButtonText = Strings.Get("PortfolioDialogClose");

        Day.Date = new DateTimeOffset(day.ToDateTime(TimeOnly.MinValue), TimeSpan.Zero);
        Day.MaxYear = new DateTimeOffset(DateTime.Today.AddYears(1));

        ApplyButton.IsEnabled = false;

        Note.Text = Strings.Get("PortfolioImportEmpty");

        LoadHistory();
    }

    /// <summary>
    /// Whether a whole-record import changed anything while the dialog was open.
    ///
    /// The pages use it to decide whether to re-read: an import here writes the archive itself,
    /// and the curves behind the dialog are drawn from what was in it a minute ago.
    /// </summary>
    public bool ArchiveChanged { get; private set; }

    /// <summary>
    /// A file chosen but not yet applied, waiting for the second press on 全量导入.
    ///
    /// Held rather than applied because replacing the archive is the one act in this dialog that
    /// cannot be undone — see the two-press note on <see cref="OnImportArchive"/>.
    /// </summary>
    private IReadOnlyList<PortfolioTrade>? _pendingReplace;

    /// <summary>
    /// Puts the archive on the dialog as a table, oldest first.
    ///
    /// **Oldest first, because this list answers "what do I have".** A reader checking that a
    /// whole-record import landed reads down from where their record starts; a broker's own app
    /// lists the newest first because it is answering "what did I just do", which is a different
    /// question and is what the preview above is for.
    /// </summary>
    private void LoadHistory()
    {
        Ledger.EnsureLoaded();

        var rows = Ledger.Archive
            .OrderBy(t => t.Day, StringComparer.Ordinal)
            .ThenBy(t => t.Time, StringComparer.Ordinal)
            .ToList();

        ArchiveExportButton.IsEnabled = rows.Count > 0;

        HistoryNote.Text = rows.Count == 0
            ? Strings.Get("TradeHistoryEmpty")
            : Strings.Format(
                "TradeHistorySummary",
                rows.Count.ToString(CultureInfo.InvariantCulture),
                rows[0].Day,
                rows[^1].Day);

        History.ItemsSource = rows
            .Select((t, i) => ToRow(t, i + 1))
            .ToList();
    }

    /// <summary>One table row: number, day, clock, direction, name and code, price, size.</summary>
    private static TradeRow ToRow(PortfolioTrade trade, int number) =>
        new(
            number.ToString(CultureInfo.InvariantCulture),
            trade.Day.Length >= 10 ? trade.Day[5..] : trade.Day,
            trade.Time,
            Strings.Get(trade.Side == TradeSide.Buy ? "PortfolioImportBuy" : "PortfolioImportSell"),
            InstrumentNames.Display(trade.Code, trade.Name),
            trade.Price.ToString("0.###", CultureInfo.InvariantCulture),
            trade.Shares.ToString("#,##0", CultureInfo.InvariantCulture));

    /// <summary>
    /// Writes the whole archive out. This is the export that used to live in 管理持仓: it was moved
    /// here because this is the page that owns the record — the place a reader comes to see what is
    /// filed is the place they should be able to take it away.
    /// </summary>
    private async void OnExportArchive(object sender, RoutedEventArgs e)
    {
        Ledger.EnsureLoaded();

        if (Ledger.Archive.Count == 0)
        {
            Note.Text = Strings.Get("LedgerArchiveEmpty");

            return;
        }

        ArchiveExportButton.IsEnabled = false;

        try
        {
            if (await CsvFiles.WriteAsync("trades", Ledger.TradesToCsv(Ledger.Archive)))
            {
                Note.Text = Strings.Format(
                    "TradeHistoryExported",
                    Ledger.Archive.Count.ToString(CultureInfo.InvariantCulture));
            }
        }
        catch (Exception ex)
        {
            Note.Text = Strings.Reason(ex);
        }
        finally
        {
            ArchiveExportButton.IsEnabled = true;
        }
    }

    /// <summary>
    /// Replaces the whole archive with a file — the exact file 全量导出 writes.
    ///
    /// <para>
    /// **It asks first, in two clicks rather than in a second dialog.** WinUI refuses to open a
    /// dialog over a dialog — <c>Only a single ContentDialog can be open at any time</c> — so the
    /// confirmation cannot be a message box; it is the same button, given a different name and a
    /// line that says what the click will cost. First press picks the file and states the trade
    /// ("5 fills in, 46 out"); second press does it. The reader who only wanted to look at the
    /// file stops after the first press and nothing has happened.
    /// </para>
    ///
    /// <para>
    /// **Nothing in this app can bring back an archive that was overwritten by the wrong file.**
    /// The fills came from a broker, the old journal has long since folded them away, and there is
    /// no second copy — which is why the count of what will be lost is in the sentence rather than
    /// a "are you sure" that gets dismissed without being read.
    /// </para>
    ///
    /// <para>
    /// **Every row has to read, and every row has to carry its day.** A whole-record file is a
    /// record of many days; a file whose rows have none is a day's orders that arrived in the
    /// wrong dialog, and replacing a year with it would be the worst possible reading.
    /// </para>
    /// </summary>
    private async void OnImportArchive(object sender, RoutedEventArgs e)
    {
        // Second press: the file was chosen and the cost was stated on the first one.
        if (_pendingReplace is { } pending)
        {
            _pendingReplace = null;
            ArchiveImportButton.Content = Strings.Get("TradeHistoryImport.Content");

            Replace(pending);

            return;
        }

        ArchiveImportButton.IsEnabled = false;

        try
        {
            if (await CsvFiles.ReadAsync("PortfolioDialogSheetEncoding") is not { } text)
            {
                return;
            }

            var parsed = TradeText.Parse(text);

            if (parsed.Trades.Count == 0 || parsed.Trades.Any(t => t.Day.Length == 0))
            {
                Note.Text = parsed.Trades.Count == 0
                    ? Strings.Get("TradeHistoryImportShape")
                    : Strings.Get("TradeHistoryImportUndated");

                return;
            }

            var trades = parsed.Trades
                .Select(t => new PortfolioTrade(
                    t.Day, t.Time, t.Code, t.Name, t.Side, t.Price, t.Shares))
                .ToList();

            // An empty archive loses nothing, so there is nothing to ask about.
            if (Ledger.Archive.Count == 0)
            {
                Replace(trades);

                return;
            }

            _pendingReplace = trades;

            ArchiveImportButton.Content = Strings.Format(
                "TradeHistoryImportConfirm.Content",
                trades.Count.ToString(CultureInfo.InvariantCulture));

            Note.Text = Strings.Format(
                "TradeHistoryReplaceAsk",
                trades.Count.ToString(CultureInfo.InvariantCulture),
                Ledger.Archive.Count.ToString(CultureInfo.InvariantCulture));
        }
        catch (Exception ex)
        {
            Note.Text = Strings.Reason(ex);
        }
        finally
        {
            ArchiveImportButton.IsEnabled = true;
        }
    }

    /// <summary>Does the replacement and says what it came to.</summary>
    private void Replace(IReadOnlyList<PortfolioTrade> trades)
    {
        var result = Ledger.Import(trades, overwrite: true);

        ArchiveChanged = true;

        LoadHistory();

        Note.Text = Strings.Format(
            "TradeHistoryImported",
            result.After.ToString(CultureInfo.InvariantCulture),
            result.Before.ToString(CultureInfo.InvariantCulture));
    }

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

        // Table rows, not prose: the same seven columns the archive uses, in the same order, at the
        // same widths — so a row about to be filed can be read against a row already filed.
        Preview.ItemsSource = result.Trades
            .Select((t, i) => ToRow(t, i + 1))
            .ToList();

        // **The rows that could not become cells.** A line with no direction has nothing for the
        // 方向 column and a line that read as nothing at all has nothing for any of them; both are
        // shown under the table as the text they are, so the reader can see which line is holding
        // the import back rather than only being told how many there are.
        Problems.Text = string.Join(
            "\n",
            result.Incomplete.Concat(result.Skipped).Select(line => "· " + line));

        PreviewPanel.Visibility = result.Trades.Count > 0 || Problems.Text.Length > 0
            ? Visibility.Visible
            : Visibility.Collapsed;

        Note.Text = BuildNote(result) + DuplicateNote(result);
        ApplyButton.IsEnabled = CanApply(result);
    }

    /// <summary>
    /// One parsed fill as a table row.
    ///
    /// The day is the row's own when it names one, and the picker's when it does not — the same
    /// rule <see cref="OnApply"/> files by, so the preview cannot promise a day the import will not
    /// use. Empty stays empty rather than borrowing today: a row with no date and no picker behind
    /// it has nothing true to show.
    /// </summary>
    private TradeRow ToRow(ParsedTrade trade, int number)
    {
        var day = trade.Day.Length > 0 ? trade.Day : Chosen;

        return new TradeRow(
            number.ToString(CultureInfo.InvariantCulture),
            day.Length >= 10 ? day[5..] : day,
            trade.Time,
            Strings.Get(trade.Side == TradeSide.Buy ? "PortfolioImportBuy" : "PortfolioImportSell"),
            InstrumentNames.Display(trade.Code, trade.Name),
            trade.Price.ToString("0.###", CultureInfo.InvariantCulture),
            trade.Shares.ToString("#,##0", CultureInfo.InvariantCulture));
    }

    /// <summary>
    /// How many of the parsed rows the archive already holds, as a sentence, or empty.
    ///
    /// **This is what "must not be imported twice" looks like from the reader's side.** The
    /// archive dedupes by fingerprint on every import, so a second paste of the same list applies
    /// nothing — but a number that only appears afterwards tells them their list was wrong when in
    /// fact it was simply already filed. Counted before, the same fact reads as "nothing to do".
    /// </summary>
    private string DuplicateNote(TradeParse result)
    {
        if (result.Trades.Count == 0)
        {
            return string.Empty;
        }

        // The day a row will be filed under: its own when it has one, the picker's when it does
        // not — the same rule `OnApply` uses, so this count is about the rows that would be filed.
        var asFiled = result.Trades
            .Select(t => new PortfolioTrade(
                t.Day.Length > 0 ? t.Day : Chosen, t.Time, t.Code, t.Name, t.Side, t.Price, t.Shares))
            .ToList();

        var filed = Ledger.AlreadyFiled(asFiled);

        return filed == 0
            ? string.Empty
            : "  " + Strings.Format(
                "TradeImportDuplicates", filed.ToString(CultureInfo.InvariantCulture));
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
    /// Applies the day's list — here, in the dialog, and without closing it.
    ///
    /// <para>
    /// **It used to hand the rows back to the page and close.** That made the dialog a form: the
    /// reader pressed 导入, the dialog vanished, and whether the record took the rows could only be
    /// seen by reopening it. The archive is now on this dialog, so the import has to happen where
    /// the archive is — otherwise the table under it is a picture of the state before the click.
    /// </para>
    ///
    /// <para>
    /// **Any skipped row cancels the import.** A list where one of six rows could not be read is
    /// a book that will be five trades out of date, and the page has no way to say so afterwards
    /// — the arithmetic is right, the position is wrong. Better to refuse the import and let the
    /// reader fix the row than to apply the five.
    /// </para>
    /// </summary>
    private void OnApply(object sender, RoutedEventArgs e)
    {
        var result = TradeText.Parse(Raw.Text);

        if (result.Trades.Count == 0 || result.Skipped.Count > 0)
        {
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
            Note.Text = $"有 {result.Incomplete.Count} 行缺买卖方向，补上才能导入";

            return;
        }

        // **Each row keeps the day it names.** A record exported from 管理持仓 carries its own
        // dates; folding a year of them onto the one day the picker holds would file them all in
        // a morning. A row that names no day — a screen of today's fills — gets the picker's,
        // which is what the picker is for.
        var trades = result.Trades
            .Select(t => new PortfolioTrade(
                t.Day.Length > 0 ? t.Day : Chosen,
                t.Time, t.Code, t.Name, t.Side, t.Price, t.Shares))
            .ToList();

        var book = Portfolio.Apply(trades);
        var archived = Ledger.Import(trades, overwrite: false);

        ArchiveChanged = true;

        // The table below is the point of doing this here: it must show the rows that were just
        // filed, or the reader presses 导入, reads "已导入 6 笔", and sees an unchanged list.
        LoadHistory();

        Note.Text = Strings.Format(
            "PortfolioPnlImported", book.Applied, book.Duplicates, book.Unmatched)
            + " · " + Strings.Format(
                "LedgerArchiveDone",
                archived.Applied.ToString(CultureInfo.InvariantCulture),
                archived.Duplicates.ToString(CultureInfo.InvariantCulture),
                archived.After.ToString(CultureInfo.InvariantCulture));

        // The text has been applied; leaving it there invites a second press that would apply
        // nothing and report "46 duplicates", which reads as a failure.
        Raw.Text = string.Empty;
        Preview.ItemsSource = null;
        Problems.Text = string.Empty;
        PreviewPanel.Visibility = Visibility.Collapsed;
        ApplyButton.IsEnabled = false;
    }
}
