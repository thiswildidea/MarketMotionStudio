using AShareMotionStudio.Localization;
using AShareMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace AShareMotionStudio.Pages;

/// <summary>
/// One stock's volume against its turnover rate, as two stacked panels.
/// </summary>
public sealed partial class StockVolumePage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    /// <summary>
    /// This page's own settings. A separate prefix from the turnover page's, because the video and
    /// layout panel is one control serving both — sharing the store would mean tuning one chart's
    /// margins silently retuned the other's.
    /// </summary>
    private readonly StudioPreferences _prefs = new("Stock.");

    private static readonly (int Months, string Key)[] Ranges =
    [
        (1, "StudioRange1M"),
        (3, "StudioRange3M"),
        (6, "StudioRange6M"),
        (12, "StudioRange12M"),
        (0, "StudioRangeCustom"),
    ];

    public StockVolumePage()
    {
        InitializeComponent();

        foreach (var (months, key) in Ranges)
        {
            RangeCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = months });
        }

        RangeCombo.SelectedIndex = 1;

        var today = DateTimeOffset.Now;
        FromDate.Date = today.AddMonths(-3);
        ToDate.Date = today;

        ChosenText.Text = Strings.Get("StockNoneChosen");

        // Offered here and not on the whole-market page: this title carries the name
        // of an instrument, which is the thing a poster may want out of frame.
        VideoSettings.AllowHideTitle = true;
        VideoSettings.TitlePlaceholder = Strings.Get("StockTitlePlaceholder");

        VideoSettings.Changed += (_, _) =>
        {
            ApplyPreviewSettings();
            VideoSettings.Save(_prefs);
        };

        _stage.Subtitle = Strings.Get("StudioStageNoData");
        _stage.Credit = Strings.Get("StudioCredit");

        Preview.Renderer = _stage;

        _playback = new Playback(this);

        // After the handlers are attached, so a restored value reaches the preview the same way a
        // typed one does.
        _prefs.Restoring = true;
        VideoSettings.Restore(_prefs);
        _prefs.Restoring = false;

        ApplyPreviewSettings();
    }

    protected override InfoBar StatusControl => Status;

    protected override string JobName => Strings.Get("StockVolumePageTitle.Text");

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        // Empty falls back to a label describing the chart. Once this page can fetch, the
        // fallback becomes the chosen instrument's name; there is deliberately no field
        // holding it yet, because a field that is only ever null is dead weight the compiler
        // is right to warn about.
        var typed = VideoSettings.TitleText;
        _stage.Title = typed.Length > 0 ? typed : Strings.Get("StockVolumeStageTitle");
        _stage.ShowTitle = VideoSettings.ShowTitle;

        RefreshScrubText();
        Preview.Redraw();
    }

    /// <summary>
    /// The two modes ask different questions of the source, so they need different
    /// controls rather than the same ones meaning different things. A multi-day span
    /// is chosen freely; a single day can only be one of the few the intraday
    /// endpoint still holds.
    /// </summary>
    private void OnModeChanged(object sender, RoutedEventArgs e)
    {
        if (RangeCombo is null || TradingDayCombo is null || CustomRange is null)
        {
            return;
        }

        var daily = DailyMode.IsChecked is true;

        RangeCombo.Visibility = daily ? Visibility.Visible : Visibility.Collapsed;
        TradingDayCombo.Visibility = daily ? Visibility.Collapsed : Visibility.Visible;

        CustomRange.Visibility = daily && RangeCombo.SelectedItem is ComboBoxItem { Tag: 0 }
            ? Visibility.Visible
            : Visibility.Collapsed;
    }

    private void OnRangeChanged(object sender, SelectionChangedEventArgs e)
    {
        // Raised by the selection assignment in the constructor, before the rest of
        // the page's controls have been reached.
        if (CustomRange is null || DailyMode is null)
        {
            return;
        }

        var custom = DailyMode.IsChecked is true && RangeCombo.SelectedItem is ComboBoxItem { Tag: 0 };
        CustomRange.Visibility = custom ? Visibility.Visible : Visibility.Collapsed;
    }

    private void OnSearchTextChanged(AutoSuggestBox sender, AutoSuggestBoxTextChangedEventArgs args)
    {
        // Only a typed change asks for suggestions. Assigning the text in code —
        // which is what choosing a suggestion does — would otherwise ask the source
        // for suggestions for the name it has just settled on.
        if (args.Reason is not AutoSuggestionBoxTextChangeReason.UserInput)
        {
            return;
        }

        ShowStatus(InfoBarSeverity.Informational, Strings.Get("StudioDataLayerPending"));
    }

    private void OnSearchSubmitted(AutoSuggestBox sender, AutoSuggestBoxQuerySubmittedEventArgs args) =>
        ShowStatus(InfoBarSeverity.Informational, Strings.Get("StudioDataLayerPending"));

    private void OnScrub(object sender, RangeBaseValueChangedEventArgs e)
    {
        _playback?.Stop();

        Preview.Progress = Scrub.Value;
        RefreshScrubText();
        Preview.Redraw();
    }

    private void RefreshScrubText()
    {
        var at = VideoSettings.Duration.TotalSeconds * Preview.Progress;
        ScrubText.Text = Strings.Format("StudioScrubPosition", at.ToString("0.0"), (int)VideoSettings.Duration.TotalSeconds);
    }

    private void OnPlay(object sender, RoutedEventArgs e) => _playback.Toggle();

    void IPlaybackHost.ShowMoment(double progress)
    {
        Preview.Progress = progress;

        // The handler is detached for the assignment: it exists to stop playback
        // when a person moves the thumb, and playback moving it is not that.
        Scrub.ValueChanged -= OnScrub;
        Scrub.Value = progress;
        Scrub.ValueChanged += OnScrub;

        RefreshScrubText();
        Preview.Redraw();
    }

    void IPlaybackHost.ShowPlaybackState(bool playing) =>
        PlayButton.Content = Strings.Get(playing ? "StudioPause.Content" : "StudioPlay.Content");

    TimeSpan IPlaybackHost.PlaybackDuration => VideoSettings.Duration;

    private void OnFetch(object sender, RoutedEventArgs e) =>
        ShowStatus(InfoBarSeverity.Informational, Strings.Get("StudioDataLayerPending"));

    private void OnExport(object sender, RoutedEventArgs e) =>
        ShowStatus(InfoBarSeverity.Informational, Strings.Get("StudioEncoderPending"));

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();
}
