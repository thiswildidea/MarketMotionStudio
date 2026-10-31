using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using MarketMotionStudio.Views;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;
using Microsoft.Windows.AppLifecycle;
using System.Globalization;
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

    /// <summary>The fonts this machine has, once they have been asked for.</summary>
    private static IReadOnlyList<string>? _fonts;

    private bool _loading = true;

    /// <summary>True while the title colour picker is being set from the store, so its
    /// own change event is not read back as a choice.</summary>
    private bool _paintingTitle;

    /// <summary>Same guard for the subtitle's picker.</summary>
    private bool _paintingSubtitle;

    /// <summary>The subtitle colour this panel has picked, as <c>#RRGGBB</c>; empty means the
    /// treatment's own default. The stored style record is the truth — this only carries the
    /// picker's answer between its change event and the record being rebuilt.</summary>
    private string _globalSubtitleColour = string.Empty;

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
        // market this app was built for first. The crypto market, when it is offered
        // at all, is last — it is the one that is not always there, and a list whose
        // last entry comes and goes reads better than one whose third does.
        FillMarketCombo(AppServices.Current.Crypto.Answered);

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

        // Given their values before the flag is cleared, like everything else:
        // the switch raises Toggled and the box raises TextChanged on being
        // filled in, and a change handled while restoring is a write of the
        // value that was just read.
        //
        // The length is the watermark's own limit rather than a number here,
        // because a box that accepts a sentence and a mark that carries
        // twenty-four characters are two answers to one question.
        WatermarkText.MaxLength = WatermarkSettings.MaxLength;
        WatermarkToggle.IsOn = WatermarkSettings.Enabled;
        WatermarkText.Text = WatermarkSettings.Text;
        FillWatermarkFonts();
        WatermarkColour.Color = WatermarkSettings.Colour;
        WatermarkStrengthSlider.Minimum = Watermark.MinOpacity;
        WatermarkStrengthSlider.Maximum = Watermark.MaxOpacity;
        WatermarkStrengthSlider.Value = WatermarkSettings.Strength;

        // Read once, when the page opens. There is no live subscription to this
        // on purpose: nothing else changes the answer while this page is in front
        // — subscribing passes through a dialog owned by whichever page asked —
        // and every action here refreshes the card on its own afterwards.
        _ = RefreshSubscriptionAsync();
        SettleWatermarkControls();

        // The global title treatment, filled and restored before the handlers are live:
        // assigning the colour picker's colour raises its change event, and a change
        // handled here would write the stored colour back over the one being restored.
        foreach (var (skin, key) in new[]
                 {
                     (TitleSkin.Plain, "PortfolioPnlTitlePlain.Content"),
                     (TitleSkin.Gilded, "PortfolioPnlTitleGilded.Content"),
                     (TitleSkin.Engraved, "PortfolioPnlTitleEngraved.Content"),
                     (TitleSkin.Fire, "PortfolioPnlTitleFire.Content"),
                     (TitleSkin.Aurum, "PortfolioPnlTitleAurum.Content"),
                     (TitleSkin.Ink, "PortfolioPnlTitleInk.Content"),
                     (TitleSkin.Neon, "PortfolioPnlTitleNeon.Content"),
                 })
        {
            TitleSkinCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = (int)skin });
        }

        // 全局默认这一侧没有「跟随全局」：这里就是那个全局。字体与换行的第一项
        // 是「默认」——应用自己拿主意的那份；副标题的样式七选一，缺省常规。
        TitleFontCombo.Items.Add(new ComboBoxItem { Content = Strings.Get("SettingsFollowDefault.Content"), Tag = "" });

        foreach (var (family, label) in TitleSettings.Fonts[1..])
        {
            var name = $"{label}  ({family})";

            TitleFontCombo.Items.Add(new ComboBoxItem { Content = name, Tag = family });
            SubtitleFontCombo.Items.Add(new ComboBoxItem { Content = name, Tag = family });
        }

        SubtitleFontCombo.Items.Insert(
            0, new ComboBoxItem { Content = Strings.Get("SettingsFollowDefault.Content"), Tag = "" });

        foreach (var lines in new[] { 1, 2, 3 })
        {
            var item = new ComboBoxItem { Content = lines.ToString(CultureInfo.InvariantCulture), Tag = lines };

            TitleLinesCombo.Items.Add(item);
            SubtitleLinesCombo.Items.Add(new ComboBoxItem { Content = $"{lines}", Tag = lines });
        }

        TitleLinesCombo.Items.Insert(
            0, new ComboBoxItem { Content = Strings.Get("SettingsFollowDefault.Content"), Tag = -1 });
        SubtitleLinesCombo.Items.Insert(
            0, new ComboBoxItem { Content = Strings.Get("SettingsFollowDefault.Content"), Tag = -1 });

        foreach (var (skin, key) in new[]
                 {
                     (TitleSkin.Plain, "PortfolioPnlTitlePlain.Content"),
                     (TitleSkin.Gilded, "PortfolioPnlTitleGilded.Content"),
                     (TitleSkin.Engraved, "PortfolioPnlTitleEngraved.Content"),
                     (TitleSkin.Fire, "PortfolioPnlTitleFire.Content"),
                     (TitleSkin.Aurum, "PortfolioPnlTitleAurum.Content"),
                     (TitleSkin.Ink, "PortfolioPnlTitleInk.Content"),
                     (TitleSkin.Neon, "PortfolioPnlTitleNeon.Content"),
                 })
        {
            SubtitleSkinCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = (int)skin });
        }

        TitleColour.Color = TitleSettings.Colour ?? TitleSkins.Default(TitleSettings.Skin);
        PaintTitleSwatch();
        PaintSubtitleSwatch();
        PaintSubtitlePicker();
        SettleTitleControls();

        _loading = false;

        SettleFrameBackdropGroups();

        _ = RefreshBackgroundUiAsync();
        _ = RefreshFramePictureUiAsync();

        // Asynchronous, and deliberately after _loading is cleared: reading the
        // startup state is a call into Windows, and the switch must end up showing
        // what Windows says rather than what was last asked for.
        _ = LoadStartupStateAsync();

        // The market card was filled above with what the process already knew, which
        // is usually everything: the window asks whether a crypto source answers as it
        // starts. This covers the other case — Settings opened before that request came
        // back — and costs nothing when it already has; see FillMarketCombo.
        _ = OfferCryptoMarketAsync();

        RefreshOutputFolder();
    }

    /// <summary>
    /// Lists the markets on offer, given what is known about the crypto source.
    ///
    /// Called twice at most: once as the page is built, with whatever the process
    /// already knows, and once more if the source had not been heard from yet.
    /// Filling it twice rather than waiting is deliberate — the alternative is holding
    /// a page back on a foreign host, and this page has a dozen cards of which the
    /// market is one.
    /// </summary>
    private void FillMarketCombo(bool cryptoReachable)
    {
        // The crypto market is listed when a source answers **or** when it is what is
        // already chosen. The second half is not a nicety: somebody who picked it and
        // then lost the route to it would otherwise be shown a combo that does not
        // contain the value it is displaying, sitting next to a window that is drawing
        // crypto pages — the one state a settings page must never be in, since the
        // control would be claiming a market the app is not on and offering no way to
        // say which one it is.
        var offered = Markets.Offered(cryptoReachable || MarketSettings.Current is MarketId.Crypto);

        // Nothing to rebuild when the list is already the right one, which is the
        // common case: the source answered before this page was opened.
        if (MarketCombo.Items.Count == offered.Length)
        {
            return;
        }

        // Rebuilding the items raises SelectionChanged, and a change handled here would
        // write the stored market back over the very value being restored — the same
        // reason the colour pickers below have their values assigned before their
        // handlers exist.
        var live = _loading;
        _loading = true;

        MarketCombo.Items.Clear();

        foreach (var id in offered)
        {
            MarketCombo.Items.Add(new ComboBoxItem { Content = Markets.Of(id).Name, Tag = id });
        }

        // Clamped rather than left at -1. The value is always in the list by
        // construction — the crypto market is listed whenever it is the chosen one —
        // but a combo showing nothing at all would be a worse way to find out
        // otherwise than a combo showing A-shares.
        MarketCombo.SelectedIndex = Math.Max(0, Array.IndexOf(offered, MarketSettings.Current));

        _loading = live;
    }

    /// <summary>
    /// Completes the market list once a source has said whether this machine can reach
    /// it, for a reader who opens Settings before the startup probe has come back.
    ///
    /// Awaited rather than blocked on, because the answer can be a six-second wait on a
    /// foreign host. All this does is add a fourth entry to a combo box somebody may be
    /// looking at, so the wait is invisible unless the box is open at that moment.
    /// </summary>
    private async Task OfferCryptoMarketAsync() =>
        FillMarketCombo(await AppServices.Current.Crypto.ReachableAsync());

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

        Note(InfoBarSeverity.Informational, message);
    }

    /// <summary>
    /// The strip at the **top** of the page, for anything worth saying about a choice
    /// on it — and the only place that decides what the strip looks like.
    ///
    /// One route rather than seven copies of four assignments, because the button's
    /// visibility is part of the sentence and not part of any one caller: a strip that
    /// offers "restart now" under a message that has nothing to do with restarting is
    /// worse than no button at all. Every caller therefore says only *what to say* and
    /// *whether a restart would settle it*.
    /// </summary>
    /// <param name="severity">How loud the strip is.</param>
    /// <param name="message">The sentence already resolved into the current language.</param>
    /// <param name="restart">Whether this is something a restart applies.</param>
    private void Note(InfoBarSeverity severity, string message, bool restart = false)
    {
        RestartNotice.Severity = severity;
        RestartNotice.Message = message;
        RestartNotice.ActionButton.Visibility = restart ? Visibility.Visible : Visibility.Collapsed;
        RestartNotice.IsOpen = true;
    }

    /// <summary>The page's own strip, for something worth telling but not stopping anything.</summary>
    private void Note(string key)
    {
        Note(InfoBarSeverity.Warning, Strings.Get(key));
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
            Note(InfoBarSeverity.Error, Strings.Format("SettingsOutputFailed", Strings.Reason(ex)));
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
            Note(InfoBarSeverity.Warning, Strings.Format("SettingsBackgroundFailed", Strings.Reason(ex)));
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

    /// <summary>
    /// Asks again whether this machine has paid, and settles the card after it.
    ///
    /// Refreshed every time rather than once, because the licence can be granted
    /// elsewhere — the Store's own window is a different window — and this page
    /// answers from whatever the last answer was. This page does not subscribe to
    /// <see cref="StoreSubscription.Changed"/>: the refresh that follows every
    /// action here is what updates it, and a second path in would be the same
    /// decision taken twice. (Not that the event has no listeners — the watermark
    /// listens, so that frames already drawn are redrawn when the answer moves.)
    /// </summary>
    private async Task RefreshSubscriptionAsync()
    {
        if (App.Window is not { } window)
        {
            return;
        }

        try
        {
            await AppServices.Current.Subscription.RefreshAsync(
                WinRT.Interop.WindowNative.GetWindowHandle(window));
        }
        finally
        {
            // Settled whichever way the refresh went. A card left at its collapsed
            // default because a call threw is a card that vanishes for somebody
            // who has paid — and the only way to cancel goes with it, while the
            // app stays unlocked around the gap.
            SettleSubscription();
        }
    }

    /// <summary>
    /// What the card says, given what the licence said.
    ///
    /// The renewal line and Manage appear only once there is something to renew
    /// or cancel. Before that they would be an empty date and a link to a page
    /// listing nothing, and someone reading the card would be left to work out
    /// that the absence meant "not yet" rather than "broken".
    /// </summary>
    private void SettleSubscription()
    {
        var subscription = AppServices.Current.Subscription;

        SubscriptionCard.Visibility =
            subscription.Known ? Visibility.Visible : Visibility.Collapsed;

        SubscriptionState.Text = Strings.Get(subscription.Subscribed
            ? "SettingsSubscriptionActive"
            : "SettingsSubscriptionInactive");

        var renews = subscription.RenewsOn;

        SubscriptionRenews.Visibility = renews is null ? Visibility.Collapsed : Visibility.Visible;
        SubscriptionRenews.Text = renews is { } when ? Strings.Format("SettingsSubscriptionRenews", Day(when)) : string.Empty;

        SubscriptionPrice.Text = subscription.Price is { Length: > 0 } price
            ? Strings.Format("SettingsSubscriptionPrice", price)
            : string.Empty;

        SubscribeButton.IsEnabled = !subscription.Busy && !subscription.Subscribed;
        RestoreButton.IsEnabled = !subscription.Busy;
        ManageButton.Visibility = subscription.Subscribed ? Visibility.Visible : Visibility.Collapsed;

        // One of the two things this unlocks is answered elsewhere in this card,
        // and by the renderer rather than by the switch: what the switch has to
        // say about it changes with every answer here.
        SettleWatermarkControls();
    }

    /// <summary>
    /// The day itself, in the reader's own order rather than the ISO one every
    /// frame inside a video uses: this is a sentence about a payment, not a row
    /// of data, and Windows already knows how the reader writes dates.
    /// </summary>
    private static string Day(DateTimeOffset when) => when.LocalDateTime.ToString("d", Strings.Culture);

    private async void OnSubscribe(object sender, RoutedEventArgs e)
    {
        if (App.Window is not { } window)
        {
            return;
        }

        var outcome = await AppServices.Current.Subscription.SubscribeAsync(
            WinRT.Interop.WindowNative.GetWindowHandle(window));

        ExplainSubscription(outcome);
        SettleSubscription();
    }

    private async void OnRestoreSubscription(object sender, RoutedEventArgs e)
    {
        if (App.Window is not { } window)
        {
            return;
        }

        await AppServices.Current.Subscription.RestoreAsync(
            WinRT.Interop.WindowNative.GetWindowHandle(window));

        SettleSubscription();

        // Only what the licence says now speaks; what it said before the button
        // was pressed does not. What was here before read the two together, and
        // the one case where they disagree is a real one — a subscription bought
        // in the Store's own window minutes ago, granted just after this process
        // last looked. Then the card above says subscribed and this note says
        // nothing was found, and the two sentences contradict each other while
        // each is true of the moment it describes.
        //
        // The note is for the case where nothing changes: somebody who has paid
        // and finds the app locked. The card changing under them is already the
        // answer when it changes.
        if (!AppServices.Current.Subscription.Subscribed)
        {
            Note("SettingsSubscriptionRestoreMissing");
        }
    }

    /// <summary>The page where a Store subscription is cancelled, outside this app.</summary>
    private async void OnManageSubscription(object sender, RoutedEventArgs e) =>
        await StoreSubscription.ManageAsync();

    /// <summary>
    /// Says how an attempt ended, when there is something to say.
    ///
    /// Success and dismissal are both silent: one is self-evident from the card
    /// changing under it, and one is what pressing Cancel means. Only the two
    /// failures speak — a purchase that could not even be offered, and a purchase
    /// the Store says went through without granting anything.
    ///
    /// **Which sentence answers which outcome is not decided here** — that is
    /// <see cref="SubscriptionOffer.Explanation"/>, because the same offer
    /// reached from an Export button reports the same answers and the two must
    /// not drift apart. This only decides where a sentence goes, which is this
    /// page's own strip.
    /// </summary>
    private void ExplainSubscription(SubscribeOutcome outcome)
    {
        if (SubscriptionOffer.Explanation(outcome) is { } key)
        {
            Note(key);
        }
    }

    /// <summary>
    /// Every font on this machine, into the combo, each item drawn in the font it
    /// names.
    ///
    /// Set in the font it names rather than in a sample word beside it: a list of
    /// font names all set in the page's own font is a list where choosing one
    /// tells you nothing until a frame is exported, and the frames are on another
    /// page. A name with a comma in it is shown in the default font, for the
    /// reason <see cref="Ink.Format"/> refuses such a name outright.
    /// </summary>
    private void FillWatermarkFonts()
    {
        foreach (var font in Fonts())
        {
            WatermarkFontCombo.Items.Add(new ComboBoxItem
            {
                Content = font,
                Tag = font,
                FontFamily = new Microsoft.UI.Xaml.Media.FontFamily(
                    font.Contains(',') ? Ink.Family : font),
            });
        }

        var wanted = WatermarkSettings.Family;

        WatermarkFontCombo.SelectedIndex = Math.Max(
            0, WatermarkFontCombo.Items
                .Select(item => (item as ComboBoxItem)?.Tag as string)
                .ToList()
                .FindIndex(name => string.Equals(name, wanted, StringComparison.OrdinalIgnoreCase)));
    }

    /// <summary>
    /// The fonts Windows knows about, sorted, asked once.
    ///
    /// Kept rather than re-read: the list is several hundred names and this page
    /// is opened again and again while a look is being settled on. A machine
    /// that will not say what fonts it has gets the one font the frames are
    /// drawn in, which is not an error worth stopping a settings page for.
    /// </summary>
    private static IReadOnlyList<string> Fonts()
    {
        if (_fonts is { } fonts)
        {
            return fonts;
        }

        try
        {
            // Every face on the machine rather than every family: Windows knows
            // families only through the faces that carry them. Duplicates go,
            // because the same family arrives once per face it has — Regular,
            // Bold, and so on — and a list of four hundred entries that is
            // really sixty fonts is not a list anyone can choose from.
            var set = Microsoft.Graphics.Canvas.Text.CanvasFontSet.GetSystemFontSet();

            _fonts = set.Fonts
                .Select(FamilyName)
                .Where(name => name.Length > 0)
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .OrderBy(name => name, StringComparer.CurrentCultureIgnoreCase)
                .ToArray();

            // Both numbers, because a short list has two very different causes:
            // a machine that reports few faces, and faces whose name could not be
            // read — the second is this code's to fix, the first is not.
            Diagnostics.CrashLog.Note($"watermark: {set.Fonts.Count} faces, {_fonts.Count} families");
        }
        catch (Exception ex)
        {
            Diagnostics.CrashLog.Note($"watermark: fonts could not be listed, {ex.GetType().Name}");
            _fonts = [Ink.Family];
        }

        return _fonts;
    }

    /// <summary>
    /// The name to offer for a face: the English one where it has one, and
    /// otherwise whichever name it answers with first.
    ///
    /// Asked for by locale rather than taken as "the first name it has", because
    /// a face can carry a name for every language it was published in and the
    /// order they come back in is not promised — on a Chinese machine several
    /// hundred families would otherwise be listed under whichever localisation
    /// happened to be first, and a list of names in six languages is a list
    /// nobody can search.
    /// </summary>
    private static string FamilyName(Microsoft.Graphics.Canvas.Text.CanvasFontFace face) =>
        face.FamilyNames.TryGetValue("en-US", out var english) && english.Length > 0
            ? english
            : face.FamilyNames.Values.FirstOrDefault(name => name.Length > 0) ?? string.Empty;

    /// <summary>Which font the mark is set in.</summary>
    private void OnWatermarkFontChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_loading || WatermarkFontCombo.SelectedItem is not ComboBoxItem { Tag: string font })
        {
            return;
        }

        WatermarkSettings.Family = font;
        SettleWatermarkControls();
    }

    /// <summary>Its colour.</summary>
    private void OnWatermarkColourChanged(ColorPicker sender, ColorChangedEventArgs args)
    {
        if (_loading)
        {
            return;
        }

        WatermarkSettings.Colour = args.NewColor;
        SettleWatermarkControls();
    }

    /// <summary>How much of that colour is used, in percent.</summary>
    private void OnWatermarkStrengthChanged(
        object sender, Microsoft.UI.Xaml.Controls.Primitives.RangeBaseValueChangedEventArgs e)
    {
        if (_loading)
        {
            return;
        }

        WatermarkSettings.Strength = (int)Math.Round(e.NewValue);
        SettleWatermarkControls();
    }

    /// <summary>Whether the exported frames carry the mark at all.</summary>
    private void OnWatermarkToggled(object sender, RoutedEventArgs e)
    {
        if (_loading)
        {
            return;
        }

        WatermarkSettings.Enabled = WatermarkToggle.IsOn;
        SettleWatermarkControls();
    }

    /// <summary>
    /// What the mark says. Stored as it is typed rather than on a commit, so the
    /// strip below is showing the name before the box is left.
    /// </summary>
    // ---- the global title treatment --------------------------------------------

    /// <summary>Selects the stored treatment and enables the "use default colour" button
    /// only once a colour has been chosen.</summary>
    private void SettleTitleControls()
    {
        TitleSkinCombo.SelectedIndex =
            Math.Max(0, Array.FindIndex(
                TitleSkinCombo.Items.OfType<ComboBoxItem>().ToArray(),
                item => item.Tag is int tag && tag == (int)TitleSettings.Skin));

        // With no colour set the headline already uses the treatment's own default, so
        // "use the default" would be a no-op; the button is then meaningless.
        TitleColourDefault.IsEnabled = TitleSettings.Colour is not null;

        // The extensible half of the global default: a null answer selects the first item,
        // which is the "not chosen" one, and an empty number box is the same null.
        var global = TitleSettings.MainStyle;

        TitleFontCombo.SelectedIndex = Math.Max(0, IndexOfTag(TitleFontCombo, global.Font ?? ""));

        // 字号与旋转现在是滑杆 + 「默认」勾选：勾上＝没有全局值（各页用自己的默认）。
        TitleSizeDefault.IsChecked = global.Size is null;
        TitleSizeSlider.Value = global.Size ?? 62;
        TitleSizeSlider.IsEnabled = TitleSizeDefault.IsChecked is not true;

        TitleRotationDefault.IsChecked = global.Rotation is null;
        TitleRotationSlider.Value = global.Rotation ?? 0;
        TitleRotationSlider.IsEnabled = TitleRotationDefault.IsChecked is not true;

        TitleLinesCombo.SelectedIndex = Math.Max(0, IndexOfTag(TitleLinesCombo, global.MaxLines ?? -1));

        var sub = TitleSettings.SubtitleStyle;

        SubtitleSkinCombo.SelectedIndex = Math.Max(0, IndexOfTag(SubtitleSkinCombo, sub.Skin ?? 0));
        SubtitleFontCombo.SelectedIndex = Math.Max(0, IndexOfTag(SubtitleFontCombo, sub.Font ?? ""));
        SubtitleSizeDefault.IsChecked = sub.Size is null;
        SubtitleSizeSlider.Value = sub.Size ?? 40;
        SubtitleSizeSlider.IsEnabled = SubtitleSizeDefault.IsChecked is not true;
        SubtitleLinesCombo.SelectedIndex = Math.Max(0, IndexOfTag(SubtitleLinesCombo, sub.MaxLines ?? -1));
        _globalSubtitleColour = sub.Colour ?? string.Empty;

        SubtitleColourDefault.IsEnabled = _globalSubtitleColour.Length > 0;

        RefreshTitlePreviews();
    }

    /// <summary>把主/副两个预览刷成当前全局样式的合并结果。</summary>
    private void RefreshTitlePreviews()
    {
        MainTitlePreview.Chosen = new TitleStyle
        {
            Skin = (int)TitleSettings.Skin,
            Colour = TitleSettings.Colour is { } c ? $"#{c.R:X2}{c.G:X2}{c.B:X2}" : null,
            Font = TagText(TitleFontCombo),
            Size = TitleSizeDefault.IsChecked is true ? null : TitleSizeSlider.Value,
            MaxLines = TagOf(TitleLinesCombo),
            Rotation = TitleRotationDefault.IsChecked is true ? null : TitleRotationSlider.Value,
        };

        MainTitlePreview.Text = Strings.Get("PortfolioPnlTitleBadge");
        MainTitlePreview.Subtitle = false;

        SubtitlePreview.Chosen = new TitleStyle
        {
            Skin = TagOf(SubtitleSkinCombo),
            Font = TagText(SubtitleFontCombo),
            Size = SubtitleSizeDefault.IsChecked is true ? null : SubtitleSizeSlider.Value,
            MaxLines = TagOf(SubtitleLinesCombo),
            Colour = _globalSubtitleColour.Length == 0 ? null : _globalSubtitleColour,
        };

        SubtitlePreview.Text = Strings.Get("PortfolioPnlTitleBadge");
        SubtitlePreview.Subtitle = true;
    }

    private static int IndexOfTag(ComboBox combo, object? tag) =>
        combo.Items.OfType<ComboBoxItem>().ToList().FindIndex(item => Equals(item.Tag, tag));

    private static int? TagOf(ComboBox combo) =>
        combo.SelectedItem is ComboBoxItem { Tag: int tag } && tag >= 0 ? tag : null;

    private static string? TagText(ComboBox combo) =>
        combo.SelectedItem is ComboBoxItem { Tag: string family } && family.Length > 0 ? family : null;

    /// <summary>The global subtitle default, rebuilt from the panel and stored whole — the
    /// style record is the storage format, so writing it field by field would mean four keys
    /// and four chances to disagree.</summary>
    private void SaveSubtitleStyle()
    {
        if (_loading)
        {
            return;
        }

        TitleSettings.SubtitleStyle = new TitleStyle
        {
            Skin = TagOf(SubtitleSkinCombo),
            Font = TagText(SubtitleFontCombo),
            Size = SubtitleSizeDefault.IsChecked is true ? null : SubtitleSizeSlider.Value,
            MaxLines = TagOf(SubtitleLinesCombo),
            Colour = _globalSubtitleColour.Length == 0 ? null : _globalSubtitleColour,
        };

        SubtitleColourDefault.IsEnabled = _globalSubtitleColour.Length > 0;
        PaintSubtitleSwatch();
        RefreshTitlePreviews();
    }

    private void OnTitleFontChanged(object sender, SelectionChangedEventArgs e)
    {
        if (!_loading)
        {
            TitleSettings.Font = TagText(TitleFontCombo);
            RefreshTitlePreviews();
        }
    }

    private void OnTitleSizeChanged(object sender, RangeBaseValueChangedEventArgs e)
    {
        if (_loading)
        {
            return;
        }

        TitleSettings.Size = TitleSizeDefault.IsChecked is true ? null : TitleSizeSlider.Value;
        RefreshTitlePreviews();
    }

    private void OnTitleSizeDefaultChanged(object sender, RoutedEventArgs e)
    {
        TitleSizeSlider.IsEnabled = TitleSizeDefault.IsChecked is not true;

        if (_loading)
        {
            return;
        }

        TitleSettings.Size = TitleSizeDefault.IsChecked is true ? null : TitleSizeSlider.Value;
        RefreshTitlePreviews();
    }

    private void OnTitleRotationChanged(object sender, RangeBaseValueChangedEventArgs e)
    {
        if (_loading)
        {
            return;
        }

        TitleSettings.Rotation = TitleRotationDefault.IsChecked is true ? null : TitleRotationSlider.Value;
        RefreshTitlePreviews();
    }

    private void OnTitleRotationDefaultChanged(object sender, RoutedEventArgs e)
    {
        TitleRotationSlider.IsEnabled = TitleRotationDefault.IsChecked is not true;

        if (_loading)
        {
            return;
        }

        TitleSettings.Rotation = TitleRotationDefault.IsChecked is true ? null : TitleRotationSlider.Value;
        RefreshTitlePreviews();
    }

    private void OnTitleLinesChanged(object sender, SelectionChangedEventArgs e)
    {
        // The global main-title style is assembled from the flat keys; the wrap cap rides with
        // them by being folded into the same store — read here as "the cap, or none".
        if (!_loading)
        {
            TitleSettings.MaxLines = TagOf(TitleLinesCombo);
            RefreshTitlePreviews();
        }
    }

    private void OnSubtitleSkinChanged(object sender, SelectionChangedEventArgs e) => SaveSubtitleStyle();

    private void OnSubtitleFontChanged(object sender, SelectionChangedEventArgs e) => SaveSubtitleStyle();

    private void OnSubtitleSizeChanged(object sender, RangeBaseValueChangedEventArgs e) => SaveSubtitleStyle();

    private void OnSubtitleSizeDefaultChanged(object sender, RoutedEventArgs e)
    {
        SubtitleSizeSlider.IsEnabled = SubtitleSizeDefault.IsChecked is not true;
        SaveSubtitleStyle();
    }

    private void OnSubtitleLinesChanged(object sender, SelectionChangedEventArgs e) => SaveSubtitleStyle();

    private void OnSubtitleColourChanged(ColorPicker sender, ColorChangedEventArgs args)
    {
        if (_paintingSubtitle)
        {
            return;
        }

        var ink = args.NewColor;

        _globalSubtitleColour = string.Format(
            CultureInfo.InvariantCulture, "#{0:X2}{1:X2}{2:X2}", ink.R, ink.G, ink.B);

        SaveSubtitleStyle();
    }

    private void OnSubtitleColourDefault(object sender, RoutedEventArgs e)
    {
        _globalSubtitleColour = string.Empty;

        PaintSubtitlePicker();
        SaveSubtitleStyle();
    }

    /// <summary>The subtitle's swatch shows the stored colour, or the treatment's own default.</summary>
    private void PaintSubtitleSwatch() =>
        SubtitleSwatch.Fill = new Microsoft.UI.Xaml.Media.SolidColorBrush(
            StoredSubtitleColour() ?? TitleSkins.Default(StoredSubtitleSkin()));

    /// <summary>Pushes the effective colour into the picker without raising its change event.</summary>
    private void PaintSubtitlePicker()
    {
        _paintingSubtitle = true;
        SubtitleColour.Color = StoredSubtitleColour() ?? TitleSkins.Default(StoredSubtitleSkin());
        _paintingSubtitle = false;
    }

    private Windows.UI.Color? StoredSubtitleColour() => TitleSettings.SubtitleStyle.ParsedColour();

    private static TitleSkin StoredSubtitleSkin() =>
        TitleSettings.SubtitleStyle.Skin is { } skin ? (TitleSkin)skin : TitleSkin.Plain;

    private void OnTitleSkinChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_loading || TitleSkinCombo.SelectedItem is not ComboBoxItem { Tag: int tag })
        {
            return;
        }

        TitleSettings.Skin = (TitleSkin)tag;

        PaintTitlePicker();
        PaintTitleSwatch();
        RefreshTitlePreviews();
    }

    private void OnTitleColourChanged(ColorPicker sender, ColorChangedEventArgs args)
    {
        // The picker raises this while we are setting its own colour back from the store.
        if (_paintingTitle)
        {
            return;
        }

        TitleSettings.Colour = args.NewColor;

        PaintTitleSwatch();
        RefreshTitlePreviews();
    }

    private void OnTitleColourDefault(object sender, RoutedEventArgs e)
    {
        TitleSettings.Colour = null;

        PaintTitlePicker();
        PaintTitleSwatch();
        RefreshTitlePreviews();
    }

    /// <summary>The swatch shows the chosen colour, or the treatment's own default.</summary>
    private void PaintTitleSwatch() =>
        TitleSwatch.Fill = new Microsoft.UI.Xaml.Media.SolidColorBrush(
            TitleSettings.Colour ?? TitleSkins.Default(TitleSettings.Skin));

    /// <summary>Pushes the effective colour into the picker without raising its change event.</summary>
    private void PaintTitlePicker()
    {
        _paintingTitle = true;
        TitleColour.Color = TitleSettings.Colour ?? TitleSkins.Default(TitleSettings.Skin);
        _paintingTitle = false;
    }

    private void OnWatermarkTextChanged(object sender, TextChangedEventArgs e)
    {
        if (_loading)
        {
            return;
        }

        WatermarkSettings.Text = WatermarkText.Text;
        SettleWatermarkControls();
    }

    /// <summary>
    /// What the watermark card shows, given the controls on it.
    ///
    /// The strip is given the resolved watermark rather than the typed text:
    /// blank falls back to the default name and off resolves to nothing, and
    /// both of those are the settings' answers, not this page's. An empty strip
    /// with no mark on it is the preview of a file with no mark on it, which is
    /// the thing the switch asks for and the only way to see it here.
    /// </summary>
    private void SettleWatermarkControls()
    {
        // Everything that decides what the mark looks like is dead while the mark
        // is off: a font chosen for a mark that is not drawn is a setting with no
        // answer anywhere, and the strip below is then the only thing on the page
        // that would still be drawing it.
        // Taking the mark off and turning it down are the two things the
        // subscription buys, so while there is none each control answers for
        // itself: the switch shows the frames as they will be written — marked —
        // and refuses the question, and the strength shows the ceiling for the
        // same reason. The rest follow the switch as they always did, which is
        // why the whole card reads as it does rather than only its switch.
        WatermarkToggle.IsEnabled = WatermarkSettings.Optional;

        // **Written back whichever way the subscription went, and this is not the
        // same thing as the line above.** While there is no subscription the
        // switch is locked and has to be *shown* the answer (`Enabled` is true
        // regardless at that point). Once there is one, the stored answer becomes
        // the truth — and the switch was set from the other answer when the page
        // opened, because the licence had not been read yet. Left alone it reads
        // "on" over a mark that is not drawn, and the strip below it is empty:
        // the card says the opposite of the frame, and the only way to find out
        // is to toggle it off and back on.
        //
        // `_loading` suppresses the write that would otherwise come back out of
        // this as a preference, the same way the slider below does it.
        if (WatermarkToggle.IsOn != WatermarkSettings.Enabled)
        {
            var restoring = _loading;
            _loading = true;
            WatermarkToggle.IsOn = WatermarkSettings.Enabled;
            _loading = restoring;
        }

        // Written back to the slider rather than only read from it: the value it
        // is holding was set when the page opened, and what has to be shown now
        // is what the mark is actually drawn at. `_loading` suppresses the write
        // that would otherwise come back out of this as a preference.
        var strength = WatermarkSettings.Strength;

        if (WatermarkStrengthSlider.Value != strength)
        {
            var restoring = _loading;
            _loading = true;
            WatermarkStrengthSlider.Value = strength;
            _loading = restoring;
        }

        WatermarkLockedNote.Visibility =
            WatermarkSettings.Optional ? Visibility.Collapsed : Visibility.Visible;

        var on = WatermarkToggle.IsOn;

        WatermarkText.IsEnabled = on;
        WatermarkFontCombo.IsEnabled = on;
        WatermarkColourButton.IsEnabled = on;
        WatermarkStrengthSlider.IsEnabled = on && WatermarkSettings.StrengthOptional;

        WatermarkSwatch.Fill =
            new Microsoft.UI.Xaml.Media.SolidColorBrush(WatermarkSettings.Colour);

        WatermarkSample.Watermark = WatermarkSettings.Current;
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
        //
        // Which is exactly why this has to be said **at the top of the page and loud
        // enough to see**: nothing on screen changes when the market does, so without
        // a sentence where the user is looking, picking a market looks like it did
        // nothing at all. The strip is docked above the cards for this, the language
        // and any other choosing that only takes effect on the way back up.
        Note(InfoBarSeverity.Informational, Strings.Get("SettingsMarketRestart.Text"), restart: true);
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
        Note(InfoBarSeverity.Informational, Strings.Get("SettingsLanguageRestart.Text"), restart: true);
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
            Note(InfoBarSeverity.Warning,
                 Strings.Format("SettingsContactFailed", ContactAddress, Strings.Reason(ex)));
        }
    }

    private void OnRestartNow(object sender, RoutedEventArgs e)
    {
        // The stored choice is applied during startup, before any window exists to
        // be left behind in the previous language.
        var failure = AppInstance.Restart(string.Empty);

        // Restart only returns when it did not happen. The button goes with it: it
        // is still on screen at this point, and offering the act again after it has
        // just failed would be offering the same failure.
        Note(InfoBarSeverity.Error, Strings.Format("SettingsRestartFailed", failure));
    }
}
