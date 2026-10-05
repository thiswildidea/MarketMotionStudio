using MarketMotionStudio.Render;
using Windows.Storage;
using Windows.UI;

namespace MarketMotionStudio;

/// <summary>
/// Whether every exported frame carries the watermark, what it says, and how it
/// is set: the font, the colour and how strongly it is drawn.
///
/// One setting for every page, and on by default: a video leaves the app as a
/// file and is posted somewhere that shows no sign of where it was made, so the
/// mark is the one thing that travels with it. Asking people to opt *in* to it
/// would mean the great majority of files went out unsigned, which is the
/// opposite of what the setting is for.
///
/// It reaches the preview, the video and the cover image, because all three are
/// drawn by the same renderer — there is no second path to update.
///
/// **Taking it off now costs a subscription, and that is decided here rather
/// than in the control that looks like it decides it.** This is the one place
/// every renderer asks; a switch that merely refuses to be clicked leaves every
/// other caller free to draw an unmarked frame, and the app is one XAML file
/// away from having one. What the switch does is ask this, not hold the answer.
/// </summary>
public static class WatermarkSettings
{
    static WatermarkSettings()
    {
        // A frame already drawn does not redraw itself, and the mark is baked
        // into the frame rather than laid over it. Nothing else knows when the
        // answer changes, so nothing else can be relied on to invalidate it.
        AppServices.Current.Subscription.Changed += (_, _) => Announce();
    }

    private const string OnKey = "FrameWatermarkOn";
    private const string TextKey = "FrameWatermarkText";
    private const string FontKey = "FrameWatermarkFont";
    private const string ColourKey = "FrameWatermarkColour";
    private const string StrengthKey = "FrameWatermarkStrength";

    /// <summary>
    /// Whether the frames carry the mark. On unless it has been turned off, and
    /// **on regardless of what was asked for while nobody is subscribed** —
    /// taking the mark off is one of the two things the subscription buys.
    ///
    /// Read as "on when the key is missing" rather than as "off": the setting
    /// was added to an app that has already been used, and an absent key is a
    /// machine that has never been asked, not one that answered no. The stored
    /// answer is still kept while unpaid, so subscribing restores the frame
    /// somebody was trying to make rather than pretending the switch was never
    /// touched.
    /// </summary>
    public static bool Enabled
    {
        get
        {
            if (PaidFor)
            {
                return Settings.Values[OnKey] is not bool on || on;
            }

            return true;
        }
        set
        {
            Settings.Values[OnKey] = value;
            Announce();
        }
    }

    /// <summary>
    /// Whether the switch is anybody's to move. Read by the control rather than
    /// baked into it, so that "greyed out" and "ignored" are the same fact in
    /// one place and cannot drift the way a duplicated rule would.
    /// </summary>
    public static bool Optional => PaidFor;

    private static bool PaidFor => AppServices.Current.Subscription.Subscribed;

    /// <summary>
    /// What the mark says.
    ///
    /// Falling back to <see cref="Watermark.DefaultText"/> when the stored text
    /// is blank rather than drawing nothing: a mark that was deleted becomes no
    /// mark at all, which is what the switch is for, so the two controls would
    /// be asking the same question twice and disagreeing about the answer.
    /// </summary>
    public static string Text
    {
        get => Settings.Values[TextKey] is string text && text.Trim().Length > 0
            ? text
            : Watermark.DefaultText;
        set
        {
            Settings.Values[TextKey] = Trim(value);
            Announce();
        }
    }

    /// <summary>
    /// Which font it is set in, as the name Windows calls it.
    ///
    /// A stored name this machine does not have is not checked against the fonts
    /// it does have: that would be a read that enumerates several hundred fonts
    /// every time a frame is drawn, and a name that has gone missing is a font
    /// the drawing falls back from anyway — the mark still says what it says,
    /// which is the half that matters. Blank falls back to the default font, as
    /// the text does to the default name, so that clearing a control is never
    /// how you turn the mark off.
    /// </summary>
    public static string Family
    {
        get => Settings.Values[FontKey] is string font && font.Trim().Length > 0
            ? font
            : Watermark.DefaultFamily;
        set
        {
            Settings.Values[FontKey] = (value ?? string.Empty).Trim();
            Announce();
        }
    }

    /// <summary>
    /// Its colour. Stored as one integer; see <see cref="StoredColour"/>.
    /// </summary>
    public static Color Colour
    {
        get => StoredColour.Read(Settings, ColourKey, Watermark.DefaultColour);
        set
        {
            Settings.Values[ColourKey] = StoredColour.Pack(value);
            Announce();
        }
    }

    /// <summary>
    /// How strongly it is drawn, in percent — the one number behind "how visible
    /// is it", which the colour alone cannot answer: at the default tenth, white,
    /// amber and blue all come out as the same faint wash.
    /// </summary>
    public static int Strength
    {
        get => Settings.Values[StrengthKey] is int strength
            ? Math.Clamp(strength, Watermark.MinOpacity, Watermark.MaxOpacity)
            : Watermark.DefaultOpacity;
        set
        {
            Settings.Values[StrengthKey] =
                Math.Clamp(value, Watermark.MinOpacity, Watermark.MaxOpacity);
            Announce();
        }
    }

    /// <summary>The longest name the text box accepts, in characters.</summary>
    public static int MaxLength => Watermark.MaxLength;

    /// <summary>Raised when either setting changed, so open previews redraw.</summary>
    public static event EventHandler? Changed;

    /// <summary>
    /// The watermark as the renderers need it, or null when it is off.
    ///
    /// Resolved once per change rather than per frame, for the same reason the
    /// backdrop is: an export asks on every one of thousands of frames.
    /// Assigned rather than invalidated, so a reader on the encoder's thread
    /// sees either the previous watermark or the new one and never a half-built
    /// one — and a frame drawn before the change and a frame drawn after it are
    /// each fully one or the other.
    ///
    /// Null is how "off" travels. A renderer that has no watermark is one with
    /// nothing to draw, and a record that would have to be asked whether it
    /// means anything is a question every drawing call would have to remember
    /// to ask.
    /// </summary>
    public static Watermark? Current => _resolved ??= Resolve();

    private static Watermark? _resolved;

    private static ApplicationDataContainer Settings => ApplicationData.Current.LocalSettings;

    private static Watermark? Resolve() =>
        Enabled ? new Watermark(Text, Family, Colour, Watermark.AlphaOf(Strength)) : null;

    private static void Announce()
    {
        _resolved = Resolve();
        Changed?.Invoke(null, EventArgs.Empty);
    }

    /// <summary>
    /// What is stored: the text without its surrounding space, and no longer
    /// than the mark can carry.
    /// </summary>
    private static string Trim(string? text)
    {
        var trimmed = (text ?? string.Empty).Trim();

        return trimmed.Length <= Watermark.MaxLength ? trimmed : trimmed[..Watermark.MaxLength];
    }
}
