using Windows.ApplicationModel;
using Windows.Storage;

namespace MarketMotionStudio;

/// <summary>Why asking to start with Windows did not take effect.</summary>
public enum StartupResult
{
    Enabled,
    Disabled,

    /// <summary>
    /// The user turned it off in Task Manager. Windows then refuses the app's
    /// requests permanently, and only Task Manager can undo it — so the app
    /// must say where to go rather than leave a switch that silently springs
    /// back.
    /// </summary>
    BlockedByUser,

    /// <summary>Turned off by policy; the user cannot change it either.</summary>
    BlockedByPolicy,
}

/// <summary>
/// The one setting that decides whether this app is reachable after its window is
/// closed: the notification-area icon.
///
/// Closing the window normally ends the app. With the tray icon present it instead
/// hides the window, because the icon is the only way back — otherwise the app
/// would still be running with no way to reach it, which looks like a bug. The two
/// are tied together on purpose: turning the icon off also turns off close-to-tray,
/// so the window keeps meaning what it usually means.
/// </summary>
public static class AppBehaviourSettings
{
    private const string TrayIconKey = "ShowTrayIcon";

    /// <summary>Whether the notification-area icon is shown. On by default.</summary>
    public static bool ShowTrayIcon
    {
        get => ApplicationData.Current.LocalSettings.Values[TrayIconKey] as bool? ?? true;
        set => ApplicationData.Current.LocalSettings.Values[TrayIconKey] = value;
    }

    /// <summary>
    /// Whether closing the window hides it rather than ending the app. False when
    /// there is no tray icon, because then there would be nothing to bring it back.
    /// </summary>
    public static bool CloseHidesToTray => ShowTrayIcon;

    /// <summary>Must match the TaskId in the manifest.</summary>
    private const string StartupTaskId = "MarketMotionStudioStartup";

    public static async Task<StartupResult> ReadStartupAsync()
    {
        try
        {
            var task = await StartupTask.GetAsync(StartupTaskId);
            return Describe(task.State);
        }
        catch (Exception ex)
        {
            // An unregistered task on an unpackaged or half-deployed build is not
            // something the user can act on; reporting "off" is honest enough and
            // leaves the switch usable. The reason goes to the log because a
            // silent fallback here looks identical to a manifest that was never
            // read, and the two need different fixes.
            Diagnostics.CrashLog.Note($"startup: read failed: {ex.GetType().Name} {ex.Message}");
            return StartupResult.Disabled;
        }
    }

    public static async Task<StartupResult> SetStartupAsync(bool enabled)
    {
        try
        {
            var task = await StartupTask.GetAsync(StartupTaskId);

            if (!enabled)
            {
                task.Disable();
                return StartupResult.Disabled;
            }

            // Returns the resulting state rather than throwing when Windows
            // refuses, so the answer has to be read rather than assumed from
            // the call having returned.
            var result = Describe(await task.RequestEnableAsync());
            Diagnostics.CrashLog.Note($"startup: request enable -> {result}");
            return result;
        }
        catch (Exception ex)
        {
            Diagnostics.CrashLog.Note($"startup: enable failed: {ex.GetType().Name} {ex.Message}");
            return StartupResult.Disabled;
        }
    }

    private static StartupResult Describe(StartupTaskState state) => state switch
    {
        StartupTaskState.Enabled or StartupTaskState.EnabledByPolicy => StartupResult.Enabled,
        StartupTaskState.DisabledByUser => StartupResult.BlockedByUser,
        StartupTaskState.DisabledByPolicy => StartupResult.BlockedByPolicy,
        _ => StartupResult.Disabled,
    };
}
