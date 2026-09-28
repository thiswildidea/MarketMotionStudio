using System.Runtime.InteropServices;
using MarketMotionStudio.Diagnostics;
using Windows.Services.Store;

namespace MarketMotionStudio;

/// <summary>How an attempt to install a Store update ended, as far as this process saw.</summary>
public enum UpdateOutcome
{
    /// <summary>
    /// Installed. Normally never observed: installing a package replaces the
    /// running app, so the process is gone before the call returns.
    /// </summary>
    Installed,

    /// <summary>The user dismissed the Store's own prompt.</summary>
    Cancelled,

    NeedsWiFi,

    LowBattery,

    Failed,
}

/// <summary>
/// Whether the Microsoft Store holds a newer version of this app, and getting it.
///
/// Held for the app's lifetime rather than by the window: the app spends most
/// of its life in the notification area, and the question is worth asking again
/// while it sits there, not only when it starts.
///
/// Every failure to ask is treated as "no update". A build sideloaded from
/// Visual Studio, a machine with the Store disabled by policy, or no network
/// all land here, and none of them is something to put in front of the user —
/// the button exists to offer something, and when there is nothing to offer it
/// should simply not be there.
/// </summary>
public sealed class StoreUpdates
{
    private StoreContext? _context;
    private IReadOnlyList<StorePackageUpdate> _pending = [];

    /// <summary>Raised on the UI thread when availability or progress state changes.</summary>
    public event EventHandler? Changed;

    public bool Available => _pending.Count > 0 || _simulated is not null;

    public bool Installing { get; private set; }

    /// <summary>The version on offer, for the button's tooltip. Null when there is none.</summary>
    public string? NewVersion { get; private set; }

    /// <summary>
    /// The Store's context, associated with the window.
    ///
    /// A desktop app has no CoreWindow for the Store to parent its prompts to,
    /// so without this the consent dialog of the non-silent path fails instead
    /// of appearing. Done once: a context can be initialised with a window only
    /// once, and there is only one window.
    /// </summary>
    private StoreContext Context(nint window)
    {
        if (_context is null)
        {
            _context = StoreContext.GetDefault();
            WinRT.Interop.InitializeWithWindow.Initialize(_context, window);
        }

        return _context;
    }

    public async Task CheckAsync(nint window)
    {
        // A check landing mid-install would replace the list being installed
        // with whatever the Store says now, which during an install is nothing.
        if (Installing)
        {
            return;
        }

        IReadOnlyList<StorePackageUpdate> found;

        try
        {
            found = [.. await Context(window).GetAppAndOptionalStorePackageUpdatesAsync()];
        }
        catch (Exception ex)
        {
            CrashLog.Note($"store: update check failed, {ex.GetType().Name} 0x{ex.HResult:X8}");
            found = [];
        }

        _pending = found;
        NewVersion = found.Count > 0 ? found.Max(u => Comparable(u.Package.Id.Version))!.ToString() : null;

        ReadSimulation();

        Changed?.Invoke(this, EventArgs.Empty);
    }

    /// <summary>
    /// Downloads and installs what <see cref="CheckAsync"/> found.
    ///
    /// Silently where the Store allows it — only when the user has automatic
    /// app updates switched on and is not on a metered connection — and
    /// otherwise through the Store's own prompt, which is the path that asks
    /// before spending someone's data. Either way the button was the request;
    /// the prompt, where it appears, is the Store's condition, not this app's.
    ///
    /// Installing replaces the running app, so the process is ended from
    /// outside. Registering for restart first is what brings it back on the
    /// new version, and is undone if nothing was installed: the same
    /// registration also relaunches the app after a crash or a Windows reboot,
    /// which nobody asked for by pressing Update.
    /// </summary>
    /// <param name="progress">0 to 1 across download and install together.</param>
    public async Task<UpdateOutcome> InstallAsync(nint window, IProgress<double> progress)
    {
        if (!Available || Installing)
        {
            return UpdateOutcome.Failed;
        }

        Installing = true;
        Changed?.Invoke(this, EventArgs.Empty);

        var outcome = UpdateOutcome.Failed;

        try
        {
            if (_simulated is not null)
            {
                outcome = await SimulateInstallAsync(progress);
                return outcome;
            }

            RegisterApplicationRestart(null, 0);

            var context = Context(window);

            var operation = context.CanSilentlyDownloadStorePackageUpdates
                ? context.TrySilentDownloadAndInstallStorePackageUpdatesAsync(_pending)
                : context.RequestDownloadAndInstallStorePackageUpdatesAsync(_pending);

            // Raised off the UI thread; Progress<T> carries the report back to
            // the thread that created it.
            operation.Progress = (_, status) => progress.Report(status.PackageDownloadProgress);

            var result = await operation;

            outcome = result.OverallState switch
            {
                StorePackageUpdateState.Completed => UpdateOutcome.Installed,
                StorePackageUpdateState.Canceled => UpdateOutcome.Cancelled,
                StorePackageUpdateState.ErrorWiFiRequired or StorePackageUpdateState.ErrorWiFiRecommended => UpdateOutcome.NeedsWiFi,
                StorePackageUpdateState.ErrorLowBattery => UpdateOutcome.LowBattery,
                _ => UpdateOutcome.Failed,
            };

            CrashLog.Note($"store: update ended, state={result.OverallState}");
            return outcome;
        }
        catch (Exception ex)
        {
            CrashLog.Note($"store: update failed, {ex.GetType().Name} 0x{ex.HResult:X8}");
            return UpdateOutcome.Failed;
        }
        finally
        {
            if (outcome is not UpdateOutcome.Installed && _simulated is null)
            {
                UnregisterApplicationRestart();
            }

            // Gone once it is in. If the process survived an install — an
            // optional package, say — the button has nothing left to offer.
            if (outcome is UpdateOutcome.Installed)
            {
                _pending = [];
                _simulated = null;
                NewVersion = null;
            }

            Installing = false;
            Changed?.Invoke(this, EventArgs.Empty);
        }
    }

    private static Version Comparable(Windows.ApplicationModel.PackageVersion v) =>
        new(v.Major, v.Minor, v.Build, v.Revision);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)]
    private static extern int RegisterApplicationRestart(string? commandLine, int flags);

    [DllImport("kernel32.dll")]
    private static extern int UnregisterApplicationRestart();

    // ---- Debug-only simulation -------------------------------------------
    //
    // A Store update cannot be produced on a development machine: the Store
    // only offers one to a Store-installed package, and this build is
    // registered from bin. So the button could otherwise only be seen after a
    // real release. A file named below in LocalState, holding a version
    // string, makes a Debug build believe that version is on offer; pressing
    // the button runs a fake three-second install and reports success, which
    // is enough to see the button appear, count up and go away. Compiled out
    // of Release entirely.

    private string? _simulated;

#if DEBUG
    private static string SimulationFile => Path.Combine(
        Windows.Storage.ApplicationData.Current.LocalFolder.Path, "simulate-store-update.txt");
#endif

    private void ReadSimulation()
    {
#if DEBUG
        try
        {
            if (File.Exists(SimulationFile) && File.ReadAllText(SimulationFile).Trim() is { Length: > 0 } version)
            {
                _simulated = version;
                NewVersion = version;
            }
        }
        catch (IOException)
        {
        }
#endif
    }

    private async Task<UpdateOutcome> SimulateInstallAsync(IProgress<double> progress)
    {
#if DEBUG
        for (var step = 1; step <= 10; step++)
        {
            await Task.Delay(300);
            progress.Report(step / 10.0);
        }

        try
        {
            File.Delete(SimulationFile);
        }
        catch (IOException)
        {
        }

        return UpdateOutcome.Installed;
#else
        await Task.CompletedTask;
        return UpdateOutcome.Failed;
#endif
    }
}
