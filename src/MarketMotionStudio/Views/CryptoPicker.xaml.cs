using System;
using System.Collections.Generic;
using System.Linq;
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
/// **The limit is the palette's, and it is a refusal rather than a trim.** Six curves
/// read against each other are a comparison; a seventh takes a colour the sixth already
/// has. So a seventh press is not accepted and the switch stays off, which is the one
/// answer that leaves the person holding it in charge of which six.
///
/// The control keeps no store of its own: what is chosen is handed to it and handed
/// back. A preference about which coins is the page's to remember, and a control that
/// saved its own would be a second place the same choice is kept.
/// </summary>
public sealed partial class CryptoPicker : UserControl
{
    /// <summary>Raised when the choice changes, so the page can save it and redraw.</summary>
    public event EventHandler? Changed;

    private readonly List<RaceEntry> _chosen = [];

    public CryptoPicker()
    {
        InitializeComponent();

        foreach (var asset in CryptoAsset.All)
        {
            // Named by its code, not by the name it displays: the name is the one this
            // interface language spells, and anything that has to reach one of these —
            // a screen reader, a script — would otherwise need fourteen spellings.
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

        var wanted = codes.ToList();

        foreach (var asset in CryptoAsset.All)
        {
            if (!wanted.Any(c => string.Equals(c, asset.Code, StringComparison.OrdinalIgnoreCase)))
            {
                continue;
            }

            if (_chosen.Count >= Limit)
            {
                break;
            }

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

        Say();
    }

    /// <summary>The line under the row: how many are on, and the ceiling.</summary>
    private void Say() =>
        Note.Text = Strings.Format("CryptoPicksNote", _chosen.Count, Limit);

    private static CryptoAsset Asset(string code) =>
        CryptoAsset.Of(code) ?? CryptoAsset.All[0];
}
