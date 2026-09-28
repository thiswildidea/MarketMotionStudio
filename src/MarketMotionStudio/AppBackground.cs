using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Media;
using Windows.Storage;
using Windows.UI;

namespace MarketMotionStudio;

/// <summary>
/// The optional picture behind the window, and what has to change for the
/// content in front of it to stay readable.
///
/// The app's pages are dense panels around a fixed 9:16 preview, and their
/// legibility is the point of the tool. So the picture is only ever the bottom
/// layer: a dimming layer sits on it, and every surface that carries content —
/// cards, panels, the docked navigation pane — turns opaque while a picture is
/// showing. What the picture can reach is the margins between them, the title
/// bar and the page headings. The preview surface itself draws an opaque frame
/// of its own, so it never takes the picture in.
///
/// Images are copied into the app's own folder rather than referenced where
/// they were picked. A path into someone's Pictures folder breaks the day the
/// file is moved or deleted, and a background that silently vanishes looks like
/// a setting that did not stick.
///
/// The keeping of the copies is <see cref="PictureLibrary"/>, shared with the
/// animation frame's own backdrop; what is here is the window's half — the
/// dimming, and the content surfaces.
/// </summary>
public static class AppBackground
{
    private const string DimKey = "BackgroundDim";

    /// <summary>
    /// Window pictures live under the setting keys the app has always used.
    ///
    /// Reachable to the Settings page, which builds the same kind of gallery for
    /// both sets of pictures and would otherwise need two copies of it.
    /// </summary>
    internal static PictureLibrary Library { get; } = new("Background", "Backgrounds");

    /// <summary>How many earlier pictures are kept for switching back to.</summary>
    public const int RecentLimit = PictureLibrary.RecentLimit;

    /// <summary>
    /// The dimming range, in percent. Not down to zero: a picture at full
    /// strength behind the page headings and the title bar is exactly the
    /// thing that costs legibility, and the floor is what keeps the choice a
    /// matter of taste rather than of whether the page can be read.
    /// </summary>
    public const int MinDim = 30;

    public const int MaxDim = 95;

    public const int DefaultDim = 65;

    public static string[] FileTypes => PictureLibrary.FileTypes;

    public static event EventHandler? Changed;

    static AppBackground()
    {
        // A change to the kept pictures is a change to this background; the
        // window listens to this one event for both.
        Library.Changed += (_, _) => Changed?.Invoke(null, EventArgs.Empty);
    }

    private static ApplicationDataContainer Settings => ApplicationData.Current.LocalSettings;

    /// <summary>Where copies are kept.</summary>
    public static string Folder => Library.Folder;

    /// <summary>Where Windows keeps its own wallpapers and lock-screen pictures.</summary>
    public static string SystemFolder => PictureLibrary.SystemFolder;

    /// <summary>Windows' own pictures on this machine, in folder order.</summary>
    public static IReadOnlyList<string> SystemPictures => PictureLibrary.SystemPictures;

    /// <summary>Whether a path is one of Windows' own pictures rather than a kept copy.</summary>
    public static bool IsSystemPicture(string path) => PictureLibrary.IsSystemPicture(path);

    /// <summary>The picture in use, as a full path, or null for none.</summary>
    public static string? Current => Library.Current;

    /// <summary>Earlier pictures, most recent first, full paths, only those still on disk.</summary>
    public static IReadOnlyList<string> Recent => Library.Recent;

    public static int Dim
    {
        get => Settings.Values[DimKey] is int dim ? Math.Clamp(dim, MinDim, MaxDim) : DefaultDim;
        set
        {
            Settings.Values[DimKey] = Math.Clamp(value, MinDim, MaxDim);
            Changed?.Invoke(null, EventArgs.Empty);
        }
    }

    /// <summary>Copies a picked file in and makes it the picture behind the window.</summary>
    public static Task UseNewAsync(StorageFile picked) => Library.UseNewAsync(picked);

    /// <summary>Makes a kept picture, or one of Windows' own, the one behind the window.</summary>
    public static void Use(string path) => Library.Use(path);

    /// <summary>Stops showing a picture. The file stays among the recent ones.</summary>
    public static void Clear() => Library.Clear();

    /// <summary>Forgets one of the kept pictures and deletes its copy.</summary>
    public static void Forget(string path) => Library.Forget(path);

    // ---- The surfaces ------------------------------------------------------
    //
    // App.xaml overrides four Fluent brushes by key, with brush instances of
    // its own that start at exactly the Fluent values, so nothing looks
    // different until a picture is chosen. They live in a dictionary merged
    // after Fluent's, which is what makes them the ones elements resolve to;
    // changing a brush's Color then changes every element using it at once,
    // in both themes, with nothing re-resolved or restarted. High contrast is
    // left alone: App.xaml overrides nothing there, and no picture is shown.

    private static readonly (string Key, Color Normal, Color Behind)[] Dark =
    [
        ("CardBackgroundFillColorDefaultBrush", Hex(0x0D, 0xFF, 0xFF, 0xFF), Hex(0xFF, 0x2B, 0x2B, 0x2B)),
        ("LayerFillColorDefaultBrush", Hex(0x4C, 0x3A, 0x3A, 0x3A), Hex(0xFF, 0x28, 0x28, 0x28)),
        ("NavigationViewContentBackground", Hex(0x4C, 0x3A, 0x3A, 0x3A), Hex(0x00, 0x00, 0x00, 0x00)),

        // Half the base colour, not all of it: the pane holds a few short
        // labels rather than rows to be read across, so it can let a little
        // of the dimmed picture through where a panel cannot.
        ("NavigationViewExpandedPaneBackground", Hex(0x00, 0x00, 0x00, 0x00), Hex(0x80, 0x20, 0x20, 0x20)),
    ];

    private static readonly (string Key, Color Normal, Color Behind)[] Light =
    [
        ("CardBackgroundFillColorDefaultBrush", Hex(0xB3, 0xFF, 0xFF, 0xFF), Hex(0xFF, 0xFB, 0xFB, 0xFB)),
        ("LayerFillColorDefaultBrush", Hex(0x80, 0xFF, 0xFF, 0xFF), Hex(0xFF, 0xF9, 0xF9, 0xF9)),
        ("NavigationViewContentBackground", Hex(0x80, 0xFF, 0xFF, 0xFF), Hex(0x00, 0xFF, 0xFF, 0xFF)),
        ("NavigationViewExpandedPaneBackground", Hex(0x00, 0xFF, 0xFF, 0xFF), Hex(0x80, 0xF3, 0xF3, 0xF3)),
    ];

    /// <summary>
    /// Makes the content surfaces opaque while a picture is behind them, and
    /// gives them back their translucency when there is none.
    ///
    /// The content area goes the other way — transparent, so the picture shows
    /// between the cards rather than being covered by a full-page layer.
    /// </summary>
    public static void ApplySurfaces(bool pictureShowing)
    {
        // The dictionary App.xaml merges after Fluent's, found by what it
        // holds rather than by position, so reordering App.xaml cannot point
        // this at Fluent's own brushes.
        var themes = Application.Current.Resources.MergedDictionaries
            .Where(d => d is not Microsoft.UI.Xaml.Controls.XamlControlsResources)
            .Select(d => d.ThemeDictionaries)
            .FirstOrDefault(t => t.TryGetValue("Default", out var dark)
                && dark is ResourceDictionary r && r.ContainsKey("CardBackgroundFillColorDefaultBrush"));

        if (themes is null)
        {
            return;
        }

        foreach (var (theme, table) in new[] { ("Default", Dark), ("Light", Light) })
        {
            if (!themes.TryGetValue(theme, out var found) || found is not ResourceDictionary dictionary)
            {
                continue;
            }

            foreach (var (key, normal, behind) in table)
            {
                if (dictionary.TryGetValue(key, out var value) && value is SolidColorBrush brush)
                {
                    brush.Color = pictureShowing ? behind : normal;
                }
            }
        }
    }

    private static Color Hex(byte a, byte r, byte g, byte b) => Color.FromArgb(a, r, g, b);
}
