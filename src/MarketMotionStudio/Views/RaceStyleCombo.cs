using MarketMotionStudio.Localization;
using MarketMotionStudio.Pages;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace MarketMotionStudio.Views;

/// <summary>
/// The display-style picker the race pages share: 条形竞速 and the four re-stagings of the
/// same standings, ported from NbaMotionStudio's career-race page.
///
/// A <see cref="ComboBox"/> subclass rather than a panel, so a page places it among its own
/// combo boxes and it looks like them. It owns its persistence: <see cref="Bind"/> hands it
/// the page's <see cref="StudioPreferences"/>, from which it restores the saved style once
/// and saves every change after. Raising <see cref="Chosen"/> is all a page has to answer —
/// which, like every parameter on these pages, means "rebuild the renderer and redraw".
/// </summary>
public sealed class RaceStyleCombo : ComboBox
{
    /// <summary>The menu, in the order the styles shipped: the original race first.</summary>
    public static readonly (RaceStyle Style, string Key)[] Styles =
    [
        (RaceStyle.Bar, "RaceStyleBar"),
        (RaceStyle.Podium, "RaceStylePodium"),
        (RaceStyle.Skyline, "RaceStyleSkyline"),
        (RaceStyle.Pyramid, "RaceStylePyramid"),
        (RaceStyle.FocusTour, "RaceStyleFocusTour"),
    ];

    /// <summary>Raised on a change that was not the population or the restore itself.</summary>
    public event EventHandler? Chosen;

    private StudioPreferences? _prefs;

    /// <summary>
    /// Guards everything the control selects on its own — the constructor's default and
    /// <see cref="Bind"/>'s restore. A flag only protects the assignments that come after
    /// it, and populating a combo box selects its first item: without the guard the first
    /// item's selection would save a default over the value about to be restored.
    /// </summary>
    private bool _loading = true;

    public RaceStyleCombo()
    {
        Header = Strings.Get("RaceStyleHeader");
        HorizontalAlignment = HorizontalAlignment.Stretch;

        foreach (var (style, key) in Styles)
        {
            Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = style });
        }

        SelectedIndex = 0;
        _loading = false;

        SelectionChanged += OnSelection;
    }

    /// <summary>The style on the menu right now, Bar when nothing holds.</summary>
    public RaceStyle ChosenStyle =>
        SelectedItem is ComboBoxItem { Tag: RaceStyle style } ? style : RaceStyle.Bar;

    /// <summary>
    /// Hands the control its page's preferences: the saved style is restored here, and
    /// every change afterwards saves itself. Called from the page's constructor, inside
    /// the restore window the page already holds open — a double guard, since a save of
    /// the value being restored is the one mistake this dance exists to prevent.
    /// </summary>
    public void Bind(StudioPreferences prefs)
    {
        _prefs = prefs;

        var saved = Math.Clamp(prefs.GetInt("Style", (int)RaceStyle.Bar), 0, Styles.Length - 1);

        _loading = true;

        // Restored by tag, not by position, like every menu on these pages.
        SelectedItem = Items.OfType<ComboBoxItem>().FirstOrDefault(i => i.Tag is RaceStyle s && (int)s == saved)
            ?? Items[0];

        _loading = false;
    }

    private void OnSelection(object sender, SelectionChangedEventArgs e)
    {
        if (_loading)
        {
            return;
        }

        _prefs?.Save("Style", (int)ChosenStyle);
        Chosen?.Invoke(this, EventArgs.Empty);
    }
}
