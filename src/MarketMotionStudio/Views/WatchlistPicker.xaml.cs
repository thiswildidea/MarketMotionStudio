using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Pages;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;
using Microsoft.UI.Xaml.Media;

namespace MarketMotionStudio.Views;

/// <summary>One suggestion, as the box itself displays it.</summary>
public sealed record WatchSuggestion(string Code, string Name)
{
    public string Display => $"{Name}  {Code}";

    public override string ToString() => Display;
}

/// <summary>
/// The row that fills a person's own list, and the chips that show what is on it.
///
/// Shared by every roster board that offers the list, because the list itself is shared — see
/// <see cref="Watchlist"/>. The control owns the typing and the adding; what the board does with
/// a changed list is the board's business, and it hears about it through <see cref="Changed"/>.
///
/// **The search is asked about all three markets, not about one.** These boards are not governed
/// by the market setting — a mainland share, a Hong Kong one and a New York one can be on the
/// list together and all three will be drawn — so a search that answered only the market in force
/// would hide two thirds of what the board is willing to draw. The endpoint answers every venue
/// at once and one market's profile filters the rest away, so each is asked and the answers are
/// merged.
/// </summary>
public sealed partial class WatchlistPicker : UserControl
{
    /// <summary>Raised after a pick is added or removed.</summary>
    public event EventHandler? Changed;

    /// <summary>Raised when the control has something to say that only the page can show.</summary>
    public event Action<string>? Notice;

    private readonly DispatcherTimer _searchDebounce = new() { Interval = TimeSpan.FromMilliseconds(260) };

    private string _lastQuery = string.Empty;

    private WatchSuggestion? _pendingChoice;

    /// <summary>The picks this board is drawing, when <see cref="Selectable"/> is on.</summary>
    private readonly HashSet<string> _on = new(StringComparer.OrdinalIgnoreCase);

    /// <summary>Whether the reader has switched anything, and so which rule answers "what is drawn".</summary>
    private bool _touched;

    public WatchlistPicker()
    {
        InitializeComponent();

        Watchlist.EnsureLoaded();
        Chips.ItemsSource = Watchlist.Picks;

        // Applied here and again on load: the page writes `Selectable` in XAML, which lands after
        // this constructor has run and after the chips have been built from the default template.
        ApplyChipTemplate();
        Loaded += (_, _) => ApplyChipTemplate();

        _searchDebounce.Tick += async (_, _) =>
        {
            _searchDebounce.Stop();
            await SuggestAsync(_lastQuery);
        };
    }

    /// <summary>What is on the list, as the board can draw it.</summary>
    public IReadOnlyList<RaceEntry> Entries => [.. Watchlist.Picks];

    /// <summary>
    /// Whether the chips can be switched on and off, so that choosing a pick is a decision about
    /// this board rather than about the shared list.
    ///
    /// Off by default, and pointedly so: a ranking board draws the whole list, and a chip there
    /// that could be quietly switched off would be a board silently missing a row — which reads
    /// as a ranking that left an entrant out rather than as a setting someone changed. The one
    /// board that adds its picks into a single total turns it on, because the sum of five holdings
    /// is not the number anyone is looking for when they are asking about one of them.
    /// </summary>
    public bool Selectable { get; set; }

    /// <summary>
    /// The picks that board is drawing: the ones switched on — or, until the reader has switched
    /// anything, the first one alone.
    ///
    /// **One, not all, by default.** This list is shared with the ranking boards, where a dozen
    /// names is an ordinary list; on a board that adds them up, a dozen names added together is a
    /// total about nobody in particular. Opening on the first pick shows a real answer at once,
    /// and each further pick is one click. It also never draws an empty frame: an empty selection
    /// is only reachable by switching the first pick off as well, and that is reported when fetch
    /// is pressed rather than rendered as a blank chart.
    /// </summary>
    public IReadOnlyList<RaceEntry> SelectedEntries
    {
        get
        {
            var picks = Watchlist.Picks;

            if (picks.Count == 0)
            {
                return [];
            }

            return _touched
                ? [.. picks.Where(p => _on.Contains(p.Code))]
                : [picks[0]];
        }
    }

    /// <summary>
    /// Puts a pick into what this board is drawing, without the reader having to find its chip
    /// and switch it on.
    ///
    /// The one-tap rows call this. A press there has already decided that instrument is on this
    /// frame, and a pick that arrived on the list but switched off would draw nothing at all —
    /// which reads as a broken button rather than as a setting. The transition is the same one a
    /// first click on a switch makes: "the first pick alone" stops being the rule, and the state
    /// it was showing is carried into an explicit set, so the press adds a holding rather than
    /// replacing the board.
    /// </summary>
    public void Include(string code)
    {
        if (!_touched)
        {
            _touched = true;
            _on.Clear();

            if (Watchlist.Picks.Count > 0)
            {
                _on.Add(Watchlist.Picks[0].Code);
            }
        }

        _on.Add(code);

        // The chips that already exist were ticked from the rule that was in force when they
        // were built. A pick that was on the list and switched off is the one this changes, and
        // it would otherwise sit there unticked while the board drew it.
        RefreshChips();
    }

    /// <summary>
    /// Puts every built chip's switch where the board actually is.
    ///
    /// Hung off the panel rather than pushed per chip, and reached through the visual tree
    /// because an <see cref="ItemsControl"/> wraps what the template built in a container of its
    /// own — the chip is a descendant of the panel's child, not the child.
    /// </summary>
    private void RefreshChips()
    {
        if (Chips.ItemsPanelRoot is not { } panel)
        {
            return;
        }

        foreach (var child in panel.Children)
        {
            foreach (var chip in Switches(child))
            {
                if (chip.Tag is string code)
                {
                    chip.IsChecked = IsOn(code);
                }
            }
        }
    }

    private static IEnumerable<ToggleButton> Switches(DependencyObject root)
    {
        var count = VisualTreeHelper.GetChildrenCount(root);

        for (var i = 0; i < count; i++)
        {
            var child = VisualTreeHelper.GetChild(root, i);

            if (child is ToggleButton chip)
            {
                yield return chip;

                continue;
            }

            foreach (var deeper in Switches(child))
            {
                yield return deeper;
            }
        }
    }

    private void OnSearchTextChanged(AutoSuggestBox sender, AutoSuggestBoxTextChangedEventArgs args)
    {
        if (args.Reason is not AutoSuggestionBoxTextChangeReason.UserInput)
        {
            return;
        }

        _lastQuery = sender.Text;
        _searchDebounce.Stop();
        _searchDebounce.Start();
    }

    private async Task SuggestAsync(string query)
    {
        query = query.Trim();

        if (query.Length == 0)
        {
            Search.ItemsSource = null;
            return;
        }

        try
        {
            // One request per market, because one market's profile discards the other two's
            // answers. Three round trips behind a 260 ms debounce, for a list typed once.
            var merged = new List<WatchSuggestion>();

            foreach (var id in Markets.All)
            {
                var found = await AppServices.Current.Stocks.SearchAsync(
                    query, Markets.Of(id), System.Threading.CancellationToken.None);

                foreach (var pick in found)
                {
                    var named = InstrumentNames.Display(pick.Code, pick.Name);

                    if (!merged.Any(m => m.Code == pick.Code))
                    {
                        merged.Add(new WatchSuggestion(pick.Code, named));
                    }
                }
            }

            Search.ItemsSource = merged.Take(8).ToArray();
        }
        catch (Exception)
        {
            Search.ItemsSource = null;
        }
    }

    private void OnSuggestionChosen(AutoSuggestBox sender, AutoSuggestBoxSuggestionChosenEventArgs args)
    {
        if (args.SelectedItem is WatchSuggestion chosen)
        {
            _pendingChoice = chosen;
            sender.Text = chosen.Display;
        }
    }

    private void OnSearchSubmitted(AutoSuggestBox sender, AutoSuggestBoxQuerySubmittedEventArgs args)
    {
        var (code, name) = _pendingChoice is { } pick
            ? (pick.Code, pick.Name)
            : (StockDirectory.Normalize(sender.Text), string.Empty);

        _pendingChoice = null;

        if (code is null)
        {
            Notice?.Invoke(Strings.Get("StockBadCode"));
            return;
        }

        // The vendor's names can carry spaces («五 粮 液») which stretch a row's label into its
        // value. Stripped here; the bars fetch corrects the name again once it knows it.
        name = new string([.. name.Where(c => !char.IsWhiteSpace(c))]);
        name = InstrumentNames.Display(code, name);

        if (Watchlist.Has(code))
        {
            sender.Text = string.Empty;
            return;
        }

        if (Watchlist.Picks.Count >= Watchlist.Most)
        {
            Notice?.Invoke(Strings.Format("SectorTooManyStocks", Watchlist.Most));
            return;
        }

        Watchlist.Add(code, name);
        sender.Text = string.Empty;

        Changed?.Invoke(this, EventArgs.Empty);
    }

    private void OnRemove(object sender, RoutedEventArgs e)
    {
        if ((sender as FrameworkElement)?.Tag is not string code)
        {
            return;
        }

        Watchlist.Remove(code);
        Changed?.Invoke(this, EventArgs.Empty);
    }

    /// <summary>Swaps in the chip the board asked for.</summary>
    private void ApplyChipTemplate() =>
        Chips.ItemTemplate = (DataTemplate)Resources[Selectable ? "PickChip" : "PlainChip"];

    /// <summary>Whether one pick is part of what is being drawn, under whichever rule is in force.</summary>
    private bool IsOn(string code)
    {
        var picks = Watchlist.Picks;

        return _touched
            ? _on.Contains(code)
            : picks.Count > 0 && string.Equals(picks[0].Code, code, StringComparison.OrdinalIgnoreCase);
    }

    /// <summary>
    /// Puts a chip's switch where the board actually is.
    ///
    /// Hung on the template rather than pushed from here, because containers for a bound collection
    /// appear when they appear — a switch written from the picker would have to be written at a
    /// moment nobody can name, and would miss every chip rebuilt after a rename.
    /// </summary>
    private void OnChipLoaded(object sender, RoutedEventArgs e)
    {
        if (sender is ToggleButton chip && chip.Tag is string code)
        {
            chip.IsChecked = IsOn(code);
        }
    }

    /// <summary>
    /// Switches one pick in or out of this board's total.
    ///
    /// The first switch touched turns the standing rule into an explicit set: until then "what is
    /// drawn" is the first pick, and a rule is not something that can be added to or taken from.
    /// The state it is showing is carried over, so the first click does what it looks like it does
    /// rather than clearing the board.
    /// </summary>
    private void OnToggle(object sender, RoutedEventArgs e)
    {
        if (sender is not ToggleButton chip || chip.Tag is not string code)
        {
            return;
        }

        if (!_touched)
        {
            _touched = true;
            _on.Clear();

            if (Watchlist.Picks.Count > 0)
            {
                _on.Add(Watchlist.Picks[0].Code);
            }
        }

        if (chip.IsChecked == true)
        {
            _on.Add(code);
        }
        else
        {
            _on.Remove(code);
        }

        Changed?.Invoke(this, EventArgs.Empty);
    }
}
