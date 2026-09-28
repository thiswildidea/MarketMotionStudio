using Windows.Storage;

namespace MarketMotionStudio;

/// <summary>
/// A set of pictures the user has chosen, kept as copies in this app's own folder.
///
/// Two of these exist, one for the picture behind the window and one for the
/// picture behind the animation frames, and each keeps its own copies and its own
/// recent list. That is deliberate: one shared pool would mean the six most recent
/// frame backdrops quietly deleting the window's picture, and a single "forget"
/// taking a picture away from a place it was still being used.
///
/// Images are copied in rather than referenced where they were picked. A path into
/// someone's Pictures folder breaks the day the file is moved or deleted, and a
/// picture that silently vanishes looks like a setting that did not stick.
/// </summary>
/// <param name="settingKey">
/// Prefix for this set's two setting values. The window's is <c>Background</c>, giving
/// the keys the app has always used.
/// </param>
/// <param name="folderName">Where this set's copies live, under the app's local folder.</param>
public sealed class PictureLibrary(string settingKey, string folderName)
{
    /// <summary>How many earlier pictures are kept for switching back to.</summary>
    public const int RecentLimit = 6;

    public static readonly string[] FileTypes = [".jpg", ".jpeg", ".png", ".bmp"];

    /// <summary>A setting value naming a system picture, relative to <see cref="SystemFolder"/>.</summary>
    private const string SystemPrefix = "system:";

    /// <summary>
    /// Raised when the picture in use, or the set of kept pictures, changed.
    /// </summary>
    public event EventHandler? Changed;

    private static ApplicationDataContainer Settings => ApplicationData.Current.LocalSettings;

    /// <summary>
    /// Where copies are kept. From ApplicationData rather than a path built on
    /// %LOCALAPPDATA%: MSIX redirects writes under the latter, and a path this
    /// process holds would not be the one the files are actually in.
    /// </summary>
    public string Folder => Path.Combine(ApplicationData.Current.LocalFolder.Path, folderName);

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
    public string? Current
    {
        get
        {
            if (Settings.Values[settingKey + "Image"] is not string value || value.Length == 0)
            {
                return null;
            }

            var system = value.StartsWith(SystemPrefix, StringComparison.Ordinal);

            // Resolved and checked to still be inside the folder, so a value
            // edited to "system:..\..\somewhere" names nothing.
            var path = system
                ? Path.GetFullPath(Path.Combine(SystemFolder, value[SystemPrefix.Length..]))
                : Path.Combine(Folder, value);

            var home = system ? SystemFolder : Folder;

            return Inside(home, path) && File.Exists(path) ? path : null;
        }
    }

    private static bool Inside(string folder, string path)
    {
        var root = Path.GetFullPath(folder).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        return Path.GetFullPath(path).StartsWith(root, StringComparison.OrdinalIgnoreCase);
    }

    /// <summary>Earlier pictures, most recent first, full paths, only those still on disk.</summary>
    public IReadOnlyList<string> Recent =>
    [
        .. RecentNames()
            .Select(name => Path.Combine(Folder, name))
            .Where(File.Exists),
    ];

    /// <summary>
    /// Copies a picked file in and makes it the picture in use.
    ///
    /// A new name every time, never the original's: two pictures called
    /// IMG_0001.jpg from two phones are different pictures, and a copy named
    /// after its source would overwrite one with the other.
    /// </summary>
    public async Task UseNewAsync(StorageFile picked)
    {
        Directory.CreateDirectory(Folder);

        var extension = Path.GetExtension(picked.Name).ToLowerInvariant();
        var name = $"{Guid.NewGuid():N}{(FileTypes.Contains(extension) ? extension : ".img")}";

        var folder = await StorageFolder.GetFolderFromPathAsync(Folder);
        await picked.CopyAsync(folder, name, NameCollisionOption.ReplaceExisting);

        Use(Path.Combine(Folder, name));
    }

    /// <summary>
    /// Makes a kept picture, or one of Windows' own, the one in use.
    ///
    /// Only kept copies go on the recent list. Windows' pictures are always
    /// offered anyway, and putting them there would push the user's own
    /// pictures off it.
    /// </summary>
    public void Use(string path)
    {
        if (IsSystemPicture(path))
        {
            Settings.Values[settingKey + "Image"] = SystemPrefix + Path.GetRelativePath(SystemFolder, path);
            Announce();
            return;
        }

        var name = Path.GetFileName(path);

        Settings.Values[settingKey + "Image"] = name;
        Settings.Values[settingKey + "Recent"] =
            string.Join('|', new[] { name }.Concat(RecentNames().Where(n => n != name)));

        Prune();
        Announce();
    }

    /// <summary>
    /// Stops using a picture. The file stays among the recent ones, so taking
    /// it off is not the same as losing it.
    /// </summary>
    public void Clear()
    {
        Settings.Values[settingKey + "Image"] = string.Empty;
        Announce();
    }

    /// <summary>
    /// Forgets one of the kept pictures and deletes its copy. The picture in
    /// use can be forgotten too; the set then has none.
    /// </summary>
    public void Forget(string path)
    {
        // Windows' pictures are not the app's to delete.
        if (IsSystemPicture(path))
        {
            return;
        }

        var name = Path.GetFileName(path);

        Settings.Values[settingKey + "Recent"] = string.Join('|', RecentNames().Where(n => n != name));

        if (Settings.Values[settingKey + "Image"] as string == name)
        {
            Settings.Values[settingKey + "Image"] = string.Empty;
        }

        TryDelete(Path.Combine(Folder, name));
        Announce();
    }

    private IEnumerable<string> RecentNames() =>
        (Settings.Values[settingKey + "Recent"] as string ?? string.Empty)
            .Split('|', StringSplitOptions.RemoveEmptyEntries);

    /// <summary>
    /// Keeps the list and the folder the same size. Anything past the limit,
    /// and any file in the folder the list no longer names, is deleted: the
    /// copies are this app's, and a folder that only ever grows is a slow leak
    /// of someone's disk.
    /// </summary>
    private void Prune()
    {
        var keep = RecentNames().Take(RecentLimit).ToList();
        Settings.Values[settingKey + "Recent"] = string.Join('|', keep);

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

    private void Announce() => Changed?.Invoke(this, EventArgs.Empty);
}
