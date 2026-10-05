using MarketMotionStudio.Diagnostics;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Pages;
using System.Runtime.InteropServices;
using Microsoft.UI.Dispatching;
using Microsoft.UI.Windowing;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media.Animation;

namespace MarketMotionStudio;

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

    /// <summary>
    /// The tray menu's update item. The window's own update button and this one do
    /// the same thing, so they share <see cref="InstallUpdateAsync"/>; what differs
    /// is that the tray may be the only thing on screen, and installing needs the
    /// window back — it may ask about running work, and the Store may show its own
    /// prompt.
    /// </summary>
    public System.Windows.Input.ICommand UpdateCommand { get; }

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
        UpdateCommand = new RelayCommand(UpdateFromTray);

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

        // Its name, too, and not only when work starts: an icon without one is
        // the only thing in Windows that cannot say what it is, and until now
        // the name arrived only once a job began and changed it.
        RefreshTrayTooltip();

        ApplyTheme();

        // Fires both when the user picks a theme in Settings and when Windows
        // changes its own while this app is set to follow it. The caption
        // buttons are drawn by the system and do not follow either on their own.
        Root.ActualThemeChanged += (_, _) => PaintCaptionButtons();

        // The optional picture behind the window. Applied once at startup and
        // again whenever Settings changes the picture or the dimming, so the
        // Settings page does not need to reach into this window.
        AppBackground.Changed += (_, _) => _ = ApplyBackgroundAsync();
        _ = ApplyBackgroundAsync();

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

        // Before the first navigation, so that the first page shown is the first
        // entry in the history rather than a second visit to nothing.
        WireHistory();

        // Before the first navigation: the menu is pared back to what the market can
        // supply, and the page the window opens on is read from what is left. Done the
        // other way round the shell would land on a page the market has no data for
        // and then have nowhere to put it.
        ApplyMarket();
        Nav.SelectedItem = Nav.MenuItems[0];

        // The label is a TextBlock inside the item now, so the item no longer
        // names itself; screen readers get the same word the label shows.
        Microsoft.UI.Xaml.Automation.AutomationProperties.SetName(NavSettingsItem, NavSettingsLabel.Text);

        _services.Updates.Changed += (_, _) => _dispatcher.TryEnqueue(RefreshUpdateButton);
        Nav.DisplayModeChanged += (_, _) => RefreshSettingsItem();
        Nav.PaneOpened += (_, _) => RefreshSettingsItem();
        Nav.PaneClosed += (_, _) => RefreshSettingsItem();
        RefreshSettingsItem();

        _updateCheck.Tick += async (_, _) => await CheckForUpdatesAsync();
        _updateCheck.Start();
        _ = CheckForUpdatesAsync();

        // Asked here rather than at each gate. The answer changes twice a month
        // at most — when somebody subscribes, and when the month runs out — and
        // a Store round trip between a click and the dialog that answers it would
        // be felt, while a stale answer can be corrected by the dialog itself:
        // it offers to re-read the licence to anybody whose app thinks they have
        // not paid.
        _ = _services.Subscription.RefreshAsync(WindowHandle);
    }

    /// <summary>
    /// How often to ask the Store again. The app can sit in the notification
    /// area for weeks, so asking only at startup would mean a release goes
    /// unnoticed until the next reboot; asking often would be a Store call for
    /// nothing, since releases here are weeks apart.
    /// </summary>
    private readonly DispatcherTimer _updateCheck = new() { Interval = TimeSpan.FromHours(6) };

    private nint WindowHandle => WinRT.Interop.WindowNative.GetWindowHandle(this);

    private Task CheckForUpdatesAsync() => _services.Updates.CheckAsync(WindowHandle);

    /// <summary>
    /// Shows the update button while there is something to install, counts up
    /// while it installs, and takes it away once there is nothing left —
    /// which after a real install is the next start, on the new version.
    /// </summary>
    private void RefreshUpdateButton()
    {
        var updates = _services.Updates;

        UpdateButton.Visibility = updates.Available ? Visibility.Visible : Visibility.Collapsed;
        UpdateButton.IsEnabled = !updates.Installing;

        if (!updates.Installing)
        {
            UpdateCaption.Text = Strings.Get("NavUpdate");
        }

        var tip = updates.NewVersion is { } version ? Strings.Format("NavUpdateTip", version) : null;
        ToolTipService.SetToolTip(UpdateButton, tip);
        Microsoft.UI.Xaml.Automation.AutomationProperties.SetName(UpdateButton, tip ?? string.Empty);

        RefreshTrayUpdateItem();
        RefreshSettingsItem();
    }

    /// <summary>
    /// The tray's update item: "Update to …" and pressable while the Store has
    /// one, and the installed version otherwise, greyed out — with nothing to
    /// install there is nothing for the item to do, and a pressable item that
    /// does nothing is worse than one that says it cannot.
    ///
    /// The window's button is hidden in that case instead of disabled: the
    /// navigation pane has room to spare, and a button that comes and goes is
    /// what says the Store answered. The tray menu has no such room, and an
    /// item that appeared and disappeared would make the menu jump.
    /// </summary>
    private void RefreshTrayUpdateItem()
    {
        var updates = _services.Updates;

        TrayUpdateItem.IsEnabled = updates.Available && !updates.Installing;
        TrayUpdateItem.Text = updates.Available
            ? updates.NewVersion is { } version ? Strings.Format("TrayUpdateTo", version) : Strings.Get("NavUpdate")
            : Strings.Format("TrayUpToDate", Pages.SettingsPage.AppVersion);
        TrayUpdateGlyph.Glyph = updates.Available ? "\uE896" : "\uE895";
    }

    /// <summary>Installs the update the tray item is offering.</summary>
    private async void UpdateFromTray()
    {
        var updates = _services.Updates;

        if (!updates.Available || updates.Installing)
        {
            return;
        }

        // The install asks about running work and the Store may show its own
        // prompt, both of which need a window; the tray has none of its own.
        RestoreFromTray();

        await InstallUpdateAsync();
    }

    /// <summary>
    /// What the Settings item shows when its label cannot be seen.
    ///
    /// With icons only, the grid inside the item is off-screen, and with it
    /// the update button; a dot on the icon is what says there is something
    /// there. The tooltip is what a plain string label would have given the
    /// item automatically in that mode, and a grid does not.
    /// </summary>
    private void RefreshSettingsItem()
    {
        var labelShown = Nav.DisplayMode == NavigationViewDisplayMode.Expanded && Nav.IsPaneOpen;

        NavSettingsItem.InfoBadge = _services.Updates.Available && !labelShown ? new InfoBadge() : null;
        ToolTipService.SetToolTip(NavSettingsItem, labelShown ? null : NavSettingsLabel.Text);
    }

    /// <summary>Installs the update the window's button is offering.</summary>
    private async void OnUpdate(object sender, RoutedEventArgs e) => await InstallUpdateAsync();

    /// <summary>
    /// Installs the update on offer, from either the window's button or the tray's
    /// item — both offer the same install, and both must ask the same question
    /// before it starts.
    ///
    /// Installing replaces the running app, so anything in progress is ended
    /// with it — here that is an export, which runs for minutes and is the one
    /// long job this app starts. That is worth one question before it happens,
    /// and only then: with nothing running there is nothing to lose, and the
    /// button was the request.
    /// </summary>
    private async Task InstallUpdateAsync()
    {
        var updates = _services.Updates;

        if (!updates.Available || updates.Installing)
        {
            return;
        }

        if (_services.Work.IsBusy)
        {
            var confirm = new ContentDialog
            {
                XamlRoot = Root.XamlRoot,
                Title = Strings.Get("UpdateBusyTitle"),
                Content = new TextBlock
                {
                    TextWrapping = TextWrapping.Wrap,
                    Text = Strings.Format("UpdateBusyBody", string.Join(", ", _services.Work.Running)),
                },
                PrimaryButtonText = Strings.Get("UpdateBusyGo"),
                CloseButtonText = Strings.Get("StudioCancel.Content"),
                DefaultButton = ContentDialogButton.Close,
            };

            if (await Views.Dialogs.ShowAsync(confirm) != ContentDialogResult.Primary)
            {
                return;
            }
        }

        // Both surfaces count up together: the window is the one being watched
        // while it installs, but the menu is what is open when the install was
        // started from the tray, and a menu item frozen on "Update to …" would
        // look like nothing had happened.
        var progress = new Progress<double>(fraction =>
        {
            var text = Strings.Format("NavUpdating", (int)Math.Round(Math.Clamp(fraction, 0, 1) * 100));
            UpdateCaption.Text = text;
            TrayUpdateItem.Text = text;
        });

        UpdateCaption.Text = Strings.Format("NavUpdating", 0);
        TrayUpdateItem.Text = Strings.Format("NavUpdating", 0);
        TrayUpdateItem.IsEnabled = false;

        var outcome = await updates.InstallAsync(WindowHandle, progress);

        var said = outcome switch
        {
            UpdateOutcome.Installed => null,
            UpdateOutcome.Cancelled => Strings.Get("UpdateCancelled"),
            UpdateOutcome.NeedsWiFi => Strings.Get("UpdateNeedsWiFi"),
            UpdateOutcome.LowBattery => Strings.Get("UpdateLowBattery"),
            _ => Strings.Get("UpdateFailed"),
        };

        if (said is not null)
        {
            ShowToast(said);
        }
    }

    /// <summary>
    /// Pares the menu back to the pages the chosen market can supply.
    ///
    /// A page is hidden rather than left to draw nothing, because what it would show
    /// is not a smaller answer but a different one: the turnover of an index's own
    /// constituents sits on the same axis as the turnover of a whole market and is
    /// not the figure the page is about.
    ///
    /// The market is fixed for the life of the window — changing it asks for a
    /// restart, for the reason <see cref="MarketSettings"/> gives — so this runs once
    /// rather than being wired to a change notification.
    /// </summary>
    private void ApplyMarket()
    {
        var profile = Markets.Of(MarketSettings.Current);

        // Taken out of the menu rather than hidden in it. A collapsed item is still an
        // item: keyboard navigation and the framework's own selection bookkeeping both
        // keep a place for it, and this app's first item is the one it selects at
        // startup — which would land on a page with nothing to draw. Removal is the
        // only way to be sure the page is unreachable, and nothing puts it back,
        // because the market does not change while the window is open.
        if (!profile.WholeMarketTurnover)
        {
            Nav.MenuItems.Remove(NavMarketTurnover);
        }
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
    /// Says something about an action the user just attempted, where the
    /// window's own surfaces are too far from the click to connect with it.
    ///
    /// It carries no button and takes no input: anything needing a decision
    /// belongs in a dialog, which waits, rather than in a notice that leaves
    /// after three seconds.
    /// </summary>
    public void ShowToast(string message)
    {
        ToastText.Text = message;

        // Restarted rather than queued. A second refusal while the first is
        // still showing is the same conversation, and stacking notices would
        // put the newest one where it is read last.
        _toast?.Stop();
        _toast = BuildToastAnimation();
        _toast.Begin();
    }

    private Storyboard? _toast;

    /// <summary>
    /// One storyboard for the whole life of the notice: in, hold, out. A timer
    /// between two animations would leave the hold running after the window
    /// closed or the animation was cut short.
    /// </summary>
    private Storyboard BuildToastAnimation()
    {
        const double Hidden = -96;
        const double Resting = 12;

        var slide = new DoubleAnimationUsingKeyFrames();
        var fade = new DoubleAnimationUsingKeyFrames();

        void At(DoubleAnimationUsingKeyFrames track, double seconds, double value, EasingModeExt easing)
        {
            track.KeyFrames.Add(new EasingDoubleKeyFrame
            {
                KeyTime = KeyTime.FromTimeSpan(TimeSpan.FromSeconds(seconds)),
                Value = value,
                EasingFunction = easing switch
                {
                    EasingModeExt.Out => new CubicEase { EasingMode = EasingMode.EaseOut },
                    EasingModeExt.In => new CubicEase { EasingMode = EasingMode.EaseIn },
                    _ => null,
                },
            });
        }

        At(slide, 0, Hidden, EasingModeExt.None);
        At(slide, 0.28, Resting, EasingModeExt.Out);
        At(slide, 3.28, Resting, EasingModeExt.None);
        At(slide, 3.56, Hidden, EasingModeExt.In);

        At(fade, 0, 0, EasingModeExt.None);
        At(fade, 0.28, 1, EasingModeExt.Out);
        At(fade, 3.28, 1, EasingModeExt.None);
        At(fade, 3.56, 0, EasingModeExt.In);

        Storyboard.SetTarget(slide, ToastSlide);
        Storyboard.SetTargetProperty(slide, "Y");
        Storyboard.SetTarget(fade, Toast);
        Storyboard.SetTargetProperty(fade, "Opacity");

        var board = new Storyboard();
        board.Children.Add(slide);
        board.Children.Add(fade);
        return board;
    }

    private enum EasingModeExt { None, In, Out }

    /// <summary>
    /// Applies the stored theme. Called again when the Settings page changes it;
    /// unlike the language, this needs no restart.
    /// </summary>
    public void ApplyTheme()
    {
        ThemeSettings.Apply(Root);
        PaintCaptionButtons();
    }

    /// <summary>The picture now on screen, so a dimming change does not decode it again.</summary>
    private string? _backgroundShown;

    /// <summary>
    /// Shows the chosen background picture, or none, and sets the surfaces to
    /// match.
    ///
    /// Decoded from a stream closed straight after, never from its path, so
    /// the copy on disk is not held open and can be deleted when it is taken
    /// off the list. Decoded no wider than a large screen, because a phone
    /// photo is 12 megapixels and at full size would be tens of megabytes held
    /// for as long as the app runs.
    ///
    /// Nothing in high contrast: the picture is decoration, and high contrast
    /// is a statement that decoration is in the way.
    /// </summary>
    private async Task ApplyBackgroundAsync()
    {
        var path = new Windows.UI.ViewManagement.AccessibilitySettings().HighContrast ? null : AppBackground.Current;

        if (path is not null && path != _backgroundShown)
        {
            try
            {
                var picture = new Microsoft.UI.Xaml.Media.Imaging.BitmapImage { DecodePixelWidth = 2560 };

                await using (var stream = File.OpenRead(path))
                {
                    await picture.SetSourceAsync(stream.AsRandomAccessStream());
                }

                BackgroundPicture.Source = picture;
                _backgroundShown = path;
            }
            catch (Exception ex)
            {
                CrashLog.Note($"background: picture could not be shown, {ex.GetType().Name}");
                path = null;
            }
        }

        if (path is null)
        {
            BackgroundPicture.Source = null;
            _backgroundShown = null;
        }

        var showing = path is not null;

        BackgroundPicture.Visibility = showing ? Visibility.Visible : Visibility.Collapsed;
        BackgroundDimmer.Visibility = showing ? Visibility.Visible : Visibility.Collapsed;
        BackgroundDimmer.Opacity = AppBackground.Dim / 100.0;

        AppBackground.ApplySurfaces(showing);
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
            "MarketCap" => typeof(MarketCapPage),
            "AhPremium" => typeof(AhPremiumPage),
            "ExtremeDays" => typeof(ExtremeDaysPage),
            "FxCorridor" => typeof(FxCorridorPage),
            "IndexRace" => typeof(IndexRacePage),
            "AssetRace" => typeof(AssetRacePage),
            "BondRace" => typeof(BondRacePage),
            "Drawdown" => typeof(DrawdownPage),
            "HoldOdds" => typeof(HoldOddsPage),
            "Matrix" => typeof(MonthlyMatrixPage),
            "GainCalendar" => typeof(GainCalendarPage),
            "DcaPlan" => typeof(DcaPlanPage),
            "Candle" => typeof(CandlePage),
            "Position" => typeof(PositionPage),
            "Help" => typeof(HelpPage),
            "Settings" => typeof(SettingsPage),
            _ => null,
        };

        if (page is null || ContentFrame.CurrentSourcePageType == page)
        {
            return;
        }

        // A hidden item keeps its tag, so the tag alone is not proof that the page is
        // on offer: a stale selection, a restored one, or any future caller with a tag
        // in hand would otherwise land on a page the market cannot feed.
        if (page == typeof(MarketTurnoverPage) && !Markets.WholeMarket(MarketSettings.Current))
        {
            return;
        }

        // The transition says which way the reader moved: stepping back slides the
        // page in from the left, a new visit enters as it always has.
        ContentFrame.Navigate(page, null, HistoryTransition());
        RecordVisit(tag);
    }
}
