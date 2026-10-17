using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Automation;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Views;

/// <summary>
/// Which coins a frame is about, as one row of switches the three crypto pages share.
///
/// Its own control rather than the watchlist picker the stock pages bind to, and the
/// reason is that the two lists are not the same kind of thing. <c>Watchlist</c> holds
/// market codes a person typed in and every roster board reads it; a coin's code is not
/// a market code, and putting one on that list would have the stock pages asking a
/// Chinese quote endpoint about <c>BTC</c>. So the coins are their own list, kept by
/// the page that chose them and shared by the three that offer them — the same idea as
/// the watchlist, about a different set of instruments.
///
/// **The row opens as the twelve, and the box finds the rest.** Typing narrows the twelve while it
/// is typed, and the same word is asked of the sources; what comes back that is not already a switch
/// appears under the box, and choosing one there puts it on the row. A coin found this way is
/// written down (<see cref="CryptoRegistry"/>), so the next run opens with it as a switch like any
/// other. The stock pages' picker works this way, and the two boxes reading the same way is the
/// point of reading one before writing the other.
///
/// **The limit is the palette's, and it is a refusal rather than a trim.** Six curves
/// read against each other are a comparison; a seventh takes a colour the sixth already
/// has. So a seventh press is not accepted and the switch stays off, which is the one
/// answer that leaves the person holding it in charge of which six.
///
/// The control keeps no store of its own: what is chosen is handed to it and handed
/// back. A preference about which coins is the page's to remember, and a control that
/// saved its own would be a second place the same choice is kept. The coins a search added are
/// remembered, but that is a different question — which coins exist, not which are on this frame.
/// </summary>
public sealed partial class CryptoPicker : UserControl
{
    /// <summary>Raised when the choice changes, so the page can save it and redraw.</summary>
    public event EventHandler? Changed;

    private readonly List<RaceEntry> _chosen = [];

    /// <summary>How long after the last keystroke the sources are asked, so a word is one request.</summary>
    private readonly DispatcherTimer _search = new() { Interval = TimeSpan.FromMilliseconds(260) };

    /// <summary>What the box currently reads.</summary>
    private string _typed = string.Empty;

    /// <summary>What the last request that was sent asked for, so a late answer to an older word is dropped.</summary>
    private string _asked = string.Empty;

    public CryptoPicker()
    {
        InitializeComponent();

        // Named the way the switches are named — see the note on `AutomationId` below.
        // `x:Uid` is what localises these two and is not reliably what names them for
        // anything that has to reach them: the switches are named here in code and are
        // found, the box was left to its own markup and was not.
        AutomationProperties.SetAutomationId(Search, "CryptoSearch");
        AutomationProperties.SetAutomationId(NoMatch, "CryptoSearchNone");

        // The coins a search added in an earlier run are read here too, so they open as switches
        // beside the twelve — the same row the run that added them left behind.
        CryptoRegistry.EnsureLoaded();

        foreach (var asset in CryptoAsset.All.Concat(CryptoAsset.Extra))
        {
            AddChip(asset);
        }

        _search.Tick += async (_, _) =>
        {
            _search.Stop();
            await FindAsync();
        };

        Say();
    }

    /// <summary>
    /// How many coins one frame will hold.
    ///
    /// Six by inheritance — <see cref="CryptoCandleLoader.MostTracks"/> and the two
    /// loaders beside it — and settable because the candle page's split frame takes
    /// fewer panels than the palette has colours.
    /// </summary>
    public int Limit { get; set; } = CryptoCandleLoader.MostTracks;

    /// <summary>What is on the frame, in the order it was chosen.</summary>
    public IReadOnlyList<RaceEntry> Selected => _chosen;

    /// <summary>
    /// Puts these coins on the frame and nothing else, without raising
    /// <see cref="Changed"/> — a restore, not a choice.
    /// </summary>
    public void Select(IEnumerable<string> codes)
    {
        _chosen.Clear();

        foreach (var code in codes)
        {
            if (_chosen.Count >= Limit)
            {
                break;
            }

            // One of the twelve, or one a search brought in on an earlier run — `Of` is the one
            // place that knows both, and the switch for either is already built.
            if (CryptoAsset.Of(code) is not { } asset)
            {
                continue;
            }

            AddChip(asset);
            _chosen.Add(new RaceEntry(asset.Code, asset.Display));
        }

        // At least one, or the frame has nothing to draw: the first coin when a stored
        // preference names none — which is what a first run does.
        if (_chosen.Count == 0)
        {
            var first = CryptoAsset.All[0];
            _chosen.Add(new RaceEntry(first.Code, first.Display));
        }

        Paint();
    }

    /// <summary>Whether a coin is on the frame.</summary>
    public bool Has(string code) =>
        _chosen.Any(c => string.Equals(c.Code, code, StringComparison.OrdinalIgnoreCase));

    /// <summary>
    /// One coin's switch, named by its code rather than by the name it displays: the name is the
    /// one this interface language spells, and anything that has to reach one of these — a screen
    /// reader, a script — would otherwise need fourteen spellings.
    /// </summary>
    private void AddChip(CryptoAsset asset)
    {
        if (Coins.Children.OfType<ToggleButton>()
                .Any(c => string.Equals(c.Tag as string, asset.Code, StringComparison.OrdinalIgnoreCase)))
        {
            return;
        }

        var chip = new ToggleButton
        {
            Content = asset.Display,
            Tag = asset.Code,
            Margin = new Thickness(0, 0, 8, 6),
        };

        AutomationProperties.SetAutomationId(chip, "Coin" + asset.Code);
        AutomationProperties.SetName(chip, asset.Display);

        chip.Click += OnCoinClick;

        Coins.Children.Add(chip);
    }

    private void OnCoinClick(object sender, RoutedEventArgs e)
    {
        if (sender is not ToggleButton chip || chip.Tag is not string code)
        {
            return;
        }

        if (chip.IsChecked == true)
        {
            if (_chosen.Count >= Limit)
            {
                // Refused, and the switch goes back: see the note on `Limit`.
                chip.IsChecked = false;
                Say();

                return;
            }

            _chosen.Add(new RaceEntry(code, Asset(code).Display));
        }
        else
        {
            _chosen.RemoveAll(c => string.Equals(c.Code, code, StringComparison.OrdinalIgnoreCase));
        }

        Paint();

        Changed?.Invoke(this, EventArgs.Empty);
    }

    /// <summary>Every switch set to whether its coin is on the frame.</summary>
    private void Paint()
    {
        foreach (var child in Coins.Children)
        {
            if (child is ToggleButton chip && chip.Tag is string code)
            {
                chip.IsChecked = Has(code);
            }
        }

        // After the switches, not before: a coin that was just chosen has to be shown
        // even when the box would have hidden it — see `Shows`.
        Narrow();

        Say();
    }

    private void OnSearchChanged(object sender, TextChangedEventArgs e)
    {
        _typed = Search.Text;

        Narrow();

        // Restarted rather than left running, so a word is one request when the typing stops —
        // the same debounce the stock picker uses.
        _search.Stop();
        _search.Start();
    }

    /// <summary>
    /// Asks the sources what was typed, and shows what came back that is not already a switch.
    ///
    /// The answer to an older word is dropped: a search is a round trip, and the reply to `bit`
    /// landing after the reply to `bitco` would put the wrong list under a box that reads `bitco`.
    /// A source that cannot be reached answers nothing, which reads the same as a word that matched
    /// nothing — the honest thing to say, and not an error to report over a box that still narrows.
    /// </summary>
    private async Task FindAsync()
    {
        var typed = _typed.Trim();

        if (typed.Length == 0)
        {
            ShowFound([]);

            return;
        }

        _asked = typed;

        IReadOnlyList<CryptoAsset> answered;

        try
        {
            answered = await AppServices.Current.Crypto.SearchAsync(typed, CancellationToken.None);
        }
        catch (Exception)
        {
            answered = [];
        }

        if (!string.Equals(typed, _asked, StringComparison.Ordinal)
            || !string.Equals(typed, _typed.Trim(), StringComparison.Ordinal))
        {
            return;
        }

        var fresh = new List<CryptoAsset>();

        foreach (var asset in answered)
        {
            // Already a switch on the row — one of the twelve, or added earlier — so it is toggled
            // below rather than added here. Two results for one code is also one switch.
            if (CryptoAsset.Of(asset.Code) is not null
                || fresh.Any(f => string.Equals(f.Code, asset.Code, StringComparison.OrdinalIgnoreCase)))
            {
                continue;
            }

            fresh.Add(asset);

            if (fresh.Count >= 8)
            {
                break;
            }
        }

        ShowFound(fresh);
    }

    /// <summary>Puts the search results under the box, one pressable row each.</summary>
    private void ShowFound(IReadOnlyList<CryptoAsset> found)
    {
        Found.Children.Clear();

        foreach (var asset in found)
        {
            var row = new Button
            {
                Content = $"{asset.Display} · {asset.Code}",
                Tag = asset,
                HorizontalAlignment = HorizontalAlignment.Stretch,
                HorizontalContentAlignment = HorizontalAlignment.Left,
            };

            AutomationProperties.SetAutomationId(row, "Sugg" + asset.Code);
            row.Click += OnFoundClick;

            Found.Children.Add(row);
        }

        Found.Visibility = found.Count > 0 ? Visibility.Visible : Visibility.Collapsed;
    }

    private void OnFoundClick(object sender, RoutedEventArgs e)
    {
        if (sender is Button { Tag: CryptoAsset asset })
        {
            Choose(asset);
        }
    }

    /// <summary>
    /// Puts a searched coin on the frame, by the same rules a switch is held to.
    ///
    /// Refused at the ceiling rather than trimmed, exactly as a seventh switch is; and written down
    /// only once it is taken, so a search that ended in a refusal does not grow the list for a run
    /// that would not have shown the coin.
    /// </summary>
    private void Choose(CryptoAsset asset)
    {
        if (_chosen.Count >= Limit)
        {
            Say();

            return;
        }

        CryptoRegistry.Remember(asset);
        AddChip(asset);

        _chosen.Add(new RaceEntry(asset.Code, asset.Display));

        // Clears the box and what it found: the coin is a switch on the row now, and a list that
        // still offered it would read as it not having been taken. Assigning `Text` runs
        // `OnSearchChanged`, which puts the twelve back and asks the empty word nothing.
        Search.Text = string.Empty;
        ShowFound([]);

        Paint();

        Changed?.Invoke(this, EventArgs.Empty);
    }

    /// <summary>
    /// Shows the coins whose name or code contains what was typed, and puts the rest
    /// away.
    ///
    /// The name it measures against is the one **this** interface language spells —
    /// the same one written on the switch beside it — so a typed word means what it
    /// looks like it means, and the answer to "how do I find it" is "spell it the way
    /// the app spells it". The code is matched as well, because a code is what a
    /// person who already knows what they want types.
    ///
    /// A coin that is on the frame is shown whatever was typed. It is part of the
    /// answer being asked for, and a row that hid it would leave the count on the line
    /// below — "已选 3 个" — with nothing on the row to account for it.
    /// </summary>
    private void Narrow()
    {
        var typed = Search.Text.Trim();
        var hits = 0;

        foreach (var child in Coins.Children)
        {
            if (child is not ToggleButton chip || chip.Tag is not string code)
            {
                continue;
            }

            // Counted apart from what is shown. A chosen coin stays on the row whatever
            // was typed (see `Shows`), so "the row is not empty" is not the same question
            // as "the word found something" — and it is the second one the line below
            // answers. Counted the other way, typing a word that matches nothing leaves
            // the chosen coins sitting there with nothing said, which reads as the box
            // having stopped working.
            if (TypedMatches(code, typed))
            {
                hits++;
            }

            chip.Visibility = Shows(code, typed) ? Visibility.Visible : Visibility.Collapsed;
        }

        NoMatch.Visibility = typed.Length > 0 && hits == 0
            ? Visibility.Visible
            : Visibility.Collapsed;
    }

    /// <summary>Whether a coin belongs on the row while this much has been typed.</summary>
    private bool Shows(string code, string typed) => TypedMatches(code, typed) || Has(code);

    /// <summary>
    /// Whether what was typed names this coin — by the name this interface language
    /// spells, or by the code.
    ///
    /// These are the two things a person can see: the word on the switch, and the
    /// code, which is what somebody who already knows what they want types.
    /// </summary>
    private bool TypedMatches(string code, string typed) =>
        typed.Length == 0
        || Asset(code).Display.Contains(typed, StringComparison.OrdinalIgnoreCase)
        || code.Contains(typed, StringComparison.OrdinalIgnoreCase);

    /// <summary>The line under the row: how many are on, and the ceiling.</summary>
    private void Say() =>
        Note.Text = Strings.Format("CryptoPicksNote", _chosen.Count, Limit);

    private static CryptoAsset Asset(string code) =>
        CryptoAsset.Of(code) ?? CryptoAsset.All[0];
}
