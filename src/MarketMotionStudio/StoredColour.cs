using Windows.UI;

namespace MarketMotionStudio;

/// <summary>
/// A colour as the settings container holds it.
///
/// One integer rather than <c>#RRGGBB</c>: a string is parsed at every read, and a
/// value nobody edits by hand gains nothing from being readable in a file.
///
/// Shared because two settings keep a colour now — the frame's backdrop and the
/// watermark — and a second copy of the packing is a second answer to "what does
/// this number mean". It is the one thing about a stored colour that would be
/// silently wrong rather than loudly: unpacked the other way round, the same
/// number is a different colour, and nothing reports a mismatch.
/// </summary>
internal static class StoredColour
{
    /// <summary>A colour packed into one integer, alpha in the high byte.</summary>
    public static int Pack(Color colour) =>
        (colour.A << 24) | (colour.R << 16) | (colour.G << 8) | colour.B;

    /// <summary>The colour a packed integer is. See <see cref="Pack"/>.</summary>
    public static Color Unpack(int packed) => Color.FromArgb(
        (byte)((packed >> 24) & 0xFF),
        (byte)((packed >> 16) & 0xFF),
        (byte)((packed >> 8) & 0xFF),
        (byte)(packed & 0xFF));

    /// <summary>
    /// A stored colour, or <paramref name="fallback"/> when the key holds nothing.
    ///
    /// The key is read here rather than at each call site so that "missing means
    /// the default" is stated once: a setting added to an app that has already
    /// been used meets an absent key on machines that were never asked.
    /// </summary>
    public static Color Read(Windows.Storage.ApplicationDataContainer settings, string key, Color fallback) =>
        settings.Values[key] is int packed ? Unpack(packed) : fallback;
}
