using System.Globalization;
using Microsoft.Windows.ApplicationModel.Resources;

namespace AShareMotionStudio.Localization;

/// <summary>
/// Lookup for strings that are built in code rather than declared in XAML.
///
/// Anything static in the UI should use x:Uid instead, so the framework resolves
/// it without code. This exists for the rest: messages with runtime values, and
/// text chosen by a branch.
/// </summary>
public static class Strings
{
    private static readonly ResourceLoader Loader = new();

    /// <summary>
    /// The culture matching the language the interface actually resolved to.
    ///
    /// **Not `CultureInfo.CurrentCulture`, and the difference is not academic.** A language
    /// pinned in Settings goes through `PrimaryLanguageOverride`, which redirects *resource*
    /// lookup; the thread's culture still follows the operating system. So on an English Windows
    /// showing a Chinese interface, `CurrentCulture` is `en-US` — which rendered a calendar's
    /// month as "Jun" and its weekday row as "M T W T F" inside an otherwise Chinese frame.
    ///
    /// The fix is the trick this shell already uses to pick the help document: let the resources
    /// name the answer. `CultureName` is a per-language string, so whichever language MRT chose —
    /// including by its own fallback rules — is the one that answers, and there is one resolution
    /// rather than two free to disagree.
    ///
    /// Cached because the language cannot change without a restart.
    /// </summary>
    public static CultureInfo Culture { get; } = ResolveCulture();

    private static CultureInfo ResolveCulture()
    {
        try
        {
            var name = Get("CultureName");

            // Get returns "[CultureName]" for a missing key rather than throwing, so a bracketed
            // value means the resource is absent — not that the culture is unknown.
            if (!name.StartsWith('['))
            {
                return CultureInfo.GetCultureInfo(name);
            }
        }
        catch (CultureNotFoundException)
        {
            // A tag that is not a culture is a content bug in the resw, not a reason to fail.
        }

        return CultureInfo.CurrentCulture;
    }

    public static string Get(string key)
    {
        // A resw name like "StudioExport.Content" is stored in the PRI as a
        // subtree "StudioExport" containing "Content", and the loader addresses
        // subtrees with a slash. Passing the dotted form through unchanged finds
        // nothing.
        var path = key.Replace('.', '/');

        try
        {
            return Loader.GetString(path);
        }
        catch (Exception)
        {
            // GetString throws for a missing resource rather than returning an
            // empty string. Left uncaught, one forgotten key takes down the page
            // that reads it; shown as the key, the gap is visible in testing
            // instead of at a customer.
            return $"[{key}]";
        }
    }

    /// <summary>
    /// An exception in one line, never empty.
    ///
    /// Some exceptions carry no message at all, and "Could not save the file:"
    /// followed by nothing reads as the app having lost its own error. The type
    /// name is a poor explanation but it is a searchable one.
    /// </summary>
    public static string Reason(Exception ex) =>
        string.IsNullOrWhiteSpace(ex.Message) ? ex.GetType().Name : ex.Message;

    public static string Format(string key, params object[] args)
    {
        var format = Get(key);

        try
        {
            return string.Format(format, args);
        }
        catch (FormatException)
        {
            // A translation whose placeholders do not match the arguments is a
            // content bug, not a reason to fail the operation that was reporting
            // its result.
            return format;
        }
    }
}
