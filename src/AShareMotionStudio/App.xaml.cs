using AShareMotionStudio.Diagnostics;
using AShareMotionStudio.Localization;
using Microsoft.UI.Dispatching;
using Microsoft.UI.Xaml;
using Microsoft.Windows.AppLifecycle;

namespace AShareMotionStudio;

public partial class App : Application
{
    private const string InstanceKey = "AShareMotionStudio.Main";

    /// <summary>
    /// The shell window. Pages reach it for the things that belong to the window
    /// rather than to a page: the theme, and what the title bar says while work
    /// is running. A <see cref="Microsoft.UI.Xaml.Controls.ContentDialog"/> also
    /// needs the window's XamlRoot, and there is exactly one window.
    /// </summary>
    public static MainWindow? Window { get; private set; }

    public App()
    {
        InitializeComponent();
        CrashLog.Install(this);

        // Before any window or resource is created: a language override applied
        // later leaves whatever is already on screen in the previous language.
        LanguageSettings.ApplyAtStartup();
    }

    [STAThread]
    private static void Main(string[] args)
    {
        WinRT.ComWrappersSupport.InitializeComWrappers();

        // One studio at a time. Two instances would race for the encoder and
        // write into the same output folder under the same file names, and the
        // second window is never what someone re-launching the app wanted —
        // they wanted the one they already had.
        if (RedirectToPrimaryInstance())
        {
            return;
        }

        Application.Start(callbackParams =>
        {
            var queue = DispatcherQueue.GetForCurrentThread();
            SynchronizationContext.SetSynchronizationContext(new DispatcherQueueSynchronizationContext(queue));
            _ = new App();
        });
    }

    private static bool RedirectToPrimaryInstance()
    {
        var primary = AppInstance.FindOrRegisterForKey(InstanceKey);

        if (primary.IsCurrent)
        {
            // A second launch arrives here as an activation of this instance.
            // Bringing the window forward is what the person who clicked the
            // icon asked for; doing nothing looks like a launch that failed.
            primary.Activated += (_, _) => Window?.BringToFront();
            return false;
        }

        var activation = AppInstance.GetCurrent().GetActivatedEventArgs();
        primary.RedirectActivationToAsync(activation).AsTask().GetAwaiter().GetResult();
        return true;
    }

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        var shell = new MainWindow();
        Window = shell;
        shell.Activate();
    }
}
