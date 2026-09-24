using Windows.Storage;
using Windows.Storage.AccessCache;
using Windows.Storage.Pickers;

namespace AShareMotionStudio;

/// <summary>
/// Where exported videos go.
///
/// This is the one piece of storage in the app that has to be thought about,
/// because the obvious implementation is wrong in a way that does not announce
/// itself. **MSIX silently redirects <c>%LOCALAPPDATA%</c> writes** into the
/// package container while the path string the app is holding still points at
/// the original location — so a default of "Desktop\A股成交额视频", which is how
/// the browser-based tools this replaces did it, produces a file the app reports
/// having written at a path where the user cannot find it.
///
/// A folder the user picked is not redirected. So the folder is chosen through a
/// picker and remembered as a **token** in the future-access list rather than as
/// a path: a path string re-opened later is subject to the same redirection and
/// to the folder having moved, where the token is the grant itself.
///
/// Nothing is chosen up front. The first export asks, through a save picker, and
/// remembers the folder it landed in; every export after that writes there
/// without asking, which is the behaviour the reference tools bought with a
/// browser download preference. Reading the Videos library instead would mean
/// declaring the <c>videosLibrary</c> capability to save one question.
/// </summary>
public static class OutputFolder
{
    private const string TokenKey = "OutputFolderToken";

    /// <summary>The remembered display path, or null when none has been chosen.</summary>
    public static string? RememberedPath =>
        ApplicationData.Current.LocalSettings.Values["OutputFolderPath"] as string;

    /// <summary>
    /// The remembered folder, or null when there is none or the grant no longer
    /// resolves.
    ///
    /// A token can fail: the folder was deleted, or it was on a drive that is not
    /// mounted now. That is not an error to report on its own — the caller falls
    /// back to asking — so it comes back as an absence rather than as an
    /// exception.
    /// </summary>
    public static async Task<StorageFolder?> TryGetAsync()
    {
        if (ApplicationData.Current.LocalSettings.Values[TokenKey] is not string token || token.Length == 0)
        {
            return null;
        }

        try
        {
            return await StorageApplicationPermissions.FutureAccessList.GetFolderAsync(token);
        }
        catch (Exception)
        {
            // The grant is gone or the folder is not there. Forget it rather than
            // leaving a token that will fail again on every export, and let the
            // caller ask afresh.
            Forget();
            return null;
        }
    }

    /// <summary>
    /// Records a folder as the place exports go from now on.
    ///
    /// The path is stored alongside the token purely so Settings has something to
    /// show. It is never used to open the folder — see the note on this class
    /// about why a path is not a durable handle here.
    /// </summary>
    public static void Remember(StorageFolder folder)
    {
        var token = StorageApplicationPermissions.FutureAccessList.Add(folder);

        ApplicationData.Current.LocalSettings.Values[TokenKey] = token;
        ApplicationData.Current.LocalSettings.Values["OutputFolderPath"] = folder.Path;
    }

    public static void Forget()
    {
        if (ApplicationData.Current.LocalSettings.Values[TokenKey] is string token && token.Length > 0)
        {
            try
            {
                StorageApplicationPermissions.FutureAccessList.Remove(token);
            }
            catch (Exception)
            {
                // Removing a grant that is already gone is the state being asked
                // for, not a failure.
            }
        }

        ApplicationData.Current.LocalSettings.Values.Remove(TokenKey);
        ApplicationData.Current.LocalSettings.Values.Remove("OutputFolderPath");
    }

    /// <summary>
    /// Asks for a folder and remembers it. Returns null when the user cancelled.
    /// </summary>
    /// <remarks>
    /// A picker in a desktop app has no window of its own to be modal to, and
    /// shown without one it throws rather than appearing. The handle has to be
    /// supplied, which is why this takes a window rather than being callable from
    /// anywhere.
    /// </remarks>
    public static async Task<StorageFolder?> ChooseAsync(Microsoft.UI.Xaml.Window window)
    {
        var picker = new FolderPicker { SuggestedStartLocation = PickerLocationId.VideosLibrary };

        // Empty filter lists are rejected by the folder picker with an opaque
        // failure, which is a long-standing quirk rather than anything to do with
        // what is being picked.
        picker.FileTypeFilter.Add("*");

        WinRT.Interop.InitializeWithWindow.Initialize(
            picker, WinRT.Interop.WindowNative.GetWindowHandle(window));

        var folder = await picker.PickSingleFolderAsync();

        if (folder is not null)
        {
            Remember(folder);
        }

        return folder;
    }
}
