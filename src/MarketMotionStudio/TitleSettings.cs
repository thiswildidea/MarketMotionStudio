using MarketMotionStudio.Render;
using Windows.Storage;
using Windows.UI;

namespace MarketMotionStudio;

/// <summary>
/// The headline treatment every page draws — Plain, Gilded or Engraved — and the
/// colour it is inked in, as one global choice.
///
/// The portfolio page already carries its own per-page title controls; this is the
/// default the other twenty-some pages fall back to, so the look the reader sets
/// here reaches the whole app at once instead of having to be picked page by page.
///
/// Read by <see cref="Render.TitleBlock"/> at draw time, so a change here reaches
/// every page's next redraw without a restart — the title is drawn by the same
/// renderer the preview, the video and the cover all use, which is why there is
/// no second path to keep in step. (The watermark and the frame backdrop behave
/// the same way; only the market and the language need a restart, because they
/// change which pages exist rather than how a frame is painted.)
/// </summary>
public static class TitleSettings
{
    private const string SkinKey = "TitleSkin";
    private const string ColourKey = "TitleColour";

    /// <summary>
    /// The chosen treatment. Plain until set, which is what every page shipped
    /// with — so an unset value means "leave the titles as they were".
    /// </summary>
    public static TitleSkin Skin
    {
        get => Settings.Values[SkinKey] is int value && Enum.IsDefined(typeof(TitleSkin), value)
            ? (TitleSkin)value
            : TitleSkin.Plain;
        set
        {
            Settings.Values[SkinKey] = (int)value;
            Announce();
        }
    }

    /// <summary>
    /// The colour, or null to ink each treatment in its own default. Null until a
    /// colour is picked, which leaves the defaults in place — a colour chosen here
    /// overrides every page's own default, the portfolio page included.
    /// </summary>
    public static Color? Colour
    {
        get => Settings.Values[ColourKey] is int packed && packed != 0
            ? StoredColour.Unpack(packed)
            : null;
        set
        {
            Settings.Values[ColourKey] = value is { } colour ? StoredColour.Pack(colour) : 0;
            Announce();
        }
    }

    /// <summary>Raised when either setting changes, so an open preview can redraw.</summary>
    public static event EventHandler? Changed;

    private static ApplicationDataContainer Settings => ApplicationData.Current.LocalSettings;

    private static void Announce() => Changed?.Invoke(null, EventArgs.Empty);
}
