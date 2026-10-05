using MarketMotionStudio.Render;
using Windows.Storage;

namespace MarketMotionStudio;

/// <summary>
/// Whether every exported frame carries the watermark, and what it says.
///
/// One setting for every page, and on by default: a video leaves the app as a
/// file and is posted somewhere that shows no sign of where it was made, so the
/// mark is the one thing that travels with it. Asking people to opt *in* to it
/// would mean the great majority of files went out unsigned, which is the
/// opposite of what the setting is for.
///
/// It reaches the preview, the video and the cover image, because all three are
/// drawn by the same renderer — there is no second path to update.
/// </summary>
public static class WatermarkSettings
{
    private const string OnKey = "FrameWatermarkOn";
    private const string TextKey = "FrameWatermarkText";

    /// <summary>
    /// Whether the frames carry the mark. On unless it has been turned off.
    ///
    /// Read as "on when the key is missing" rather than as "off": the setting
    /// was added to an app that has already been used, and an absent key is a
    /// machine that has never been asked, not one that answered no.
    /// </summary>
    public static bool Enabled
    {
        get => Settings.Values[OnKey] is not bool on || on;
        set
        {
            Settings.Values[OnKey] = value;
            Announce();
        }
    }

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

    private static Watermark? Resolve() => Enabled ? new Watermark(Text) : null;

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
