using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// Localised display names for the built-in instruments, looked up by code.
///
/// The markets file carries every preset's name as the source spells it — Chinese,
/// because the quote source is Chinese — and that string is still the fallback. What
/// the interface shows is a resw entry keyed by the code instead, so a preset button,
/// a picker row and a chart title all answer in the language the app is running in
/// while the *request* keeps travelling by code alone: a name is never a parameter,
/// only a label.
///
/// A code without resw entries — anything the search endpoint returns beyond the
/// built-in lists — falls back to the name the source supplied, which is the honest
/// answer the app has.
/// </summary>
public static class InstrumentNames
{
    /// <summary>
    /// The name to show for a code: the current language's entry, or the fallback —
    /// the name the market file or the search result carried — when there is none.
    /// </summary>
    public static string Display(string code, string fallback) =>
        Strings.TryGet(Key(code), out var name) ? name : fallback;

    /// <summary>
    /// The resw key for a code: the code's own letters and digits, upper-cased, after
    /// a fixed prefix. `usSPY.AM` and the search endpoint's lower-case `usspy.am` both
    /// become <c>INSTUSSPYAM</c> — the source answers in whatever case it likes, and a
    /// key that cared would miss half of them. Not pretty, but the mapping is
    /// mechanical, needs no hand-maintained table, and two lists that carry the same
    /// instrument get the same name for free.
    /// </summary>
    private static string Key(string code) => "INST" + new string(
        [.. code.Where(char.IsLetterOrDigit)]).ToUpperInvariant();
}
