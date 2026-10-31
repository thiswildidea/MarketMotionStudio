using System.Text.Json;
using System.Text.Json.Serialization;
using Windows.UI;

namespace MarketMotionStudio.Render;

/// <summary>
/// The style of one line of headline type — the main title or the subtitle — as a bag of
/// *optional* choices.
///
/// Every property is nullable on purpose, and the nulls are the mechanism. A page keeps its own
/// <see cref="TitleStyle"/> in which a field it never set stays null, and
/// <see cref="Merge"/> fills each null from the global default: a field the page *did* set wins,
/// one it left alone falls through. "未配置的项回退到全局值" is therefore not a rule the page
/// has to remember to apply — it is what the record does.
///
/// Extensible by construction: a property added here is null in every stored config written
/// before it existed, so old stored values deserialize cleanly and the new field simply falls
/// back to the global answer until someone sets it. No migration, no version number.
///
/// Stored as JSON. <see cref="Colour"/> rides as the page's own "#RRGGBB" spelling rather than
/// as a packed integer, because the string survives a round trip through a text box unchanged
/// and null stays null — a packed 0 cannot be told from black.
/// </summary>
public sealed record TitleStyle
{
    /// <summary>The typeface, in the name DirectWrite resolves. Null = the app's own choice.</summary>
    public string? Font { get; init; }

    /// <summary>The size, in baseline pixels. Null = the size the page was tuned with.</summary>
    public double? Size { get; init; }

    /// <summary>The ink, as "#RRGGBB". Null = the treatment's own default colour.</summary>
    public string? Colour { get; init; }

    /// <summary>The treatment — 常规 / 镀金 / 雕琢 — as the <see cref="TitleSkin"/> number.
    /// Null = the global treatment answers.</summary>
    public int? Skin { get; init; }

    /// <summary>Whether the type is set bold. Null = bold, what every headline shipped with.</summary>
    public bool? Bold { get; init; }

    /// <summary>How many lines an automatically wrapped headline may take before the size gives
    /// way instead. Null = two, what the pages shipped with. Typed line breaks always count
    /// towards the cap, exactly as the plain title has always worked.</summary>
    public int? MaxLines { get; init; }

    /// <summary>
    /// The whole block's rotation, in degrees, clockwise. Null = level.
    ///
    /// Layout is unchanged by it on purpose: the rows are reserved for the level block, and a
    /// rotated one swings within and a little beyond the room it already paid for. Reserving for
    /// the rotated bounding box would charge every headline for a decoration most will never
    /// hang on theirs.
    /// </summary>
    public double? Rotation { get; init; }

    /// <summary>
    /// The colour as the canvas wants it, or null when the style does not name one.
    /// A colour that does not parse is the same as no colour: an unparsable choice would
    /// otherwise be a headline that refuses to draw.
    /// </summary>
    public Color? ParsedColour()
    {
        var hex = Colour;

        if (hex is not { Length: 7 } || hex[0] != '#')
        {
            return null;
        }

        return byte.TryParse(hex[1..3], System.Globalization.NumberStyles.HexNumber, null, out var r)
            && byte.TryParse(hex[3..5], System.Globalization.NumberStyles.HexNumber, null, out var g)
            && byte.TryParse(hex[5..7], System.Globalization.NumberStyles.HexNumber, null, out var b)
            ? Color.FromArgb(255, r, g, b)
            : null;
    }

    /// <summary>
    /// One style laid over another: the local choice where the page made one, the global answer
    /// where it did not.
    ///
    /// Either side may be null — a page with no local config at all is the pure global answer,
    /// and a caller with no global (none yet, but the signature says it could happen) is the
    /// pure local one.
    /// </summary>
    public static TitleStyle Merge(TitleStyle? local, TitleStyle? global) => new()
    {
        Font = local?.Font ?? global?.Font,
        Size = local?.Size ?? global?.Size,
        Colour = local?.Colour ?? global?.Colour,
        Skin = local?.Skin ?? global?.Skin,
        Bold = local?.Bold ?? global?.Bold,
        MaxLines = local?.MaxLines ?? global?.MaxLines,
        Rotation = local?.Rotation ?? global?.Rotation,
    };

    /// <summary>Reads a stored config; anything unreadable is the empty one, not an exception —
    /// a hand-edited preference file must not take the page down with it.</summary>
    public static TitleStyle FromJson(string? json)
    {
        if (string.IsNullOrWhiteSpace(json))
        {
            return new TitleStyle();
        }

        try
        {
            return JsonSerializer.Deserialize<TitleStyle>(json, Options) ?? new TitleStyle();
        }
        catch (JsonException)
        {
            return new TitleStyle();
        }
    }

    /// <summary>Writes the config for storage. Null fields are omitted, so the stored string
    /// only ever names the choices that were actually made.</summary>
    public string ToJson() => JsonSerializer.Serialize(this, Options);

    private static readonly JsonSerializerOptions Options = new()
    {
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };
}
