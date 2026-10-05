using MarketMotionStudio.Render;
using Windows.Storage;
using Windows.UI;

namespace MarketMotionStudio;

/// <summary>
/// What the animation frames are drawn on: the default gradient, a gradient of
/// the user's own two colours, or a picture.
///
/// One setting for every page, not one per page. A frame is a video that will
/// be posted somewhere, and the reason to change its backdrop is a reason
/// about the person posting — a channel's colours, a branded background — which
/// is the same on the turnover page as on the calendar. Seven copies of this
/// setting would be seven places to keep in step for a choice that is made
/// once.
///
/// It reaches the video and the cover PNG as well as the preview, because all
/// three are drawn by the same renderer: there is no second path to update.
/// </summary>
public static class AnimationBackdrop
{
    private const string KindKey = "FrameBackdropKind";
    private const string TopKey = "FrameBackdropTop";
    private const string BottomKey = "FrameBackdropBottom";
    private const string DimKey = "FrameBackdropDim";
    private const string StrengthKey = "FrameBackdropStrength";

    /// <summary>
    /// The dimming range for a picture, in percent. Not down to zero: every
    /// text colour in every frame is a light tone chosen against the dark
    /// default, so a picture at full strength costs the numbers their
    /// legibility. The floor is what keeps the choice a matter of taste rather
    /// than of whether the video can be read.
    /// </summary>
    public const int MinDim = 20;

    public const int MaxDim = 95;

    public const int DefaultDim = 60;

    /// <summary>
    /// The opacity range for a colour, in percent. The top is full: two colour
    /// stops are the whole point of choosing them, and a pair that cannot be
    /// had at full strength is a pair that was not really offered. The floor
    /// keeps a colour from being set so faint that it is only a tint of the
    /// frame's own backdrop and the choice stops reading as a choice.
    /// </summary>
    public const int MinStrength = 20;

    public const int MaxStrength = 100;

    public const int DefaultStrength = 100;

    /// <summary>
    /// Its own copies, separate from the window's. See <see cref="PictureLibrary"/>.
    ///
    /// Reachable to the Settings page, which builds one gallery for both sets of
    /// pictures rather than two copies of the same code.
    /// </summary>
    internal static PictureLibrary Pictures { get; } = new("FrameBackdrop", "FrameBackdrops");

    /// <summary>Raised when the backdrop changed, so open previews redraw.</summary>
    public static event EventHandler? Changed;

    static AnimationBackdrop()
    {
        Pictures.Changed += (_, _) => Announce();
    }

    private static ApplicationDataContainer Settings => ApplicationData.Current.LocalSettings;

    public static string[] FileTypes => PictureLibrary.FileTypes;

    public static BackdropKind Kind
    {
        get => Settings.Values[KindKey] is int kind && Enum.IsDefined(typeof(BackdropKind), kind)
            ? (BackdropKind)kind
            : BackdropKind.Default;
        set
        {
            Settings.Values[KindKey] = (int)value;
            Announce();
        }
    }

    /// <summary>The top of the gradient, used when <see cref="Kind"/> is a colour.</summary>
    public static Color Top
    {
        get => Read(TopKey, Palette.Background[0].Colour);
        set
        {
            Settings.Values[TopKey] = StoredColour.Pack(value);
            Announce();
        }
    }

    /// <summary>The bottom of the gradient, used when <see cref="Kind"/> is a colour.</summary>
    public static Color Bottom
    {
        get => Read(BottomKey, Palette.Background[^1].Colour);
        set
        {
            Settings.Values[BottomKey] = StoredColour.Pack(value);
            Announce();
        }
    }

    /// <summary>
    /// How far a picture is faded back towards the frame's own backdrop, in percent.
    /// </summary>
    public static int Dim
    {
        get => Settings.Values[DimKey] is int dim ? Math.Clamp(dim, MinDim, MaxDim) : DefaultDim;
        set
        {
            Settings.Values[DimKey] = Math.Clamp(value, MinDim, MaxDim);
            Announce();
        }
    }

    /// <summary>
    /// How opaque the two chosen colours are, in percent, for <see cref="BackdropKind.Colour"/>.
    ///
    /// Unlike <see cref="Dim"/> this runs the other way: 100 is the colours as
    /// chosen and lower lets the page's own gradient through. A picture needs
    /// holding back because it arrives with colours of its own; a colour was
    /// chosen, so what there is to decide about it is how much of it to use.
    /// </summary>
    public static int Strength
    {
        get => Settings.Values[StrengthKey] is int strength
            ? Math.Clamp(strength, MinStrength, MaxStrength)
            : DefaultStrength;
        set
        {
            Settings.Values[StrengthKey] = Math.Clamp(value, MinStrength, MaxStrength);
            Announce();
        }
    }

    /// <summary>The chosen picture, or null when there is none.</summary>
    public static string? Picture => Pictures.Current;

    /// <summary>Earlier pictures, most recent first, only those still on disk.</summary>
    public static IReadOnlyList<string> Recent => Pictures.Recent;

    /// <summary>This Windows' own wallpapers, offered alongside the user's.</summary>
    public static IReadOnlyList<string> SystemPictures => PictureLibrary.SystemPictures;

    /// <summary>Picks a picture, copies it in, and makes it the backdrop.</summary>
    public static Task UsePictureAsync(StorageFile picked) => Pictures.UseNewAsync(picked);

    /// <summary>Makes a kept picture, or one of Windows' own, the backdrop.</summary>
    public static void UsePicture(string path) => Pictures.Use(path);

    /// <summary>Stops using a picture. It stays on the recent list.</summary>
    public static void ClearPicture() => Pictures.Clear();

    /// <summary>Forgets one of the kept pictures and deletes its copy.</summary>
    public static void ForgetPicture(string path) => Pictures.Forget(path);

    /// <summary>
    /// The backdrop as the renderers need it.
    ///
    /// Resolved once per change rather than per frame: an export asks for this
    /// on every one of its thousands of frames, and reading it out of the
    /// settings container that often is a look-up the drawing does not need.
    /// Assigned rather than invalidated, so a reader on the encoder's thread
    /// never sees a half-built value — it sees either the previous backdrop or
    /// the new one.
    /// </summary>
    public static Backdrop Current => _resolved ??= Resolve();

    private static Backdrop? _resolved;

    private static Backdrop Resolve() =>
        new(Kind, Top, Bottom, Pictures.Current, Dim / 100.0, Strength / 100.0);

    private static void Announce()
    {
        _resolved = Resolve();
        Changed?.Invoke(null, EventArgs.Empty);
    }

    private static Color Read(string key, Color fallback) => StoredColour.Read(Settings, key, fallback);
}
