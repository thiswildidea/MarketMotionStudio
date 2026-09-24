using Microsoft.UI.Xaml;
using Windows.Storage;

namespace AShareMotionStudio;

/// <summary>
/// The user's light/dark choice.
///
/// Unlike the language, this takes effect at once. A theme is a property of
/// elements already in the tree and is re-read when it changes, where an
/// <c>x:Uid</c> is resolved when its XAML loads and never looked at again —
/// which is why one of these settings needs a restart and the other does not.
///
/// It does not reach the preview. What the exported video looks like is fixed by
/// the render, not by the app's appearance, so the 9:16 frame keeps its own
/// palette in both themes; a preview that changed colour with the chrome would
/// be lying about the file it is going to produce.
/// </summary>
public static class ThemeSettings
{
    private const string Key = "AppTheme";

    /// <summary>
    /// The stored choice. <see cref="ElementTheme.Default"/> means follow
    /// Windows, which is also what an unset value means.
    /// </summary>
    public static ElementTheme Current
    {
        get => ApplicationData.Current.LocalSettings.Values[Key] is string saved &&
               Enum.TryParse<ElementTheme>(saved, out var theme)
            ? theme
            : ElementTheme.Default;

        set => ApplicationData.Current.LocalSettings.Values[Key] = value.ToString();
    }

    /// <summary>
    /// Applies the choice to a window's content.
    ///
    /// Set on the root element rather than on <see cref="Application"/>: the
    /// application-wide property can only be assigned before any content is
    /// created, so using it would make this a restart-only setting for no
    /// reason.
    /// </summary>
    public static void Apply(FrameworkElement root) => root.RequestedTheme = Current;
}
