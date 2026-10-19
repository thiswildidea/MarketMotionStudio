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

    public PortfolioDialog()
    {
        InitializeComponent();

        Title = Strings.Get("PortfolioDialogTitle");
        CloseButtonText = Strings.Get("PortfolioDialogClose");

        Portfolio.EnsureLoaded();

        _debounce.Tick += async (_, _) =>
        {
            _debounce.Stop();
            await SuggestAsync(_query);
        };

        Rebuild();
    }

    /// <summary>Draws the book, one row per holding.</summary>
    private void Rebuild()
    {
        Rows.Children.Clear();

        if (Portfolio.Holdings.Count == 0)
        {
            Rows.Children.Add(new TextBlock
            {
                Text = Strings.Get("PortfolioPnlEmpty"),
                TextWrapping = TextWrapping.Wrap,
                Style = (Style)Application.Current.Resources["CaptionTextBlockStyle"],
            });

            return;
        }

        foreach (var holding in Portfolio.Holdings.ToList())
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
        void Commit(object _, RoutedEventArgs __)
        {
            var size = Number(shares.Text);
            var price = Number(cost.Text);

            if (size <= 0 || price < 0)
            {
                return;
            }

            Portfolio.Put(new Holding(holding.Code, holding.Name, Math.Round(size, 4), Math.Round(price, 4)));
        }

        shares.LostFocus += Commit;
        cost.LostFocus += Commit;

        var remove = new Button
        {
            Content = new FontIcon { Glyph = "\uE74D", FontSize = 12 },
            VerticalAlignment = VerticalAlignment.Center,
            Padding = new Thickness(8),
        };

        AutomationProperties.SetName(remove, Strings.Format("PortfolioDialogRemove", holding.Code.ToUpperInvariant()));

        remove.Click += (_, _) =>
        {
            Portfolio.Remove(holding.Code);
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

            if (shares <= 0 || cost < 0)
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

            var existed = Portfolio.Find(code) is not null;

            Portfolio.Put(new Holding(code, name, Math.Round(shares, 4), Math.Round(cost, 4)));

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
