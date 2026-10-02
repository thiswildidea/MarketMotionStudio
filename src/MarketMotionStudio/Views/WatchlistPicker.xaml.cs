using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Pages;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

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

    public WatchlistPicker()
    {
        InitializeComponent();

        Watchlist.EnsureLoaded();
        Chips.ItemsSource = Watchlist.Picks;

        _searchDebounce.Tick += async (_, _) =>
        {
            _searchDebounce.Stop();
            await SuggestAsync(_lastQuery);
        };
    }

    /// <summary>What is on the list, as the board can draw it.</summary>
    public IReadOnlyList<RaceEntry> Entries => [.. Watchlist.Picks];

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
}
