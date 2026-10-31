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

    /// <summary>
    /// The typefaces the title style offers, in the names DirectWrite resolves.
    ///
    /// CJK faces first — the frames are written in Chinese — and the first entry is null, which
    /// is not a face but "not chosen": a combo needs something to show for "I did not choose",
    /// and a null tag is exactly that, carried through to the style record as a field left
    /// unset. The list is deliberately short — a headline choice, not a font browser — and every
    /// face here ships with Windows.
    /// </summary>
    public static readonly (string? Family, string Label)[] Fonts =
    [
        (null, ""),
        ("Microsoft YaHei", "微软雅黑"),
        ("SimHei", "黑体"),
        ("SimSun", "宋体"),
        ("KaiTi", "楷体"),
        ("FangSong", "仿宋"),
        ("DengXian", "等线"),
        ("Arial", "Arial"),
        ("Georgia", "Georgia"),
        ("Impact", "Impact"),
    ];

    /// <summary>Raised when either setting changes, so an open preview can redraw.</summary>
    public static event EventHandler? Changed;

    // ---- the extensible half: what the two-layer title style falls back to ---------------

    private const string FontKey = "TitleFont";
    private const string SizeKey = "TitleSize";
    private const string RotationKey = "TitleRotation";
    private const string MaxLinesKey = "TitleMaxLines";
    private const string SubtitleKey = "TitleSubtitleStyle";

    /// <summary>The global headline typeface, or null for the app's own choice — the face
    /// every page shipped with. Read by <see cref="Render.TitleBlock"/> when neither the page
    /// nor anything else names a font.</summary>
    public static string? Font
    {
        get => Settings.Values[FontKey] as string;
        set
        {
            Set(FontKey, string.IsNullOrWhiteSpace(value) ? null : value);
            Announce();
        }
    }

    /// <summary>The global headline size, in baseline pixels. Null = each page keeps the size
    /// its header block was tuned against — which is what an unset value has to mean, because
    /// one size does not fit pages whose headline rows were each measured separately.</summary>
    public static double? Size
    {
        get => Settings.Values[SizeKey] is double value && value > 0 ? value : null;
        set
        {
            Set(SizeKey, value is > 0 ? value : null);
            Announce();
        }
    }

    /// <summary>The global headline rotation, in degrees. Null (and zero) = level.</summary>
    public static double? Rotation
    {
        get => Settings.Values[RotationKey] is double value && value != 0 ? value : null;
        set
        {
            Set(RotationKey, value is { } v && v != 0 ? v : null);
            Announce();
        }
    }

    /// <summary>Stores one optional setting: a null answer removes the key, because a container
    /// value set to literal null is not the same as an absent one — the getter would have to
    /// unpick both shapes forever after.</summary>
    private static void Set(string key, object? value)
    {
        if (value is { } stored)
        {
            Settings.Values[key] = stored;
        }
        else
        {
            Settings.Values.Remove(key);
        }
    }

    /// <summary>The global wrap cap for the headline, or null for the two lines every page
    /// shipped with. Typed line breaks are honoured on top of the cap, as always.</summary>
    public static int? MaxLines
    {
        get => Settings.Values[MaxLinesKey] is int value && value > 0 ? value : null;
        set
        {
            Set(MaxLinesKey, value is > 0 ? value : null);
            Announce();
        }
    }

    /// <summary>
    /// The global default for the **subtitle** — a second line of headline under the main one.
    ///
    /// The subtitle's *text* is not a global setting: what a subtitle says belongs to the page
    /// drawing it. What a subtitle looks like, though, is exactly the kind of choice one answer
    /// serves, so the treatment, face, size and colour live here and a page's own subtitle style
    /// overrides it field by field.
    /// </summary>
    public static Render.TitleStyle SubtitleStyle
    {
        get => Render.TitleStyle.FromJson(Settings.Values[SubtitleKey] as string);
        set
        {
            var json = value?.ToJson();

            if (string.IsNullOrEmpty(json) || json == "{}")
            {
                Settings.Values.Remove(SubtitleKey);
            }
            else
            {
                Settings.Values[SubtitleKey] = json;
            }

            Announce();
        }
    }

    /// <summary>
    /// The global default for the **main title**, as one <see cref="Render.TitleStyle"/>: the
    /// treatment and colour this class has always carried, plus the face, size and rotation the
    /// two-layer mechanism added. This is what a page's own title style merges over.
    /// </summary>
    public static Render.TitleStyle MainStyle => new()
    {
        Skin = (int)Skin,
        Colour = Colour is { } colour
            ? $"#{colour.R:X2}{colour.G:X2}{colour.B:X2}"
            : null,
        Font = Font,
        Size = Size,
        MaxLines = MaxLines,
        Rotation = Rotation,
    };

    private static ApplicationDataContainer Settings => ApplicationData.Current.LocalSettings;

    private static void Announce() => Changed?.Invoke(null, EventArgs.Empty);
}
