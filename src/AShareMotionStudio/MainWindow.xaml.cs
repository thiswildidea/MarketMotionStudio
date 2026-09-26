using AShareMotionStudio.Diagnostics;
using AShareMotionStudio.Localization;
using AShareMotionStudio.Pages;
using System.Runtime.InteropServices;
using Microsoft.UI.Dispatching;
using Microsoft.UI.Windowing;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media.Animation;

namespace AShareMotionStudio;

/// <summary>
/// The shell: navigation, the window's own chrome, and the theme. Pages own
/// their own data, drawing and export.
/// </summary>
public sealed partial class MainWindow : Window
{
    private readonly AppServices _services = AppServices.Current;
    private readonly DispatcherQueue _dispatcher = DispatcherQueue.GetForCurrentThread();

    /// <summary>
    /// The tray menu's actions, as commands rather than Click handlers. Click does
    /// not reach this class from that menu: the library hosts the flyout in its own
    /// popup, and the code-behind wiring does not travel with it. Nothing fails
    /// visibly — the item highlights and dismisses as normal and simply does nothing
    /// — so the symptom looks like a broken action rather than an event never sent.
    /// </summary>
    public System.Windows.Input.ICommand ShowWindowCommand { get; }

    public System.Windows.Input.ICommand ExitCommand { get; }

    private sealed class RelayCommand(Action execute) : System.Windows.Input.ICommand
    {
        public event EventHandler? CanExecuteChanged { add { } remove { } }

        public bool CanExecute(object? parameter) => true;

        public void Execute(object? parameter) => execute();
    }

    /// <summary>
    /// Set only by the tray's Exit item. Closing the window hides it, so without a
    /// way to say "this time really close" there would be no way out of the app at
    /// all.
    /// </summary>
    private bool _exiting;

    public MainWindow()
    {
        // Assigned before InitializeComponent so the context-menu bindings have
        // something to bind to.
        ShowWindowCommand = new RelayCommand(RestoreFromTray);
        ExitCommand = new RelayCommand(ExitApp);

        InitializeComponent();

        // The window carries its own title and icon, separately from the
        // package. Left unset, WinUI names every window "WinUI Desktop" and
        // gives it the framework's own icon, which is what Alt+Tab and Task
        // View show — the package identity does not reach them.
        Title = Strings.Get("AppTitle.Text");
        TitleText.Text = Strings.Get("AppTitle.Text");
        AppWindow.SetIcon(Path.Combine(AppContext.BaseDirectory, "Assets", "AppIcon.ico"));

        ExtendsContentIntoTitleBar = true;
        SetTitleBar(AppTitleBar);

        // Before anything is shown. Moving the window after it is on screen is a
        // visible jump, and this app's fixed-aspect preview is what makes people
        // size the window in the first place.
        WindowPlacement.Restore(AppWindow);
        AppWindow.Closing += OnWindowClosing;

        // The icon is created with the window; its visibility is the stored
        // preference, applied here and again whenever Settings changes it.
        ApplyTrayVisibility();

        ApplyTheme();

        // Fires both when the user picks a theme in Settings and when Windows
        // changes its own while this app is set to follow it. The caption
        // buttons are drawn by the system and do not follow either on their own.
        Root.ActualThemeChanged += (_, _) => PaintCaptionButtons();

        // An export outlives the moment it is started and the window is often
        // behind something else while it runs. The title is the only thing a
        // window that is not on top can still say, so it says it — this is the
        // job the notification-area icon does in the tool this shell came from,
        // and it is the whole reason BackgroundWork is here rather than being
        // state each page keeps to itself.
        _services.Work.Changed += (_, _) => _dispatcher.TryEnqueue(RefreshTitle);

        // The tray tooltip is the only thing a hidden window can say, so it
        // carries what is running rather than just the app's name.
        _services.Work.Changed += (_, _) => _dispatcher.TryEnqueue(RefreshTrayTooltip);

        Nav.SelectedItem = Nav.MenuItems[0];
    }

    /// <summary>
    /// Brings the window to the front, for the second launch that was folded
    /// into this instance.
    ///
    /// Marshalled onto the window's dispatcher: the single-instance redirect
    /// raises <c>AppInstance.Activated</c> on whichever thread it arrives on,
    /// and <see cref="AppWindow"/> belongs to the UI thread. Called cross-thread
    /// it silently does nothing, which reads as a launch that failed.
    /// </summary>
    public void BringToFront() => _dispatcher.TryEnqueue(() =>
    {
        // Show alone leaves a window that was hidden while minimised still
        // minimised, and a restored window can still sit behind whatever the
        // user is looking at. Neither is distinguishable from a launch that
        // did nothing.
        AppWindow.Show();

        if (AppWindow.Presenter is OverlappedPresenter { State: OverlappedPresenterState.Minimized } presenter)
        {
            presenter.Restore();
        }

        Activate();
        SetForegroundWindow(WinRT.Interop.WindowNative.GetWindowHandle(this));
    });

    /// <summary>
    /// Says what is running, in the one place a window behind another window can
    /// still be read.
    /// </summary>
    private void RefreshTitle()
    {
        var running = _services.Work.Running;
        var name = Strings.Get("AppTitle.Text");

        var text = running.Count == 0
            ? name
            : Strings.Format("TitleBusy", string.Join(", ", running), name);

        Title = text;
        TitleText.Text = text;
    }

    /// <summary>
    /// Brings the window forward when the tray icon is clicked. Show alone leaves a
    /// window that was hidden while minimised still minimised, and a restored window
    /// can still sit behind whatever the user is looking at — neither is
    /// distinguishable from a click that did nothing.
    /// </summary>
    private void RestoreFromTray()
    {
        try
        {
            AppWindow.Show();

            if (AppWindow.Presenter is OverlappedPresenter { State: OverlappedPresenterState.Minimized } presenter)
            {
                presenter.Restore();
            }

            Activate();
            SetForegroundWindow(WinRT.Interop.WindowNative.GetWindowHandle(this));
        }
        catch (Exception ex)
        {
            // Reaching the window is the point of the icon; if it fails there is no
            // fallback worth trying, but the failure should be visible somewhere.
            CrashLog.Note($"tray: restore failed: {ex.GetType().Name} {ex.Message}");
        }
    }

    /// <summary>
    /// The only way out of the app when the window is hidden to the tray. Closing the
    /// window only hides it, so without this the process would live forever with no
    /// visible surface.
    /// </summary>
    private void ExitApp()
    {
        try
        {
            _exiting = true;
            Tray.Dispose();

            // Exit rather than Close: the window may be hidden, and ending the
            // application is what the menu item says it does. Closing the last window
            // is a longer way round to the same place that depends on the window
            // still existing.
            Application.Current.Exit();
        }
        catch (Exception ex)
        {
            CrashLog.Note($"tray: exit failed: {ex.GetType().Name} {ex.Message}");
        }
    }

    [DllImport("user32.dll")]
    private static extern bool SetForegroundWindow(IntPtr hWnd);

    /// <summary>
    /// Applies the tray-icon preference. Called from the constructor and again
    /// whenever Settings changes it, so the Settings page does not need to reach
    /// into this window.
    /// </summary>
    public void ApplyTrayVisibility()
    {
        Tray.Visibility = AppBehaviourSettings.ShowTrayIcon ? Visibility.Visible : Visibility.Collapsed;
    }

    /// <summary>
    /// Closing puts the window away instead of ending the app, so work that is still
    /// running is not killed by the gesture people use to get a window off their
    /// screen. The only way out is the tray's Exit item, which is where someone
    /// looking to quit will go once the window has vanished there once.
    /// </summary>
    private void OnWindowClosing(AppWindow sender, AppWindowClosingEventArgs args)
    {
        // Saved on every close, including the one that only hides to the tray.
        // Someone who sizes the window, closes it to the tray and later exits from
        // the tray menu never reaches the other branch, and would find their sizing
        // had never been kept.
        WindowPlacement.Save(sender);

        if (_exiting)
        {
            Tray.Dispose();
            return;
        }

        // With no tray icon there is nothing to bring the window back, so hiding it
        // would leave the app running and unreachable. Closing then means what it
        // usually means.
        if (!AppBehaviourSettings.CloseHidesToTray)
        {
            _exiting = true;
            Tray.Dispose();
            return;
        }

        args.Cancel = true;
        AppWindow.Hide();
        RefreshTrayTooltip();
    }

    /// <summary>
    /// The tooltip is the only thing a hidden window can say, so it carries what is
    /// running rather than just the app's name.
    /// </summary>
    private void RefreshTrayTooltip()
    {
        var running = _services.Work.Running;

        Tray.ToolTipText = running.Count == 0
            ? Strings.Get("AppTitle.Text")
            : Strings.Format("TrayBusy", string.Join(", ", running));
    }

    /// <summary>
    /// Applies the stored theme. Called again when the Settings page changes it;
    /// unlike the language, this needs no restart.
    /// </summary>
    public void ApplyTheme()
    {
        ThemeSettings.Apply(Root);
        PaintCaptionButtons();
    }

    /// <summary>
    /// Colours the minimise, maximise and close buttons to match.
    ///
    /// They are drawn by the system, outside the XAML tree, so extending content
    /// into the title bar leaves them on the system's theme rather than the
    /// app's. Choosing dark while Windows is light would otherwise leave three
    /// black glyphs on a dark title bar. The backgrounds stay transparent so the
    /// Mica behind them is not interrupted by three opaque squares.
    /// </summary>
    private void PaintCaptionButtons()
    {
        var bar = AppWindow.TitleBar;
        var dark = Root.ActualTheme is ElementTheme.Dark;

        var ink = dark ? Microsoft.UI.Colors.White : Microsoft.UI.Colors.Black;
        var wash = dark ? (byte)0xFF : (byte)0x00;

        bar.ButtonBackgroundColor = Microsoft.UI.Colors.Transparent;
        bar.ButtonInactiveBackgroundColor = Microsoft.UI.Colors.Transparent;

        bar.ButtonForegroundColor = ink;
        bar.ButtonHoverForegroundColor = ink;
        bar.ButtonPressedForegroundColor = ink;
        bar.ButtonInactiveForegroundColor = Microsoft.UI.Colors.Gray;

        bar.ButtonHoverBackgroundColor = Windows.UI.Color.FromArgb(0x20, wash, wash, wash);
        bar.ButtonPressedBackgroundColor = Windows.UI.Color.FromArgb(0x40, wash, wash, wash);
    }

    private void OnNavigationSelectionChanged(NavigationView sender, NavigationViewSelectionChangedEventArgs args)
    {
        if (args.SelectedItem is NavigationViewItem { Tag: string tag })
        {
            Navigate(tag);
        }
    }

    private void Navigate(string tag)
    {
        var page = tag switch
        {
            "MarketTurnover" => typeof(MarketTurnoverPage),
            "StockVolume" => typeof(StockVolumePage),
            "SectorRace" => typeof(SectorRacePage),
            "Matrix" => typeof(MonthlyMatrixPage),
            "GainCalendar" => typeof(GainCalendarPage),
            "Help" => typeof(HelpPage),
            "Settings" => typeof(SettingsPage),
            _ => null,
        };

        if (page is null || ContentFrame.CurrentSourcePageType == page)
        {
            return;
        }

        ContentFrame.Navigate(page, null, new EntranceNavigationTransitionInfo());
    }
}
