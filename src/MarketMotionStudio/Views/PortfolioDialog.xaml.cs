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
/// **What it shows is the initial position, and what it writes is that same position.** The rows,
/// the file 导入初始持仓 reads, and the file 导出初始持仓 writes are one list — 导出 writes the rows
/// above it, not a snapshot from disk, so the file and the screen can never disagree. The book the
/// rest of the app draws is this position walked forward by every fill since; that walk is redone
/// once when the dialog closes (see <see cref="RebaseBook"/>), because a new starting point makes
/// the old finish stale.
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
    /// What the dialog is showing, row by row — **the initial position**, which is the one thing
    /// this dialog owns.
    /// </summary>
    /// <remarks>
    /// It used to show the day's closing figures, on the argument that those are what the reader
    /// recognises as "my holdings". That made the three baseline buttons describe a different book
    /// from the one on screen: 导入 changed a snapshot nobody could see, and 导出 wrote a file that
    /// did not match the rows above it (实测：导入 9 只之后列表仍是 14,100 股，导出的却是 3,000 股).
    /// A dialog that edits the initial position has to show the initial position.
    /// </remarks>
    private readonly List<Holding> _rows;

    /// <summary>
    /// Whether the baseline moved during this visit — an import, an edit, a row added or removed.
    ///
    /// The book behind the dialog is the same position walked forward, so a new starting point
    /// makes it stale. Nothing is rebased until the dialog closes: the rows above are a form being
    /// edited, and recomputing a book from a half-typed form would move the position on every
    /// keystroke.
    /// </summary>
    private bool _baselineMoved;

    /// <summary>
    /// Which of the two baselines this visit edits: the mainland one or the one carrying the Hong
    /// Kong positions.
    ///
    /// **The page passes the scope it is drawing.** A dialog that always edited the same snapshot
    /// would leave the other book invisible but not untouched: a reader who switched to 港股通 and
    /// pressed 管理持仓 would see the mainland rows, correct one, and file the correction against
    /// a book the page has stopped reading — "改了没变" with nothing on screen to explain it.
    /// </summary>
    private readonly PortfolioScope _scope;

    public PortfolioDialog()
        : this(null)
    {
    }

    /// <param name="rows">
    /// Ignored when a baseline exists — the dialog always opens on the initial position, not on
    /// whatever the page is currently drawing. Kept for the fallback: with no baseline set, the
    /// book on hand is the only starting point there is.
    /// </param>
    /// <param name="scope">Which of the two books this visit edits.</param>
    public PortfolioDialog(IReadOnlyList<Holding>? rows, PortfolioScope scope = PortfolioScope.WithKong)
    {
        InitializeComponent();

        _scope = scope;

        Title = Strings.Get("PortfolioDialogTitle");
        CloseButtonText = Strings.Get("PortfolioDialogClose");

        Portfolio.EnsureLoaded();

        // The snapshot's day, so the reader sees which morning is set before deciding whether to
        // change it. Today when nothing has been set: it is the day a snapshot taken now describes,
        // and a picker sitting on 1918 would only be confusing.
        Ledger.EnsureLoaded();

        var baselineDay = Ledger.BaselineDayOf(_scope);

        var anchor = baselineDay == DateOnly.MinValue
            ? DateOnly.FromDateTime(DateTime.Today)
            : baselineDay;

        BaselineDay.Date = new DateTimeOffset(anchor.ToDateTime(TimeOnly.MinValue), TimeSpan.Zero);
        BaselineDay.MaxYear = new DateTimeOffset(DateTime.Today.AddYears(1));

        // **The 港股通 book's day is not the reader's to set.** Its baseline is the last session's
        // close — rewritten by the page whenever the curve reaches its final frame — so a picker
        // would offer a choice the next animation silently overwrites, and a date filed by hand
        // against figures the page no longer holds. The mainland book keeps its picker: its
        // baseline is one morning the reader filed, and the spans are measured from it.
        BaselineDay.IsEnabled = _scope is PortfolioScope.AShare;

        // **The baseline is what this dialog edits**, so it is what the dialog opens on. The page's
        // drawing is the fallback, used only when no starting point has been set — in that case the
        // book on hand is the only thing there is to show.
        // **This scope's baseline**, not the other one: the mainland book and the Hong Kong one
        // are two different mornings' figures and a dialog that mixed them would correct a book
        // the page is not reading.
        _rows = Ledger.BaselineOf(_scope) is { Empty: false } opening
            ? [.. opening.Kept]
            : rows is { Count: > 0 } ? [.. rows] : [.. Portfolio.Holdings];

        // Closing does not move focus, so a number typed into a box can still be sitting there
        // uncommitted; every row's write-back is also held in `_commits` and run here. The book is
        // then rebased once, off the committed rows rather than off what the boxes happened to say.
        Closing += (_, _) =>
        {
            CommitAll();

            RebaseBook();
        };

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
    /// Writes the rows above into the baseline, under the date the picker holds.
    ///
    /// **Every change goes through here**, whether it came from a retyped share count, a row added
    /// at the bottom, a removal, or a file. The alternative — keeping the edits in memory until the
    /// reader presses 设为初始持仓 — makes 导出 write the *previous* baseline while the screen shows
    /// the new one, which is the exact disagreement this dialog just stopped having.
    ///
    /// The day comes from the picker rather than from the last import: a reader who moves the date
    /// and then fixes a share count means both, and a snapshot filed under the old date would
    /// quietly undo the move.
    /// </summary>
    private void CommitBaseline()
    {
        var rows = _rows.Where(r => r.Shares > 0).ToList();

        if (rows.Count == 0)
        {
            return;
        }

        Ledger.SetBaseline(_scope, ChosenBaselineDay, rows);

        _baselineMoved = true;

        Edited = true;
    }

    /// <summary>
    /// Makes the book behind the dialog agree with the baseline it just took.
    ///
    /// The position on the page is this snapshot walked forward by every fill since, so replacing
    /// the snapshot without walking it again leaves two answers on one screen — the curve drawn from
    /// the new start and the list still showing the old finish. Called once, on close, and only
    /// when something actually moved: an untouched dialog must not rewrite the book.
    /// </summary>
    private void RebaseBook()
    {
        if (!_baselineMoved || _rows.All(r => r.Shares <= 0))
        {
            return;
        }

        // The 港股通 rows are a closing figure — its day is locked to the last session and the
        // page keeps the baseline on the curve's final frame — so the journal restarts strictly
        // after that day: the day's own fills are inside the rows already, and keeping them would
        // fold them a second time at the next roll. The mainland book is a morning snapshot and
        // keeps the on-or-after default.
        Portfolio.Rebase(ChosenBaselineDay, _rows, Ledger.Archive,
            closeBook: _scope is PortfolioScope.WithKong);
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

            // An untouched cost keeps its full precision; only the one the reader retyped is
            // written at the four decimals the box can show.
            var updated = new Holding(
                holding.Code, holding.Name, size, sameCost ? holding.Cost : price);

            var at = _rows.FindIndex(r => string.Equals(r.Code, holding.Code, StringComparison.OrdinalIgnoreCase));

            if (at >= 0)
            {
                _rows[at] = updated;
            }

            // The baseline is the record this dialog edits, so the edit lands there now rather
            // than in a copy that only the dialog can see.
            CommitBaseline();
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
            _rows.RemoveAll(r => string.Equals(r.Code, holding.Code, StringComparison.OrdinalIgnoreCase));

            CommitBaseline();
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

            var added = new Holding(code, name, Math.Round(shares, 4), Math.Round(cost, 4));

            var at = _rows.FindIndex(r => string.Equals(r.Code, code, StringComparison.OrdinalIgnoreCase));

            if (at >= 0)
            {
                _rows[at] = added;
            }
            else
            {
                _rows.Add(added);
            }

            CommitBaseline();

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
    /// The snapshot's day, as the picker has it.
    ///
    /// A `DateTimeOffset` is what the control carries and `yyyy-MM-dd` is what every line of the
    /// ledger speaks, so the conversion happens once, here, rather than at each of the three
    /// places below that would otherwise each do their own.
    /// </summary>
    private DateOnly ChosenBaselineDay =>
        DateOnly.FromDateTime(BaselineDay.Date.DateTime);

    /// <summary>
    /// Writes the list as it stands to a CSV the reader can open in anything.
    ///
    /// Exports **what the dialog shows** — the day's closing figures — because that is the list
    /// the reader is reconciling against; the stored book is still the morning's until something
    /// is actually changed here.
    /// </summary>
    private async void OnExport(object sender, RoutedEventArgs e)
    {
        SheetExportButton.IsEnabled = false;

        try
        {
            if (await CsvFiles.WriteAsync("holdings", HoldingsSheet.Write(_rows)))
            {
                Say(Strings.Format("PortfolioDialogExportDone", _rows.Count));
            }
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
    /// Sets the book's starting point to **the list as it stands now**, on the day chosen.
    ///
    /// Taking it from what is on screen rather than from a second form is not laziness: the rows
    /// have just been reconciled against the broker, and a snapshot entered twice from two places
    /// is two answers to "what did I hold".
    /// </summary>
    private void OnSetBaseline(object sender, RoutedEventArgs e)
    {
        Ledger.EnsureLoaded();

        var rows = _rows.Where(r => r.Shares > 0).ToList();

        if (rows.Count == 0)
        {
            Say(Strings.Get("LedgerBaselineNone"));

            return;
        }

        var day = ChosenBaselineDay;

        // Same path every other change takes, so the book is rebased on close whether the new
        // baseline came from a button press or from a file.
        CommitBaseline();

        Say(Strings.Format(
            "LedgerBaselineDone",
            day.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
            rows.Count.ToString(CultureInfo.InvariantCulture)));
    }

    /// <summary>
    /// Reads a snapshot back in, replacing the one in force.
    ///
    /// <para>
    /// **The file the export writes is the file this accepts**, and nothing else: the five columns
    /// `day,code,name,shares,cost` with one date for the whole file. That is deliberate. A general
    /// spreadsheet reader here would let a broker's holdings page be pasted in "as a snapshot",
    /// and the columns it guessed wrong would be the cost — which is the number every figure on
    /// the two portfolio pages is then measured from.
    /// </para>
    ///
    /// <para>
    /// **Replacing, not merging.** The snapshot is one morning, so a second file is a second
    /// answer to the same question. Anything else would leave the reader holding the union of two
    /// books that were never held together.
    /// </para>
    ///
    /// <para>
    /// **Nothing is applied unless every line reads.** A snapshot missing two of its twenty rows
    /// opens every curve on a book the reader does not hold, and no page can say which two fell
    /// out; the line numbers come back instead, so the file can be fixed.
    /// </para>
    /// </summary>
    private async void OnImportBaseline(object sender, RoutedEventArgs e)
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

        BaselineImportButton.IsEnabled = false;

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

            var read = Ledger.SnapshotFromCsv(text);

            if (!read.Ready)
            {
                ReportSnapshotFile(read);

                return;
            }

            var snapshot = read.Snapshot!;

            // **The list is the file's rows, at once and for good.** This is the whole point of
            // the dialog: an import replaces the initial position, so the position on screen has
            // to become the one in the file — and stay that way, because there is nothing else on
            // this dialog for it to fall back to. It used to write the snapshot and leave the list
            // showing the closing figures, which read as "the import did nothing" (实测：导入 9 只
            // 后列表仍是 14,100 股).
            _rows.Clear();
            _rows.AddRange(snapshot.Kept);

            Ledger.SetBaseline(_scope, snapshot.Day, snapshot.Kept);

            _baselineMoved = true;
            Edited = true;

            // The picker follows the file, so the day on screen is the day in force: leaving it
            // on whatever it held before would let the next 以当前列表设为初始持仓 silently reset
            // a date the reader had just read out of a file.
            BaselineDay.Date = new DateTimeOffset(
                snapshot.Day.ToDateTime(TimeOnly.MinValue), TimeSpan.Zero);

            Rebuild();

            Say(Strings.Format(
                "LedgerBaselineImported",
                snapshot.Day.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
                snapshot.Count.ToString(CultureInfo.InvariantCulture)));
        }
        catch (Exception ex)
        {
            Say(Strings.Reason(ex));
        }
        finally
        {
            BaselineImportButton.IsEnabled = true;
        }
    }

    /// <summary>
    /// Why a snapshot file could not be applied, in terms of what the reader can do about it.
    ///
    /// Two failures and two sentences: a file with unreadable lines names them, and a file with
    /// no rows at all is not one of these exports. Rows disagreeing about the day are not a
    /// failure — the snapshot takes the latest day the file mentions.
    /// </summary>
    private void ReportSnapshotFile(SnapshotRead read)
    {
        if (read.Rejected.Count > 0)
        {
            Say(Strings.Format(
                "LedgerBaselineImportRejected",
                string.Join("、", read.Rejected.Select(n => n.ToString(CultureInfo.InvariantCulture)))));

            return;
        }

        Say(Strings.Get("LedgerBaselineImportShape"));
    }

    /// <summary>Writes the snapshot out, so a book rebuilt elsewhere can be checked against it.</summary>
    private async void OnExportBaseline(object sender, RoutedEventArgs e)
    {
        Ledger.EnsureLoaded();

        // A number typed and not yet blurred is still in its box; the button press is about to
        // move focus, but the file must not depend on that ordering.
        CommitAll();

        // **The rows on screen, not the file already on disk.** 导出 is the reader saving what they
        // have just built up here; reading the stored snapshot instead would hand them a file that
        // disagrees with the list above it, which is the one thing an export must never do.
        var rows = _rows.Where(r => r.Shares > 0).ToList();

        if (rows.Count == 0)
        {
            Say(Strings.Get("LedgerBaselineNone"));

            return;
        }

        var snapshot = new HoldingSnapshot(ChosenBaselineDay, rows);

        BaselineExportButton.IsEnabled = false;

        try
        {
            if (await CsvFiles.WriteAsync("baseline", Ledger.SnapshotToCsv(snapshot)))
            {
                Say(Strings.Format(
                    "PortfolioDialogExportDone",
                    snapshot.Count.ToString(CultureInfo.InvariantCulture)));
            }
        }
        catch (Exception ex)
        {
            Say(Strings.Reason(ex));
        }
        finally
        {
            BaselineExportButton.IsEnabled = true;
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

            // A whole list replaces the starting position, the same way a file dropped on 导入初始持仓
            // does. Nothing is written into the book here: the rows are the baseline, and the book
            // is that baseline walked forward — recomputed once on close.
            CommitBaseline();

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
