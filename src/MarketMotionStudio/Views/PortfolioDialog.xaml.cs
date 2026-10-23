using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Automation;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;

namespace MarketMotionStudio.Views;

/// <summary>
/// One row of the suggestion list: the instrument, written the way the row it becomes will read.
///
/// A wrapper rather than the <see cref="StockRef"/> itself because the list is bound through
/// `TextMemberPath`, and what a reader needs to see is the **name and the code together** — 顺丰
/// 控股 is listed in two cities, and a list of two identical names is a list with no answer in it.
/// </summary>
public sealed record StockChoice(StockRef Stock)
{
    /// <summary>`顺丰控股 · SZ002352`.</summary>
    public string Display =>
        $"{InstrumentNames.Display(Stock.Code, Stock.Name)} · {Stock.Code.ToUpperInvariant()}";

    /// <summary>
    /// What the suggestion list draws. **A record's own <c>ToString</c> is its field dump**, and
    /// that is what the list was showing: four rows of `StockChoice { Stock = StockRef { … } }`
    /// instead of four names (实测截图). `TextMemberPath` feeds the *box* the chosen text; the
    /// list itself falls back to `ToString`, so the display has to be spelled out here.
    /// </summary>
    public override string ToString() => Display;
}

/// <summary>
/// Edits the book: add a holding by code or by name, remove one, or correct the size and cost of
/// one already there.
///
/// <para>
/// **Edits are applied as they are made**, and there is one button, which closes. A dialog with
/// OK/Cancel would need a second copy of the book to hold the edits, and the only thing that buys
/// is the ability to abandon them — on a page whose whole subject is a list the reader is looking
/// at, abandoning an edit is what the delete button is for.
/// </para>
///
/// <para>
/// **What it shows is the day's closing, and what it writes is only what the reader changed.**
/// The page's list walks the book forward through the day's fills, so the numbers under the
/// preview are the closing ones; a dialog opening on the stored book would answer with the
/// morning's and read as an import that never landed. So it is handed the closing rows — and
/// because those are not what the book holds, closing the dialog writes nothing: the first real
/// change is what commits the closing figures into the book (see <see cref="Adopt"/>).
/// </para>
///
/// <para>
/// **The code is checked against the quote endpoint before it is stored.** A holding entered with
/// a typo would fail one fetch at a time for as long as it sat in the book, and the page would
/// look broken rather than mis-typed. The request also supplies the source's own name, so the
/// row can be recognised later in whatever language the interface is running in.
/// </para>
///
/// <para>
/// **A name is answered as readily as a code.** The book is transcribed from a broker app that
/// lists 顺丰控股, not 002352, so requiring the number would mean looking it up elsewhere first —
/// and the first version of this dialog did require it, which is why typing a name here produced
/// "代码看不懂" and nothing else happened. The field now suggests while the reader types, across
/// both venues at once, because one name can be listed on two of them: 顺丰控股 is `sz002352` in
/// Shenzhen and `hk06936` in Hong Kong, and only the reader knows which one they bought.
/// </para>
/// </summary>
public sealed partial class PortfolioDialog : ContentDialog
{
    /// <summary>How long typing has to stop before the source is asked.</summary>
    private readonly DispatcherTimer _debounce = new() { Interval = TimeSpan.FromMilliseconds(260) };

    /// <summary>What the last search answered, in the order it answered it.</summary>
    private readonly List<StockChoice> _choices = [];

    /// <summary>The suggestion the reader picked, when they picked one rather than typed.</summary>
    private StockRef? _picked;

    /// <summary>The text the pending debounce is about.</summary>
    private string _query = string.Empty;

    /// <summary>
    /// Whether this visit actually changed the book — a row edited, added or removed. The page
    /// uses it to decide the book now says what the reader typed, which outranks every fill still
    /// waiting to roll into it.
    /// </summary>
    public bool Edited { get; private set; }

    /// <summary>
    /// The write-backs of every row still on the list, run when the dialog closes.
    ///
    /// A row commits on losing focus, but **closing the dialog does not move focus** — the reader
    /// edits a number and presses 关闭, and the edit is still sitting in the box with no commit
    /// behind it (实测：改成 777 后直接关闭，portfolio.json 里还是 100). So every row's commit is
    /// also held here and the whole lot is run on Closing. Each commit re-reads its own boxes and
    /// writes through `Put`, which is idempotent — running the ones that already committed costs
    /// nothing.
    /// </summary>
    private readonly List<Action> _commits = [];

    /// <summary>
    /// What the dialog is showing, row by row — **the position as the day left it**, not as it
    /// opened.
    /// </summary>
    /// <remarks>
    /// The page's list is the book walked forward by the day's fills, so the closing figures are
    /// what the reader has just been reading there. A dialog that opened on the stored book showed
    /// them the *morning* — 公牛集团 100 instead of 900, 恒生科技ETF 10,000 instead of 20,000 —
    /// which reads as an import that never landed (实测：列表 900 股 / 成本 37.054，对话框 100 股 /
    /// 成本 37.73). The book is still the morning's; what the dialog shows is the morning's plus
    /// the day, which is the only thing a reader recognises as "my holdings".
    /// </remarks>
    private readonly List<Holding> _rows;

    /// <summary>
    /// Whether those rows have been written into the book yet.
    ///
    /// They are the **closing** figures and the book holds the **opening**, so simply closing the
    /// dialog must not commit them: doing so would turn the morning's book into the evening's and
    /// leave the day's replay with nothing to walk. The book is replaced the first time the reader
    /// actually changes something, and not before.
    /// </summary>
    private bool _adopted;

    public PortfolioDialog()
        : this(null)
    {
    }

    /// <param name="rows">
    /// The book as the page is currently drawing it — the page hands in its closing figures.
    /// Null reads the stored book, which is also the right answer when there is nothing to fetch.
    /// </param>
    public PortfolioDialog(IReadOnlyList<Holding>? rows)
    {
        InitializeComponent();

        Title = Strings.Get("PortfolioDialogTitle");
        CloseButtonText = Strings.Get("PortfolioDialogClose");

        Portfolio.EnsureLoaded();

        _rows = rows is { Count: > 0 } ? [.. rows] : [.. Portfolio.Holdings];

        Closing += (_, _) => CommitAll();

        _debounce.Tick += async (_, _) =>
        {
            _debounce.Stop();
            await SuggestAsync(_query);
        };

        Rebuild();
    }

    /// <summary>Runs every row's write-back, whether or not it already ran on a lost focus.</summary>
    private void CommitAll()
    {
        foreach (var commit in _commits)
        {
            commit();
        }
    }

    /// <summary>
    /// Writes the closing rows into the book, once, on the reader's first change.
    ///
    /// Every other row has to move with the edited one: the book is about to hold one moment, and
    /// a book mixing nine morning figures with one evening figure is a position nobody ever held
    /// (公牛集团 900 shares beside 恒生科技ETF 10,000 — the day half applied).
    /// </summary>
    private void Adopt()
    {
        if (_adopted)
        {
            return;
        }

        _adopted = true;

        Portfolio.ReplaceAll(_rows);
    }

    /// <summary>Draws the book, one row per holding.</summary>
    private void Rebuild()
    {
        // The old rows' closures hold boxes that are about to be detached — keeping them would
        // commit values the visible list no longer shows.
        _commits.Clear();

        Rows.Children.Clear();

        if (_rows.Count == 0)
        {
            Rows.Children.Add(new TextBlock
            {
                Text = Strings.Get("PortfolioPnlEmpty"),
                TextWrapping = TextWrapping.Wrap,
                Style = (Style)Application.Current.Resources["CaptionTextBlockStyle"],
            });

            return;
        }

        foreach (var holding in _rows.ToList())
        {
            Rows.Children.Add(Row(holding));
        }
    }

    /// <summary>
    /// One holding: the name over its code, the two numbers, and a delete button.
    ///
    /// The numbers are editable in place — a cost corrected after a split, or a share count that
    /// was entered wrong, is the ordinary reason to open this dialog, and making that a
    /// delete-and-re-add is how a book ends up with the wrong history.
    /// </summary>
    private UIElement Row(Holding holding)
    {
        var grid = new Grid
        {
            ColumnSpacing = 8,
            Padding = new Thickness(0, 4, 0, 4),
        };

        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

        var label = new StackPanel { Spacing = 1 };

        label.Children.Add(new TextBlock
        {
            Text = InstrumentNames.Display(holding.Code, holding.Name),
            TextTrimming = TextTrimming.CharacterEllipsis,
            Style = (Style)Application.Current.Resources["CaptionTextBlockStyle"],
        });

        label.Children.Add(new TextBlock
        {
            Text = holding.Code.ToUpperInvariant(),
            Style = (Style)Application.Current.Resources["CaptionTextBlockStyle"],
            Foreground = (Brush)Application.Current.Resources["TextFillColorSecondaryBrush"],
        });

        grid.Children.Add(label);

        var shares = new TextBox
        {
            Text = holding.Shares.ToString("0.##", CultureInfo.InvariantCulture),
            Width = 90,
            VerticalAlignment = VerticalAlignment.Center,
        };

        AutomationProperties.SetName(shares, Strings.Get("PortfolioDialogShares.PlaceholderText"));
        Grid.SetColumn(shares, 1);
        grid.Children.Add(shares);

        var cost = new TextBox
        {
            Text = holding.Cost.ToString("0.####", CultureInfo.InvariantCulture),
            Width = 90,
            VerticalAlignment = VerticalAlignment.Center,
        };

        AutomationProperties.SetName(cost, Strings.Get("PortfolioDialogCost.PlaceholderText"));
        Grid.SetColumn(cost, 2);
        grid.Children.Add(cost);

        // Written back on losing focus rather than on every keystroke: a text box being typed
        // into holds "1" of "1000" for a moment, and storing that would remove a holding.
        //
        // **A negative cost is legitimate and must not be refused.** The diluted cost goes
        // negative once a sale's proceeds exceed what the remaining shares cost — this very book
        // carries 超图软件 at ¥-96.847. The old `price < 0` guard therefore silently dropped
        // every edit to exactly those rows — the reader changed the share count, the box kept
        // it, and the file never moved (实测：改成 777，关掉对话框，portfolio.json 还是 100)，
        // which is what "改了不生效" was. Garbage text parses to zero and is refused by the
        // size check; the cost needs no guard of its own.
        void WriteBack()
        {
            var size = Math.Round(Number(shares.Text), 4);
            var price = Math.Round(Number(cost.Text), 4);

            if (size <= 0)
            {
                return;
            }

            // **Closing the dialog is not editing it.** Each row shows the day's closing figure,
            // which is not what the book holds, so a row that still reads what it was seeded with
            // has nothing to say — writing it back would turn the morning's book into the evening's
            // just because the reader looked (实测：只打开再关闭，账本就变成了收盘，回放从那一刻
            // 起不再有仓位可走).
            //
            // Compared **at the box's own precision**: the seeded cost carries more digits than the
            // four the box shows (30.67523456 against "30.6752"), and an exact comparison would make
            // every untouched row look edited.
            var sameSize = size == Math.Round(holding.Shares, 4);
            var sameCost = price == Math.Round(holding.Cost, 4);

            if (sameSize && sameCost)
            {
                return;
            }

            Adopt();

            // An untouched cost keeps its full precision; only the one the reader retyped is
            // written at the four decimals the box can show.
            var updated = new Holding(
                holding.Code, holding.Name, size, sameCost ? holding.Cost : price);

            Portfolio.Put(updated);

            var at = _rows.FindIndex(r => string.Equals(r.Code, holding.Code, StringComparison.OrdinalIgnoreCase));

            if (at >= 0)
            {
                _rows[at] = updated;
            }

            Edited = true;
        }

        void Commit(object _, RoutedEventArgs __) => WriteBack();

        shares.LostFocus += Commit;
        cost.LostFocus += Commit;

        _commits.Add(WriteBack);

        var remove = new Button
        {
            Content = new FontIcon { Glyph = "\uE74D", FontSize = 12 },
            VerticalAlignment = VerticalAlignment.Center,
            Padding = new Thickness(8),
        };

        AutomationProperties.SetName(remove, Strings.Format("PortfolioDialogRemove", holding.Code.ToUpperInvariant()));

        remove.Click += (_, _) =>
        {
            Adopt();

            Portfolio.Remove(holding.Code);
            _rows.RemoveAll(r => string.Equals(r.Code, holding.Code, StringComparison.OrdinalIgnoreCase));

            Edited = true;
            Rebuild();
        };

        Grid.SetColumn(remove, 3);
        grid.Children.Add(remove);

        return grid;
    }

    // ---- searching ---------------------------------------------------------------

    /// <summary>
    /// Suggests while the reader types, once typing has paused.
    ///
    /// Debounced rather than fired per keystroke: this endpoint is asked once per character
    /// otherwise, and the answer to "顺" is never what the reader wanted anyway.
    /// </summary>
    private void OnQueryChanged(AutoSuggestBox sender, AutoSuggestBoxTextChangedEventArgs args)
    {
        // Only what the reader typed counts. A chosen suggestion also arrives here — it is this
        // code writing the text — and re-searching that would replace the list under the cursor
        // with the one item already chosen.
        if (args.Reason is not AutoSuggestionBoxTextChangeReason.UserInput)
        {
            return;
        }

        _picked = null;
        _query = Query(sender.Text);

        _debounce.Stop();

        if (_query.Length == 0)
        {
            _choices.Clear();
            sender.ItemsSource = null;
            return;
        }

        _debounce.Start();
    }

    private async Task SuggestAsync(string query)
    {
        var found = await LookupAsync(query);

        _choices.Clear();
        _choices.AddRange(found.Select(r => new StockChoice(r)));

        CodeBox.ItemsSource = found.Count == 0 ? null : _choices.ToArray();
        CodeBox.IsSuggestionListOpen = found.Count > 0;
    }

    /// <summary>
    /// Every listing the source knows by this text, on either venue this book carries.
    ///
    /// Called once per pause in typing and again by <see cref="AddAsync"/> when the field holds a
    /// name, so a reader who types a name and presses 添加 without touching the list still gets
    /// an answer rather than an error.
    /// </summary>
    private async Task<IReadOnlyList<StockRef>> LookupAsync(string raw)
    {
        var text = Query(raw);

        if (text.Length == 0)
        {
            return [];
        }

        var answered = await AppServices.Current.Stocks.SearchAsync(
            text,
            code => code.StartsWith("sh", StringComparison.OrdinalIgnoreCase) ||
                    code.StartsWith("sz", StringComparison.OrdinalIgnoreCase) ||
                    code.StartsWith("bj", StringComparison.OrdinalIgnoreCase) ||
                    code.StartsWith("hk", StringComparison.OrdinalIgnoreCase),
            CancellationToken.None);

        // **Shares only.** A search for 快手 answers with the share and six warrants on it; all
        // seven are Hong Kong codes and nothing in the digits says which is which. The `Kind`
        // field does — `GP` / `GP-A` for a share, `ETF` for a fund that trades like one, `QZ` for
        // a warrant. A book carrying a warrant by accident would never reconcile with the broker.
        var ours = answered.Where(r =>
            r.Kind.StartsWith("GP", StringComparison.OrdinalIgnoreCase) ||
            r.Kind.Equals("ETF", StringComparison.OrdinalIgnoreCase));

        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var found = new List<StockRef>();

        // The code the reader typed, if it names one, comes first: typing `01024` and being
        // offered a list whose first row is a different instrument would be a puzzle.
        var exact = Normalize(text);

        if (exact is not null)
        {
            foreach (var hit in ours.Where(r => string.Equals(r.Code, exact, StringComparison.OrdinalIgnoreCase)))
            {
                if (seen.Add(hit.Code))
                {
                    found.Add(hit);
                }
            }
        }

        foreach (var hit in ours)
        {
            if (seen.Add(hit.Code))
            {
                found.Add(hit);
            }
        }

        return [.. found.Take(8)];
    }

    private void OnSuggestionChosen(AutoSuggestBox sender, AutoSuggestBoxSuggestionChosenEventArgs args)
    {
        if (args.SelectedItem is StockChoice { Stock: var chosen })
        {
            _picked = chosen;

            // The box keeps the name and the code both: it is what the reader is about to add,
            // and a box that silently turned into `sz002352` would look like it had changed the
            // subject. `Query` strips the code back off before searching again.
            sender.Text = $"{InstrumentNames.Display(chosen.Code, chosen.Name)} · {chosen.Code.ToUpperInvariant()}";
        }
    }

    private async void OnQuerySubmitted(AutoSuggestBox sender, AutoSuggestBoxQuerySubmittedEventArgs args)
    {
        if (args.ChosenSuggestion is StockChoice { Stock: var chosen })
        {
            _picked = chosen;
        }

        await AddAsync();
    }

    // ---- adding ------------------------------------------------------------------

    private async void OnAdd(object sender, RoutedEventArgs e) => await AddAsync();

    /// <summary>Adds what was typed, if it names something the source will quote.</summary>
    private async Task AddAsync()
    {
        AddButton.IsEnabled = false;

        try
        {
            var typed = Query(CodeBox.Text);
            var shares = Number(SharesBox.Text);
            var cost = Number(CostBox.Text);

            if (typed.Length == 0)
            {
                Say(Strings.Get("PortfolioDialogBadCode"));
                return;
            }

            // Shares must be positive; the cost needs no sign guard — a diluted cost is
            // legitimately negative once a sale's proceeds have overtaken what the remaining
            // shares cost, and refusing it here would make such a position unenterable.
            if (shares <= 0)
            {
                Say(Strings.Get("PortfolioDialogBadNumbers"));
                return;
            }

            var code = _picked?.Code ?? Normalize(typed);

            if (code is null)
            {
                // A name rather than a code. Answered by asking the source, which is also what
                // the suggestion list does — a reader who typed straight through deserves the
                // same answer as one who looked at the list.
                Say(Strings.Get("PortfolioDialogChecking"));

                IReadOnlyList<StockRef> hits;

                try
                {
                    hits = await LookupAsync(typed);
                }
                catch (Exception ex)
                {
                    Say(Strings.Reason(ex));
                    return;
                }

                if (hits.Count == 0)
                {
                    Say(Strings.Format("PortfolioDialogUnknown", typed));
                    return;
                }

                if (hits.Count > 1)
                {
                    _choices.Clear();
                    _choices.AddRange(hits.Select(r => new StockChoice(r)));

                    CodeBox.ItemsSource = _choices.ToArray();
                    CodeBox.IsSuggestionListOpen = true;
                    CodeBox.Focus(FocusState.Programmatic);

                    Say(Strings.Format("PortfolioDialogPick", hits.Count));
                    return;
                }

                _picked = hits[0];
                code = hits[0].Code;
            }

            Say(Strings.Get("PortfolioDialogChecking"));

            StockSnapshot? shot;

            try
            {
                var found = await AppServices.Current.Stocks.SnapshotsAsync([code], CancellationToken.None);

                found.TryGetValue(code, out shot);
            }
            catch (Exception ex)
            {
                // A code that came out of the source's own search is not made doubtful by this
                // endpoint being slow: the search already said the listing exists, and refusing
                // it here would mean a reader could not add a stock while offline for one call.
                if (_picked is null)
                {
                    Say(Strings.Reason(ex));
                    return;
                }

                shot = null;
            }

            var name = shot?.Name is { Length: > 0 } fromSource ? fromSource : _picked?.Name ?? string.Empty;

            if (name.Length == 0)
            {
                Say(Strings.Format("PortfolioDialogUnknown", code.ToUpperInvariant()));
                return;
            }

            var existed = _rows.Any(r => string.Equals(r.Code, code, StringComparison.OrdinalIgnoreCase));

            Adopt();

            var added = new Holding(code, name, Math.Round(shares, 4), Math.Round(cost, 4));

            Portfolio.Put(added);

            var at = _rows.FindIndex(r => string.Equals(r.Code, code, StringComparison.OrdinalIgnoreCase));

            if (at >= 0)
            {
                _rows[at] = added;
            }
            else
            {
                _rows.Add(added);
            }

            Edited = true;

            CodeBox.Text = string.Empty;
            SharesBox.Text = string.Empty;
            CostBox.Text = string.Empty;
            _picked = null;

            Rebuild();
            ScrollToEnd();

            // Said rather than left to be noticed. The list is nine rows in a 280-pixel
            // scroller, so the row that was just added lands **below the fold** — which is the
            // other half of "点击添加后持仓列表未新增记录": it was added, and the dialog was
            // still showing the top of the list.
            Say(Strings.Format(
                existed ? "PortfolioDialogUpdated" : "PortfolioDialogAdded",
                $"{InstrumentNames.Display(code, name)} · {code.ToUpperInvariant()}"));
        }
        finally
        {
            AddButton.IsEnabled = true;
        }
    }

    /// <summary>Brings the row that was just written into view.</summary>
    private void ScrollToEnd() =>
        DispatcherQueue.TryEnqueue(() =>
        {
            Scroller.UpdateLayout();
            Scroller.ChangeView(null, Scroller.ScrollableHeight, null);
        });

    // ---- the list as a file --------------------------------------------------------

    /// <summary>
    /// Writes the list as it stands to a CSV the reader can open in anything.
    ///
    /// Exports **what the dialog shows** — the day's closing figures — because that is the list
    /// the reader is reconciling against; the stored book is still the morning's until something
    /// is actually changed here.
    /// </summary>
    private async void OnExport(object sender, RoutedEventArgs e)
    {
        if (App.Window is not { } window)
        {
            return;
        }

        var picker = new Windows.Storage.Pickers.FileSavePicker
        {
            SuggestedStartLocation = Windows.Storage.Pickers.PickerLocationId.DocumentsLibrary,
            SuggestedFileName = "holdings",
        };

        picker.FileTypeChoices.Add("CSV", [".csv"]);

        WinRT.Interop.InitializeWithWindow.Initialize(
            picker, WinRT.Interop.WindowNative.GetWindowHandle(window));

        if (await picker.PickSaveFileAsync() is not { } file)
        {
            return;
        }

        SheetExportButton.IsEnabled = false;

        try
        {
            // **BOM first.** Excel reads a UTF-8 CSV without one as the system code page and
            // shows every Chinese name as mojibake; with it, the file opens correctly by
            // double-click on a Chinese, Japanese or German machine alike.
            var bytes = System.Text.Encoding.UTF8.GetPreamble()
                .Concat(System.Text.Encoding.UTF8.GetBytes(HoldingsSheet.Write(_rows)))
                .ToArray();

            await Windows.Storage.FileIO.WriteBytesAsync(file, bytes);

            Say(Strings.Format("PortfolioDialogExportDone", _rows.Count));
        }
        catch (Exception ex)
        {
            Say(Strings.Reason(ex));
        }
        finally
        {
            SheetExportButton.IsEnabled = true;
        }
    }

    /// <summary>
    /// Reads a holdings file over the list, in place of it.
    ///
    /// **Replaces rather than merges.** The file is the list; a merge would leave positions in
    /// the book that the reader believed they had just deleted by removing their lines, and the
    /// only way to find that out would be the total. Nothing is applied unless every line reads
    /// cleanly, and the lines that do not are reported with their numbers.
    /// </summary>
    private async void OnImport(object sender, RoutedEventArgs e)
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

        picker.FileTypeFilter.Add(".csv");
        picker.FileTypeFilter.Add(".txt");

        WinRT.Interop.InitializeWithWindow.Initialize(
            picker, WinRT.Interop.WindowNative.GetWindowHandle(window));

        if (await picker.PickSingleFileAsync() is not { } file)
        {
            return;
        }

        SheetImportButton.IsEnabled = false;

        try
        {
            using var stream = await file.OpenStreamForReadAsync();
            using var memory = new MemoryStream();

            await stream.CopyToAsync(memory);

            if (!HoldingsSheet.TryDecode(memory.ToArray(), out var text))
            {
                Say(Strings.Get("PortfolioDialogSheetEncoding"));
                return;
            }

            var (parsed, problems) = HoldingsSheet.Parse(text, Normalize);

            if (problems.Count > 0)
            {
                Say(Complaints(problems));
                return;
            }

            if (parsed.Count == 0)
            {
                Say(Strings.Get("PortfolioDialogImportEmpty"));
                return;
            }

            // A three-column file has no name of its own; the book still knows what it calls
            // that holding, and a row reading `SZ002352` alone would be a row the reader has to
            // look up every time.
            var named = parsed
                .Select(row => row.Name.Length > 0
                    ? row
                    : row with { Name = Portfolio.Find(row.Code)?.Name ?? string.Empty })
                .ToList();

            _rows.Clear();
            _rows.AddRange(named);

            // The file is a whole list, so the book becomes it now — past the "only what the
            // reader changed" rule, because this *is* a change, and a large one.
            _adopted = true;
            Portfolio.ReplaceAll(_rows);

            Edited = true;

            Rebuild();
            ScrollToEnd();

            Say(Strings.Format("PortfolioDialogImportDone", named.Count));
        }
        catch (Exception ex)
        {
            Say(Strings.Reason(ex));
        }
        finally
        {
            SheetImportButton.IsEnabled = true;
        }
    }

    /// <summary>The first few bad lines, and how many more there are.</summary>
    private static string Complaints(IReadOnlyList<SheetRow> problems)
    {
        const int Shown = 3;

        var lines = problems
            .Take(Shown)
            .Select(p => Strings.Format("PortfolioDialogImportRow", p.Line, RowReason(p.Problem)))
            .ToList();

        if (problems.Count > Shown)
        {
            lines.Add(Strings.Format("PortfolioDialogImportMore", problems.Count - Shown));
        }

        return string.Join("\n", lines);
    }

    private static string RowReason(SheetProblem problem) => Strings.Get(problem switch
    {
        SheetProblem.Columns => "PortfolioDialogRowColumns",
        SheetProblem.Code => "PortfolioDialogRowCode",
        SheetProblem.Shares => "PortfolioDialogRowShares",
        SheetProblem.Cost => "PortfolioDialogRowCost",
        _ => "PortfolioDialogRowDuplicate",
    });

    private void Say(string message)
    {
        Message.Text = message;
        Message.Visibility = Visibility.Visible;
    }

    private static double Number(string text) =>
        double.TryParse(text.Trim(), NumberStyles.Float, CultureInfo.InvariantCulture, out var value)
            ? value
            : 0;

    /// <summary>
    /// The part of what is in the box that is worth searching.
    ///
    /// A chosen suggestion writes `顺丰控股 · SZ002352` into the box, and the reader will go on
    /// typing after that more often than not. Sending the whole string back to the source would
    /// answer nothing — it matches names and codes, not the two joined by a bullet.
    /// </summary>
    private static string Query(string raw)
    {
        var text = raw.Trim();
        var dot = text.IndexOf(" · ", StringComparison.Ordinal);

        return dot > 0 ? text[..dot].Trim() : text;
    }

    /// <summary>
    /// Turns what a reader types into a code the quote endpoint answers to.
    ///
    /// The whole point is that they should not have to know which prefix a venue uses: `300036`
    /// and `sz300036` are the same listing, and a Hong Kong code is five digits with or without
    /// its `hk` — before or after the digits, because a broker's own list writes `00700.HK` and
    /// the reader copies what they see. The six-digit mainland numbers are assigned to an
    /// exchange by their first digit — 6 Shanghai, 0 and 3 Shenzhen, 4 and 8 Beijing — which is
    /// the same rule <c>TradeText</c> applies to an imported row, deliberately: two rules would
    /// let a holding typed here and the same holding imported there become two positions.
    /// </summary>
    /// <returns>Null when the input is no code at all — which is how a name ends up here, and the
    /// caller's cue to search instead.</returns>
    public static string? Normalize(string raw)
    {
        var text = raw.Trim().ToLowerInvariant().Replace(" ", string.Empty).Replace(".", string.Empty);

        // `00700HK` — the suffix form, after the dot was taken out above.
        if (text.EndsWith("hk", StringComparison.Ordinal) && text.Length > 2)
        {
            var digits = text[..^2];

            if (digits.Length is 4 or 5 && digits.All(char.IsDigit))
            {
                return "hk" + digits.PadLeft(5, '0');
            }
        }

        if (text.StartsWith("hk", StringComparison.Ordinal))
        {
            var digits = text[2..];

            return digits.Length is 4 or 5 && digits.All(char.IsDigit) ? "hk" + digits.PadLeft(5, '0') : null;
        }

        if (text.StartsWith("sh", StringComparison.Ordinal) ||
            text.StartsWith("sz", StringComparison.Ordinal) ||
            text.StartsWith("bj", StringComparison.Ordinal))
        {
            return text.Length == 8 && text[2..].All(char.IsDigit) ? text : null;
        }

        if (!text.All(char.IsDigit))
        {
            return null;
        }

        return text.Length switch
        {
            6 => text[0] switch
            {
                '6' => "sh" + text,
                '0' or '3' => "sz" + text,
                '4' or '8' => "bj" + text,
                _ => null,
            },
            4 or 5 => "hk" + text.PadLeft(5, '0'),
            _ => null,
        };
    }
}
