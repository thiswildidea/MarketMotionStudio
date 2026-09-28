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
/// </summary>
public static class AppBackground
{
    private const string ImageKey = "BackgroundImage";
    private const string RecentKey = "BackgroundRecent";
    private const string DimKey = "BackgroundDim";

    /// <summary>How many earlier pictures are kept for switching back to.</summary>
    public const int RecentLimit = 6;

    /// <summary>
    /// The dimming range, in percent. Not down to zero: a picture at full
    /// strength behind the page headings and the title bar is exactly the
    /// thing that costs legibility, and the floor is what keeps the choice a
    /// matter of taste rather than of whether the page can be read.
    /// </summary>
    public const int MinDim = 30;

    public const int MaxDim = 95;

    public const int DefaultDim = 65;

    public static readonly string[] FileTypes = [".jpg", ".jpeg", ".png", ".bmp"];

    public static event EventHandler? Changed;

    private static ApplicationDataContainer Settings => ApplicationData.Current.LocalSettings;

    /// <summary>
    /// Where copies are kept. From ApplicationData rather than a path built on
    /// %LOCALAPPDATA%: MSIX redirects writes under the latter, and a path this
    /// process holds would not be the one the files are actually in.
    /// </summary>
    public static string Folder => Path.Combine(ApplicationData.Current.LocalFolder.Path, "Backgrounds");

    /// <summary>
    /// Where Windows keeps its own wallpapers and lock-screen pictures.
    ///
    /// Read from this machine, never shipped: they are Microsoft's pictures,
    /// and putting copies in the package would be redistributing them. So what
    /// is offered is whatever this Windows has, and a picture chosen from here
    /// is used where it lies rather than copied — the folder belongs to the
    /// system and is not something the user tidies away.
    /// </summary>
    public static string SystemFolder =>
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Windows), "Web");

    /// <summary>
    /// The folders under <see cref="SystemFolder"/> that hold whole pictures.
    /// Not <c>4K</c>, which is the same few images again at other sizes, and
    /// not <c>touchkeyboard</c>, which is keyboard skins.
    /// </summary>
    private static readonly string[] SystemSubfolders = ["Wallpaper", "Screen"];

    /// <summary>A setting value naming a system picture, relative to <see cref="SystemFolder"/>.</summary>
    private const string SystemPrefix = "system:";

    /// <summary>
    /// Windows' own pictures on this machine, in folder order. Empty when the
    /// folder is missing or unreadable, which some managed machines arrange.
    /// </summary>
    public static IReadOnlyList<string> SystemPictures
    {
        get
        {
            var found = new List<string>();

            foreach (var sub in SystemSubfolders)
            {
                var folder = Path.Combine(SystemFolder, sub);

                try
                {
                    if (Directory.Exists(folder))
                    {
                        found.AddRange(Directory
                            .EnumerateFiles(folder, "*", SearchOption.AllDirectories)
                            .Where(f => FileTypes.Contains(Path.GetExtension(f).ToLowerInvariant()))
                            .OrderBy(f => f, StringComparer.OrdinalIgnoreCase));
                    }
                }
                catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
                {
                }
            }

            return found;
        }
    }

    /// <summary>Whether a path is one of Windows' own pictures rather than a kept copy.</summary>
    public static bool IsSystemPicture(string path) => Inside(SystemFolder, path);

    /// <summary>The picture in use, as a full path, or null for none.</summary>
    public static string? Current
    {
        get
        {
            if (Settings.Values[ImageKey] is not string value || value.Length == 0)
            {
                return null;
            }

            // Resolved and checked to still be inside the folder, so a value
            // edited to "system:..\..\somewhere" names nothing.
            var path = value.StartsWith(SystemPrefix, StringComparison.Ordinal)
                ? Path.GetFullPath(Path.Combine(SystemFolder, value[SystemPrefix.Length..]))
                : Path.Combine(Folder, value);

            var home = value.StartsWith(SystemPrefix, StringComparison.Ordinal) ? SystemFolder : Folder;

            return Inside(home, path) && File.Exists(path) ? path : null;
        }
    }

    private static bool Inside(string folder, string path)
    {
        var root = Path.GetFullPath(folder).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        return Path.GetFullPath(path).StartsWith(root, StringComparison.OrdinalIgnoreCase);
    }

    /// <summary>Earlier pictures, most recent first, full paths, only those still on disk.</summary>
    public static IReadOnlyList<string> Recent =>
    [
        .. RecentNames()
            .Select(name => Path.Combine(Folder, name))
            .Where(File.Exists),
    ];

    public static int Dim
    {
        get => Settings.Values[DimKey] is int dim ? Math.Clamp(dim, MinDim, MaxDim) : DefaultDim;
        set
        {
            Settings.Values[DimKey] = Math.Clamp(value, MinDim, MaxDim);
            Changed?.Invoke(null, EventArgs.Empty);
        }
    }

    /// <summary>
    /// Copies a picked file in and makes it the background.
    ///
    /// A new name every time, never the original's: two pictures called
    /// IMG_0001.jpg from two phones are different pictures, and a copy named
    /// after its source would overwrite one with the other.
    /// </summary>
    public static async Task UseNewAsync(StorageFile picked)
    {
        Directory.CreateDirectory(Folder);

        var extension = Path.GetExtension(picked.Name).ToLowerInvariant();
        var name = $"{Guid.NewGuid():N}{(FileTypes.Contains(extension) ? extension : ".img")}";

        var folder = await StorageFolder.GetFolderFromPathAsync(Folder);
        await picked.CopyAsync(folder, name, NameCollisionOption.ReplaceExisting);

        Use(Path.Combine(Folder, name));
    }

    /// <summary>
    /// Makes a kept picture, or one of Windows' own, the background.
    ///
    /// Only kept copies go on the recent list. Windows' pictures are always
    /// offered anyway, and putting them there would push the user's own
    /// pictures off it.
    /// </summary>
    public static void Use(string path)
    {
        if (IsSystemPicture(path))
        {
            Settings.Values[ImageKey] = SystemPrefix + Path.GetRelativePath(SystemFolder, path);
            Changed?.Invoke(null, EventArgs.Empty);
            return;
        }

        var name = Path.GetFileName(path);

        Settings.Values[ImageKey] = name;
        Settings.Values[RecentKey] = string.Join('|', new[] { name }.Concat(RecentNames().Where(n => n != name)));

        Prune();
        Changed?.Invoke(null, EventArgs.Empty);
    }

    /// <summary>
    /// Stops showing a picture. The file stays among the recent ones, so taking
    /// it off is not the same as losing it.
    /// </summary>
    public static void Clear()
    {
        Settings.Values[ImageKey] = string.Empty;
        Changed?.Invoke(null, EventArgs.Empty);
    }

    /// <summary>
    /// Forgets one of the kept pictures and deletes its copy. The picture in
    /// use can be forgotten too; the window then shows none.
    /// </summary>
    public static void Forget(string path)
    {
        // Windows' pictures are not the app's to delete.
        if (IsSystemPicture(path))
        {
            return;
        }

        var name = Path.GetFileName(path);

        Settings.Values[RecentKey] = string.Join('|', RecentNames().Where(n => n != name));

        if (Settings.Values[ImageKey] as string == name)
        {
            Settings.Values[ImageKey] = string.Empty;
        }

        TryDelete(Path.Combine(Folder, name));
        Changed?.Invoke(null, EventArgs.Empty);
    }

    private static IEnumerable<string> RecentNames() =>
        (Settings.Values[RecentKey] as string ?? string.Empty)
            .Split('|', StringSplitOptions.RemoveEmptyEntries);

    /// <summary>
    /// Keeps the list and the folder the same size. Anything past the limit,
    /// and any file in the folder the list no longer names, is deleted: the
    /// copies are this app's, and a folder that only ever grows is a slow leak
    /// of someone's disk.
    /// </summary>
    private static void Prune()
    {
        var keep = RecentNames().Take(RecentLimit).ToList();
        Settings.Values[RecentKey] = string.Join('|', keep);

        if (!Directory.Exists(Folder))
        {
            return;
        }

        foreach (var file in Directory.EnumerateFiles(Folder))
        {
            if (!keep.Contains(Path.GetFileName(file)))
            {
                TryDelete(file);
            }
        }
    }

    private static void TryDelete(string path)
    {
        try
        {
            File.Delete(path);
        }
        catch (IOException)
        {
            // In use by an image still on screen; the next prune will get it.
        }
        catch (UnauthorizedAccessException)
        {
        }
    }

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
