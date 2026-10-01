using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.Windows.AppLifecycle;
using Windows.Storage;

namespace MarketMotionStudio.Pages;

public sealed partial class SettingsPage : Page
{
    /// <summary>
    /// The languages shipped with the app. The empty tag means "whatever Windows is
    /// set to", which is the default and what most users want.
    /// </summary>
    private static readonly (string Tag, string Label)[] Languages =
    [
        (string.Empty, "SettingsLanguageSystem.Content"),
        ("en-US", "English"),
        ("de", "Deutsch"),
        ("es", "Español"),
        ("fr", "Français"),
        ("it", "Italiano"),
        ("pl", "Polski"),
        ("pt-BR", "Português (Brasil)"),
        ("cs", "Čeština"),
        ("tr", "Türkçe"),
        ("ru", "Русский"),
        ("ja", "日本語"),
        ("ko", "한국어"),
        ("zh-Hans", "简体中文"),
        ("zh-Hant", "繁體中文"),
    ];

    /// <summary>
    /// Follow Windows first, because it is the default and what most people want;
    /// the other two are for overriding it.
    /// </summary>
    private static readonly (ElementTheme Theme, string Label)[] Themes =
    [
        (ElementTheme.Default, "SettingsThemeSystem"),
        (ElementTheme.Light, "SettingsThemeLight"),
        (ElementTheme.Dark, "SettingsThemeDark"),
    ];

    /// <summary>
    /// What the animation frames can be drawn on, in the order they are offered.
    ///
    /// The default first, because it is what the frames were designed with and
    /// what someone who changed it will want to come back to.
    /// </summary>
    private static readonly (BackdropKind Kind, string Key)[] FrameBackdropKinds =
    [
        (BackdropKind.Default, "SettingsFrameBackdropDefault"),
        (BackdropKind.Colour, "SettingsFrameBackdropColour"),
        (BackdropKind.Picture, "SettingsFrameBackdropPicture"),
    ];

    private bool _loading = true;

    /// <summary>
    /// Where to write when something is wrong. The same address the help document
    /// ends with; the two are reached in different moods, and someone whose export
    /// just failed is not reading a manual.
    /// </summary>
    private const string ContactAddress = "gaqo@outlook.com";

    public SettingsPage()
    {
        InitializeComponent();

        ContactLink.Content = ContactAddress;
        VersionText.Text = Strings.Format("SettingsVersion", AppVersion);

        foreach (var (tag, label) in Languages)
        {
            LanguageCombo.Items.Add(new ComboBoxItem
            {
                // The system option is translated; the language names are not,
                // because a language should be listed in its own language.
                Content = tag.Length == 0 ? Strings.Get(label) : label,
                Tag = tag,
            });
        }

        LanguageCombo.SelectedIndex = Math.Max(0, Array.FindIndex(Languages, l => l.Tag == LanguageSettings.Current));

        foreach (var (theme, label) in Themes)
        {
            ThemeCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(label), Tag = theme });
        }

        ThemeCombo.SelectedIndex = Math.Max(0, Array.FindIndex(Themes, t => t.Theme == ThemeSettings.Current));

        // Listed in the order they are offered rather than in the enum's, because the
        // order a reader meets them in is the order they are likely to want: the
        // market this app was built for first.
        foreach (var id in Markets.All)
        {
            MarketCombo.Items.Add(new ComboBoxItem { Content = Markets.Of(id).Name, Tag = id });
        }

        MarketCombo.SelectedIndex = Math.Max(0, Array.IndexOf(Markets.All, MarketSettings.Current));

        StoragePathText.Text = ApplicationData.Current.LocalFolder.Path;
        TrayToggle.IsOn = AppBehaviourSettings.ShowTrayIcon;

        DimSlider.Minimum = AppBackground.MinDim;
        DimSlider.Maximum = AppBackground.MaxDim;
        DimSlider.Value = AppBackground.Dim;

        foreach (var (kind, key) in FrameBackdropKinds)
        {
            FrameBackdropCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = kind });
        }

        FrameBackdropCombo.SelectedIndex =
            Math.Max(0, Array.FindIndex(FrameBackdropKinds, k => k.Kind == AnimationBackdrop.Kind));

        // Given their values before the handlers are live. Assigning a colour
        // picker's colour raises its change event, and a change handled here
        // would write the stored colour back over the one being restored.
        TopColour.Color = AnimationBackdrop.Top;
        BottomColour.Color = AnimationBackdrop.Bottom;
        PaintFrameGradientBase();
        PaintSwatches();

        FrameDimSlider.Minimum = AnimationBackdrop.MinDim;
        FrameDimSlider.Maximum = AnimationBackdrop.MaxDim;
        FrameDimSlider.Value = AnimationBackdrop.Dim;

        FrameStrengthSlider.Minimum = AnimationBackdrop.MinStrength;
        FrameStrengthSlider.Maximum = AnimationBackdrop.MaxStrength;
        FrameStrengthSlider.Value = AnimationBackdrop.Strength;

        _loading = false;

        SettleFrameBackdropGroups();

        _ = RefreshBackgroundUiAsync();
        _ = RefreshFramePictureUiAsync();

        // Asynchronous, and deliberately after _loading is cleared: reading the
        // startup state is a call into Windows, and the switch must end up showing
        // what Windows says rather than what was last asked for.
        _ = LoadStartupStateAsync();

        RefreshOutputFolder();
    }

    private async Task LoadStartupStateAsync()
    {
        var state = await AppBehaviourSettings.ReadStartupAsync();

        _loading = true;
        StartupToggle.IsOn = state is StartupResult.Enabled;
        _loading = false;

        ExplainStartup(state);
    }

    private async void OnStartupToggled(object sender, RoutedEventArgs e)
    {
        if (_loading)
        {
            return;
        }

        var state = await AppBehaviourSettings.SetStartupAsync(StartupToggle.IsOn);

        // Windows can refuse, and does so by returning a state rather than by
        // failing. Putting the switch back is the honest response: leaving it on
        // would claim something that is not true.
        if (StartupToggle.IsOn && state is not StartupResult.Enabled)
        {
            _loading = true;
            StartupToggle.IsOn = false;
            _loading = false;
        }

        ExplainStartup(state);
    }

    private void ExplainStartup(StartupResult state)
    {
        var message = state switch
        {
            StartupResult.BlockedByUser => Strings.Get("SettingsStartupBlockedByUser"),
            StartupResult.BlockedByPolicy => Strings.Get("SettingsStartupBlockedByPolicy"),
            _ => null,
        };

        if (message is null)
        {
            return;
        }

        Status.Severity = InfoBarSeverity.Informational;
        Status.Message = message;
        RestartButton.Visibility = Visibility.Collapsed;
        Status.IsOpen = true;
    }

    /// <summary>
    /// Says where exports go, or that nothing has been chosen and the first one will
    /// ask.
    ///
    /// The path is read from what was recorded alongside the grant rather than by
    /// resolving the grant, because this is a label and resolving it is a file-system
    /// round trip that can fail — and a Settings page that reports a folder as
    /// missing because a drive is asleep is answering a question nobody asked.
    /// </summary>
    private void RefreshOutputFolder()
    {
        var path = OutputFolder.RememberedPath;
        var chosen = path is { Length: > 0 };

        OutputPathText.Text = chosen ? path! : Strings.Get("SettingsOutputNotSet");
        ForgetOutputButton.IsEnabled = chosen;
    }

    private async void OnChooseOutput(object sender, RoutedEventArgs e)
    {
        if (App.Window is not { } window)
        {
            return;
        }

        try
        {
            if (await OutputFolder.ChooseAsync(window) is not null)
            {
                RefreshOutputFolder();
            }
        }
        catch (Exception ex)
        {
            Status.Severity = InfoBarSeverity.Error;
            Status.Message = Strings.Format("SettingsOutputFailed", Strings.Reason(ex));
            RestartButton.Visibility = Visibility.Collapsed;
            Status.IsOpen = true;
        }
    }

    private void OnForgetOutput(object sender, RoutedEventArgs e)
    {
        OutputFolder.Forget();
        RefreshOutputFolder();
    }

    private void OnThemeChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_loading || ThemeCombo.SelectedItem is not ComboBoxItem { Tag: ElementTheme theme })
        {
            return;
        }

        ThemeSettings.Current = theme;

        // Applied on the spot. A theme is re-read by elements already on screen, so
        // unlike the language there is nothing to restart for.
        App.Window?.ApplyTheme();
    }

    /// <summary>
    /// Picks a picture, copies it in and makes it the one in use. The copy is what
    /// makes it survive the original being moved; see <see cref="PictureLibrary"/>.
    ///
    /// The same route for the window's picture and the frames', which is why it
    /// takes the set rather than knowing which one it is: "choose a picture" means
    /// the same thing for both, and a second copy of this would be two places for
    /// the decode check below to be left out of one.
    /// </summary>
    /// <returns>Whether a picture was taken into use.</returns>
    private async Task<bool> PickPictureAsync(PictureLibrary library)
    {
        if (App.Window is not { } window)
        {
            return false;
        }

        var picker = new Windows.Storage.Pickers.FileOpenPicker
        {
            SuggestedStartLocation = Windows.Storage.Pickers.PickerLocationId.PicturesLibrary,
            ViewMode = Windows.Storage.Pickers.PickerViewMode.Thumbnail,
        };

        foreach (var type in PictureLibrary.FileTypes)
        {
            picker.FileTypeFilter.Add(type);
        }

        WinRT.Interop.InitializeWithWindow.Initialize(picker, WinRT.Interop.WindowNative.GetWindowHandle(window));

        if (await picker.PickSingleFileAsync() is not { } file)
        {
            return false;
        }

        try
        {
            // Decoded before it is adopted: a file that is not really a picture
            // would otherwise become the setting, show nothing, and stay on the
            // list looking like a blank thumbnail.
            await using (var stream = await file.OpenStreamForReadAsync())
            {
                await new Microsoft.UI.Xaml.Media.Imaging.BitmapImage { DecodePixelWidth = 64 }
                    .SetSourceAsync(stream.AsRandomAccessStream());
            }

            await library.UseNewAsync(file);
        }
        catch (Exception ex)
        {
            Status.Severity = InfoBarSeverity.Warning;
            Status.Message = Strings.Format("SettingsBackgroundFailed", Strings.Reason(ex));
            RestartButton.Visibility = Visibility.Collapsed;
            Status.IsOpen = true;
            return false;
        }

        return true;
    }

    private async void OnPickBackground(object sender, RoutedEventArgs e)
    {
        if (await PickPictureAsync(AppBackground.Library))
        {
            await RefreshBackgroundUiAsync();
        }
    }

    private async void OnPickFramePicture(object sender, RoutedEventArgs e)
    {
        if (await PickPictureAsync(AnimationBackdrop.Pictures))
        {
            await RefreshFramePictureUiAsync();
        }
    }

    private void OnClearBackground(object sender, RoutedEventArgs e)
    {
        AppBackground.Clear();
        SettleBackgroundControls();
    }

    private void OnClearFramePicture(object sender, RoutedEventArgs e)
    {
        AnimationBackdrop.ClearPicture();
        SettleFramePictureControls();
    }

    // ---- The frames' backdrop --------------------------------------------

    /// <summary>The kind chosen, and what that shows and hides.</summary>
    private void SettleFrameBackdropGroups()
    {
        var kind = AnimationBackdrop.Kind;

        FrameColourGroup.Visibility = kind == BackdropKind.Colour ? Visibility.Visible : Visibility.Collapsed;
        FramePictureGroup.Visibility = kind == BackdropKind.Picture ? Visibility.Visible : Visibility.Collapsed;

        SettleFramePictureControls();
    }

    private void SettleFramePictureControls()
    {
        var picture = AnimationBackdrop.Picture;

        ClearFramePictureButton.IsEnabled = picture is not null;
        FrameDimSlider.IsEnabled = picture is not null;

        if (picture is null)
        {
            FramePictureGallery.SelectedItem = null;
        }
    }

    /// <summary>
    /// The lowest layer of the preview bar: the gradient the frames use when no
    /// colour has been chosen.
    ///
    /// Painted once and left alone, because it does not depend on anything the
    /// user changes. It is under the bar's second layer so that the opacity
    /// slider has something to show through: a bar of one layer would have to
    /// answer "what is 40% of this colour" with a guess, and the answer the
    /// renderer gives is the frame's own gradient showing through it.
    /// </summary>
    private void PaintFrameGradientBase()
    {
        var gradient = new Microsoft.UI.Xaml.Media.LinearGradientBrush
        {
            StartPoint = new Windows.Foundation.Point(0.5, 0),
            EndPoint = new Windows.Foundation.Point(0.5, 1),
        };

        foreach (var (position, colour) in Palette.Background)
        {
            gradient.GradientStops.Add(
                new Microsoft.UI.Xaml.Media.GradientStop { Offset = position, Color = colour });
        }

        FrameGradientPreview.Background = gradient;
    }

    /// <summary>
    /// The two swatches, so the dropdowns show the colour they carry, and the bar
    /// under them, so the pair is visible as the gradient it will be.
    ///
    /// The bar is what makes a colour change answerable without leaving the page.
    /// It is drawn from the same two colours the frame is filled with, in the same
    /// order, at the opacity they will be drawn at, so what it shows is what the
    /// video shows rather than a second opinion about it.
    /// </summary>
    private void PaintSwatches()
    {
        TopSwatch.Fill = new Microsoft.UI.Xaml.Media.SolidColorBrush(AnimationBackdrop.Top);
        BottomSwatch.Fill = new Microsoft.UI.Xaml.Media.SolidColorBrush(AnimationBackdrop.Bottom);

        FrameGradientOverlay.Background = new Microsoft.UI.Xaml.Media.LinearGradientBrush
        {
            StartPoint = new Windows.Foundation.Point(0.5, 0),
            EndPoint = new Windows.Foundation.Point(0.5, 1),
            GradientStops =
            {
                new Microsoft.UI.Xaml.Media.GradientStop { Offset = 0, Color = AnimationBackdrop.Top },
                new Microsoft.UI.Xaml.Media.GradientStop { Offset = 1, Color = AnimationBackdrop.Bottom },
            },
        };

        FrameGradientOverlay.Opacity = AnimationBackdrop.Strength / 100.0;
    }

    private void OnFrameBackdropKindChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_loading || FrameBackdropCombo.SelectedItem is not ComboBoxItem { Tag: BackdropKind kind })
        {
            return;
        }

        AnimationBackdrop.Kind = kind;
        SettleFrameBackdropGroups();
    }

    /// <summary>
    /// Either stop of the gradient. Both pickers share the handler and are told
    /// apart by which one raised it, rather than by two handlers that would each
    /// have to be wired to the right control.
    /// </summary>
    private void OnFrameColourChanged(ColorPicker sender, ColorChangedEventArgs args)
    {
        if (_loading)
        {
            return;
        }

        if (sender == TopColour)
        {
            AnimationBackdrop.Top = args.NewColor;
        }
        else
        {
            AnimationBackdrop.Bottom = args.NewColor;
        }

        PaintSwatches();
    }

    private void OnFramePictureChosen(object sender, ItemClickEventArgs e)
    {
        if (e.ClickedItem is FrameworkElement { Tag: string path } tile)
        {
            AnimationBackdrop.UsePicture(path);
            FramePictureGallery.SelectedItem = tile;
            SettleFramePictureControls();
        }
    }

    private void OnFrameDimChanged(object sender, Microsoft.UI.Xaml.Controls.Primitives.RangeBaseValueChangedEventArgs e)
    {
        if (_loading)
        {
            return;
        }

        AnimationBackdrop.Dim = (int)Math.Round(e.NewValue);
    }

    /// <summary>How opaque the two chosen colours are.</summary>
    private void OnFrameStrengthChanged(object sender, Microsoft.UI.Xaml.Controls.Primitives.RangeBaseValueChangedEventArgs e)
    {
        if (_loading)
        {
            return;
        }

        AnimationBackdrop.Strength = (int)Math.Round(e.NewValue);
        PaintSwatches();
    }

    /// <summary>
    /// Shows the picture clicked. Only the selection moves: rebuilding thirty
    /// thumbnails to change which one is highlighted would redraw the list under
    /// the pointer. A picture of the user's own moves to the front of their list,
    /// which shows the next time the page is opened.
    /// </summary>
    private void OnBackgroundChosen(object sender, ItemClickEventArgs e)
    {
        if (e.ClickedItem is FrameworkElement { Tag: string path } tile)
        {
            AppBackground.Use(path);
            BackgroundGallery.SelectedItem = tile;
            SettleBackgroundControls();
        }
    }

    /// <summary>The controls that depend on whether a picture is showing.</summary>
    private void SettleBackgroundControls()
    {
        var current = AppBackground.Current;

        ClearBackgroundButton.IsEnabled = current is not null;
        DimSlider.IsEnabled = current is not null;

        if (current is null)
        {
            BackgroundGallery.SelectedItem = null;
        }
    }

    private void OnDimChanged(object sender, Microsoft.UI.Xaml.Controls.Primitives.RangeBaseValueChangedEventArgs e)
    {
        if (_loading)
        {
            return;
        }

        AppBackground.Dim = (int)Math.Round(e.NewValue);
    }

    /// <summary>
    /// Rebuilds the thumbnails — the user's own pictures, then Windows' — and says
    /// which one is in use by selecting it.
    ///
    /// Thumbnails come from the shell's thumbnail cache rather than from decoding
    /// each file: Windows' own pictures are 4K and 6K originals, and decoding
    /// thirty of those takes long enough to watch. Either way the file is read
    /// through a stream that is closed straight after, so a thumbnail never holds
    /// open a copy that may be taken off the list.
    /// </summary>
    /// <summary>
    /// Which refresh of each gallery is the latest. Per gallery rather than one
    /// counter for the page: the two are filled at the same time when this page
    /// opens, and a single counter would let the second one cancel the first.
    /// </summary>
    private readonly Dictionary<GridView, int> _galleryGenerations = [];

    private async Task RefreshBackgroundUiAsync()
    {
        SettleBackgroundControls();

        await RefreshGalleryAsync(
            AppBackground.Library, BackgroundGallery, BackgroundGalleryNote, RefreshBackgroundUiAsync);

        SettleBackgroundControls();
    }

    private async Task RefreshFramePictureUiAsync() =>
        await RefreshGalleryAsync(
            AnimationBackdrop.Pictures, FramePictureGallery, FramePictureGalleryNote, RefreshFramePictureUiAsync);

    /// <summary>
    /// Rebuilds one gallery's thumbnails — the user's own pictures, then Windows'
    /// — and says which one is in use by selecting it.
    ///
    /// Thumbnails come from the shell's thumbnail cache rather than from decoding
    /// each file: Windows' own pictures are 4K and 6K originals, and decoding
    /// thirty of those takes long enough to watch. Either way the file is read
    /// through a stream that is closed straight after, so a thumbnail never holds
    /// open a copy that may be taken off the list.
    /// </summary>
    /// <param name="again">How to rebuild this same gallery, for the forget item.</param>
    private async Task RefreshGalleryAsync(
        PictureLibrary library, GridView gallery, TextBlock note, Func<Task> again)
    {
        var generation = _galleryGenerations.GetValueOrDefault(gallery) + 1;
        _galleryGenerations[gallery] = generation;

        var current = library.Current;
        var recent = library.Recent;
        var system = PictureLibrary.SystemPictures;

        var tiles = new List<Image>();

        foreach (var (path, index, own) in recent.Select((p, i) => (p, i, true))
                     .Concat(system.Select((p, i) => (p, i, false))))
        {
            var tile = new Image
            {
                Source = await ThumbnailAsync(path),
                Width = 128,
                Height = 72,
                Stretch = Microsoft.UI.Xaml.Media.Stretch.UniformToFill,
                Tag = path,
            };

            Microsoft.UI.Xaml.Automation.AutomationProperties.SetName(
                tile, Strings.Format(own ? "SettingsBackgroundThumb" : "SettingsBackgroundWindowsThumb", index + 1));

            // Only the user's own pictures can be taken off. Windows' are not the
            // app's to delete, and are offered whatever happens.
            if (own)
            {
                var forget = new MenuFlyoutItem { Text = Strings.Get("SettingsBackgroundForget") };
                forget.Click += async (_, _) =>
                {
                    library.Forget(path);
                    await again();
                };

                tile.ContextFlyout = new MenuFlyout { Items = { forget } };
            }

            tiles.Add(tile);

            if (_galleryGenerations.GetValueOrDefault(gallery) != generation)
            {
                return;
            }
        }

        // Only the latest refresh fills the list. Two in flight — a click while
        // thumbnails are still decoding — would otherwise both add theirs and
        // show every picture twice.
        if (_galleryGenerations.GetValueOrDefault(gallery) != generation)
        {
            return;
        }

        gallery.Items.Clear();

        foreach (var tile in tiles)
        {
            gallery.Items.Add(tile);

            if (string.Equals(tile.Tag as string, current, StringComparison.OrdinalIgnoreCase))
            {
                gallery.SelectedItem = tile;
            }
        }

        gallery.Visibility = tiles.Count > 0 ? Visibility.Visible : Visibility.Collapsed;
        note.Visibility = gallery.Visibility;

        if (gallery.SelectedItem is { } selected)
        {
            gallery.ScrollIntoView(selected);
        }
    }

    private static async Task<Microsoft.UI.Xaml.Media.Imaging.BitmapImage> ThumbnailAsync(string path)
    {
        var bitmap = new Microsoft.UI.Xaml.Media.Imaging.BitmapImage { DecodePixelWidth = 256 };

        try
        {
            var file = await StorageFile.GetFileFromPathAsync(path);
            using var thumbnail = await file.GetThumbnailAsync(
                Windows.Storage.FileProperties.ThumbnailMode.SingleItem, 256,
                Windows.Storage.FileProperties.ThumbnailOptions.ResizeThumbnail);

            await bitmap.SetSourceAsync(thumbnail);
            return bitmap;
        }
        catch (Exception)
        {
            // No thumbnail from the shell; decode the file itself.
        }

        try
        {
            await using var stream = File.OpenRead(path);
            await bitmap.SetSourceAsync(stream.AsRandomAccessStream());
        }
        catch (Exception)
        {
            // A picture that no longer decodes is still listed, so one of the
            // user's own can be taken off; it simply shows nothing.
        }

        return bitmap;
    }

    private void OnTrayToggled(object sender, RoutedEventArgs e)
    {
        if (_loading)
        {
            return;
        }

        AppBehaviourSettings.ShowTrayIcon = TrayToggle.IsOn;
        App.Window?.ApplyTrayVisibility();
    }

    private void OnMarketChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_loading || MarketCombo.SelectedItem is not ComboBoxItem { Tag: MarketId market })
        {
            return;
        }

        MarketSettings.Current = market;

        // Stored but not applied, for the reason MarketSettings gives: the pages
        // build their lists as they are constructed and the shell keeps them alive,
        // so changing one list here would leave the rest pointing at the old market.
        Status.Severity = InfoBarSeverity.Informational;
        Status.Message = Strings.Get("SettingsMarketRestart.Text");
        RestartButton.Visibility = Visibility.Visible;
        Status.IsOpen = true;
    }

    private void OnLanguageChanged(object sender, SelectionChangedEventArgs e)
    {
        // Setting the override while the combo is being populated would rewrite the
        // stored preference with whatever happened to be selected first.
        if (_loading || LanguageCombo.SelectedItem is not ComboBoxItem { Tag: string tag })
        {
            return;
        }

        LanguageSettings.Choose(tag);

        // Stored but not applied: see LanguageSettings.Choose. Nothing on screen
        // changes yet, so the restart that changes all of it is offered rather than
        // only described.
        Status.Severity = InfoBarSeverity.Informational;
        Status.Message = Strings.Get("SettingsLanguageRestart.Text");
        RestartButton.Visibility = Visibility.Visible;
        Status.IsOpen = true;
    }

    /// <summary>
    /// The package's version, which is the one a support reply would ask for. Read
    /// from the package rather than from an assembly attribute: the package version
    /// is what the Store shows and what an update changes.
    /// </summary>
    internal static string AppVersion
    {
        get
        {
            var v = Windows.ApplicationModel.Package.Current.Id.Version;
            return $"{v.Major}.{v.Minor}.{v.Build}.{v.Revision}";
        }
    }

    /// <summary>
    /// Opens a mail draft already carrying the app and its version. Nothing else is
    /// filled in — a body pre-written by the app would be text the sender has to read
    /// and delete before writing theirs.
    /// </summary>
    private async void OnContact(object sender, RoutedEventArgs e)
    {
        var subject = Strings.Format("SettingsContactSubject", AppVersion);
        var uri = new Uri($"mailto:{ContactAddress}?subject={Uri.EscapeDataString(subject)}");

        try
        {
            await Windows.System.Launcher.LaunchUriAsync(uri);
        }
        catch (Exception ex)
        {
            // A machine with no mail client is a real machine. Saying so beats a
            // click that appears to do nothing.
            Status.Severity = InfoBarSeverity.Warning;
            Status.Message = Strings.Format("SettingsContactFailed", ContactAddress, Strings.Reason(ex));
            RestartButton.Visibility = Visibility.Collapsed;
            Status.IsOpen = true;
        }
    }

    private void OnRestartNow(object sender, RoutedEventArgs e)
    {
        // The stored choice is applied during startup, before any window exists to
        // be left behind in the previous language.
        var failure = AppInstance.Restart(string.Empty);

        // Restart only returns when it did not happen.
        Status.Severity = InfoBarSeverity.Error;
        Status.Message = Strings.Format("SettingsRestartFailed", failure);
        RestartButton.Visibility = Visibility.Collapsed;
    }
}
