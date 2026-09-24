using Windows.Storage;

namespace AShareMotionStudio.Localization;

/// <summary>
/// The user's language choice, and applying it at the one moment it takes
/// effect.
///
/// Uses <c>Microsoft.Windows.Globalization</c> rather than
/// <c>Windows.Globalization</c>: the latter is the UWP API and throws "No such
/// interface supported" in a Windows App SDK app, which surfaces as an opaque
/// XAML-thread crash rather than an error anyone can act on.
///
/// The choice is stored by this app as well as handed to the framework, because
/// the framework only persists it for packaged apps and the stored value is what
/// the settings page reads back.
/// </summary>
public static class LanguageSettings
{
    private const string SettingKey = "LanguageOverride";

    /// <summary>Empty means follow Windows.</summary>
    public static string Current
    {
        get => ApplicationData.Current.LocalSettings.Values[SettingKey] as string ?? string.Empty;
        private set => ApplicationData.Current.LocalSettings.Values[SettingKey] = value;
    }

    /// <summary>
    /// Applies the stored choice. Must run before any resource is read, so the
    /// framework resolves x:Uid against the right language; afterwards it has no
    /// effect on what is already on screen.
    /// </summary>
    public static void ApplyAtStartup() => Apply(Current);

    /// <summary>
    /// Records the choice without acting on it.
    ///
    /// Deliberately does not apply it. The framework resolves <c>x:Uid</c> when a
    /// piece of XAML loads and never re-reads it, so applying an override
    /// mid-session changes only what is built afterwards: pages opened later
    /// switch language while the window around them — loaded at startup — keeps
    /// the old one. That half-translated state looks like a bug, and it is a
    /// worse outcome than nothing changing until the restart that can change all
    /// of it at once.
    /// </summary>
    public static void Choose(string languageTag) => Current = languageTag;

    private static void Apply(string languageTag)
    {
        try
        {
            // "Follow Windows" has to undo the previous choice, not skip the
            // setter. The framework persists this override for a packaged app, so
            // a process does not start without one: leaving it alone goes on
            // applying the language the user just stopped asking for.
            if (languageTag.Length == 0)
            {
                ClearOverride();
                return;
            }

            Override = languageTag;
        }
        catch (Exception ex)
        {
            // An unsupported tag or a globalization failure must not stop the app
            // from starting. Falling back to the system language is a worse
            // experience than the user asked for, not a broken one.
            Diagnostics.CrashLog.Write("LanguageSettings", ex);
        }
    }

    /// <summary>
    /// Returns resource lookup to the system language.
    ///
    /// An empty value is the documented way to clear the override, and the shell
    /// this app is built on has seen it rejected outright with
    /// <c>0x80070057 The parameter is incorrect</c>. Naming the user's own
    /// language reaches the same screen, and because the stored choice stays
    /// empty it is re-read from Windows at every start, so changing the Windows
    /// language afterwards is still followed.
    /// </summary>
    private static void ClearOverride()
    {
        try
        {
            Override = string.Empty;
        }
        catch (Exception)
        {
            // Not recorded. Where this is rejected it is rejected every time, so
            // logging it would write a stack trace on every start of a known,
            // handled outcome and bury the crashes the log is for. Naming the
            // system language is the path that works; if that also fails, the
            // caller records it, because that would be news.
            if (SystemLanguage() is { Length: > 0 } system)
            {
                Override = system;
            }
        }
    }

    /// <summary>
    /// The language Windows is set to, read from the user's preference list
    /// rather than from the current culture: the culture reflects the override
    /// this is trying to get out from under.
    /// </summary>
    private static string? SystemLanguage()
    {
        try
        {
            return Windows.System.UserProfile.GlobalizationPreferences.Languages.FirstOrDefault();
        }
        catch (Exception)
        {
            return System.Globalization.CultureInfo.InstalledUICulture.Name;
        }
    }

    private static string Override
    {
        set => Microsoft.Windows.Globalization.ApplicationLanguages.PrimaryLanguageOverride = value;
    }
}
