using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// The plan page's question — a fixed amount on a fixed cadence, and what that
/// discipline turned into — asked of a coin.
///
/// The simulation is <see cref="DcaPlanner"/>'s, unchanged and not repeated here. What
/// this page changes is two words the stock page has to be careful about. **A coin
/// trades every day**, so a weekly plan buys every seven days rather than on the five
/// days a venue was open, and a daily one buys three hundred and sixty-five times a
/// year — a cadence is a calendar here, not a trading calendar. And **there is no
/// dividend to reinvest**, so the close is the whole return and the plan is not the
/// generous fiction the stock page's is; see the disclaimer on the frame.
///
/// The buy dates are still read off each coin's own days rather than off a grid, which
/// for a coin means the days it actually has — a source that missed a day, or a coin
/// that listed inside the span.
/// </summary>
public sealed partial class CryptoDcaPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    private const int CustomMonths = -1;

    private static readonly (int Months, string Key)[] Ranges =
    [
        (36, "DcaRange3Y"),
        (60, "DcaRange5Y"),
        (120, "DcaRange10Y"),
        (0, "DcaRangeMax"),
        (CustomMonths, "StudioRangeCustom"),
    ];

    private static readonly (DcaFrequency Frequency, string Key)[] Frequencies =
    [
        (DcaFrequency.Daily, "DcaFreqDaily"),
        (DcaFrequency.Weekly, "DcaFreqWeekly"),
        (DcaFrequency.Monthly, "DcaFreqMonthly"),
    ];

    private readonly StudioPreferences _prefs = new("CryptoDca.");

    private const int DefaultWindow = 60;

    private const int MinWindow = 10;

    private const int MaxWindow = 500;

    private DcaBoard? _board;

    private bool _ready;

    public CryptoDcaPage()
    {
        InitializeComponent();

        foreach (var (frequency, key) in Frequencies)
        {
            FreqCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = frequency });
        }

        // Weekly: a coin can be bought on a Monday, and a plan is the sort of thing a
        // person sets up on payday rather than daily.
        FreqCombo.SelectedIndex = 1;

        foreach (var (months, key) in Ranges)
        {
            RangeCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = months });
        }

        RangeCombo.SelectedIndex = 0;

        var now = DateTimeOffset.Now;
        var oldest = now.AddDays(-CryptoQuotes.YahooMostDays);

        FromDate.MinYear = oldest;
        FromDate.MaxYear = now;
        ToDate.MinYear = oldest;
        ToDate.MaxYear = now;

        foreach (var (motion, key) in new[]
                 {
                     (DcaMotion.Grow, "DcaMotionGrow"),
                     (DcaMotion.Scroll, "DcaMotionScroll"),
                 })
        {
            MotionCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = (int)motion });
        }

        MotionCombo.SelectedIndex = 0;

        Coins.Changed += OnCoinsChanged;

        VideoSettings.AllowHideTitle = false;
        VideoSettings.AllowTitleText = false;

        VideoSettings.Changed += (_, _) =>
        {
            ApplyPreviewSettings();
            SavePreferences();
        };

        // 标题区的样式与文字归 TitlePanel：面板的标题框和隐藏开关都不再是编辑入口。
        TitlePanel.Changed += (_, _) =>
        {
            VideoSettings.SetTitleText(TitlePanel.TitleText);
            ApplyPreviewSettings();
            SavePreferences();
        };

        _stage.Subtitle = Strings.Get("StudioStageNoData");
        _stage.Credit = Strings.Get("StudioCredit");

        Preview.Renderer = _stage;

        _playback = new Playback(this);

        SetPlaybackState(playing: false);

        RestorePreferences();
        ApplyPreviewSettings();

        _ready = true;
    }

    protected override InfoBar StatusControl => Status;

    protected override string JobName => Strings.Get("CryptoDcaPageTitle.Text");

    // ---- what is being drawn ---------------------------------------------------------

    private IReadOnlyList<RaceEntry> Chosen() => [.. Coins.Selected];

    private void OnCoinsChanged(object? sender, EventArgs e)
    {
        _board = null;
        SavePreferences();
        ApplyPreviewSettings();
    }

    // ---- the plan's terms ------------------------------------------------------------

    private double ChosenAmount
    {
        get
        {
            var text = AmountBox.Text.Trim();

            return double.TryParse(text, NumberStyles.Float, CultureInfo.CurrentUICulture, out var amount) ? amount
                : double.TryParse(text, NumberStyles.Float, CultureInfo.InvariantCulture, out amount) ? amount
                : 0;
        }
    }

    private DcaFrequency ChosenFrequency =>
        FreqCombo.SelectedItem is ComboBoxItem { Tag: DcaFrequency frequency } ? frequency : DcaFrequency.Weekly;

    private int ChosenMonths() =>
        RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } ? months : 0;

    private DcaMotion ChosenMotion() =>
        MotionCombo.SelectedItem is ComboBoxItem { Tag: int motion }
            ? (DcaMotion)motion
            : DcaMotion.Grow;

    private bool CrossSafeRight() => CrossCheck.IsChecked is true;

    private int ChosenWindow()
    {
        var text = WindowBox.Text.Trim();

        var window = int.TryParse(text, NumberStyles.Integer, CultureInfo.CurrentUICulture, out var parsed) ? parsed
            : int.TryParse(text, NumberStyles.Integer, CultureInfo.InvariantCulture, out parsed) ? parsed
            : DefaultWindow;

        return Math.Clamp(window, MinWindow, MaxWindow);
    }

    private static DateOnly Oldest =>
        DateOnly.FromDateTime(DateTime.Now).AddDays(-CryptoQuotes.YahooMostDays);

    private (DateOnly Start, DateOnly End) ChosenRange()
    {
        var months = ChosenMonths();
        var today = DateOnly.FromDateTime(DateTime.Now);

        if (months == CustomMonths)
        {
            var (from, to) = CustomSpan();

            return (from, to > today ? today : to);
        }

        return months == 0 ? (Oldest, today) : (today.AddMonths(-months), today);
    }

    private (DateOnly From, DateOnly To) CustomSpan() =>
        (DateOnly.FromDateTime(FromDate.Date.DateTime), DateOnly.FromDateTime(ToDate.Date.DateTime));

    private void OnLookChanged(object sender, object e)
    {
        if (!_ready)
        {
            return;
        }

        ApplyPreviewSettings();
        SavePreferences();
    }

    // ---- preview ---------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        var title = ResolvedTitle();
        var showTitle = !TitlePanel.HideTitle;
        var subtitle = TitlePanel.SubtitleText;

        TitlePanel.TitleText = title;

        if (_board is { } board)
        {
            var plan = AnimationPlan.For(VideoSettings.Duration, board.Dates.Count, board.Peak);

            Preview.Renderer = new DcaRenderer(
                board, plan, ChosenMotion(), ChosenWindow(), CrossSafeRight(),
                TitlePanel.MainStyle, TitlePanel.SubtitleStyle)
            {
                Title = title,
                ShowTitle = showTitle,
                Subtitle = subtitle,
                CurrencyKey = "DcaCurrencyUsd",
            };
        }
        else
        {
            _stage.Title = title;
            _stage.ShowTitle = showTitle;
            Preview.Renderer = _stage;
        }

        WindowBox.IsEnabled = ChosenMotion() is DcaMotion.Scroll;

        VideoSettings.TitlePlaceholder = DefaultTitle();

        var ready = _board is not null;

        PlayButton.IsEnabled = ready;
        ExportButton.IsEnabled = ready;
        CoverButton.IsEnabled = ready;

        RefreshScrubText();
        Preview.Redraw();
    }

    private string ResolvedTitle() =>
        VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : DefaultTitle();

    private string DefaultTitle()
    {
        if (_board is { } board)
        {
            return board.Comparing
                ? Compared([.. board.Tracks.Select(t => t.Name)])
                : Strings.Format("CryptoDcaDefaultTitle", board.Tracks[0].Name);
        }

        var names = Chosen().Select(e => InstrumentNames.Display(e.Code, e.Name)).ToArray();

        return names.Length switch
        {
            0 => Strings.Format("CryptoDcaDefaultTitle", CryptoAsset.All[0].Display),
            1 => Strings.Format("CryptoDcaDefaultTitle", names[0]),
            _ => Compared(names),
        };
    }

    private static string Compared(string[] names) => names.Length == 2
        ? Strings.Format("DcaVsTitle", names[0], names[1])
        : Strings.Format("DcaCompareMany", names[0], names.Length);

    // ---- fetching --------------------------------------------------------------------

    private async void Fetch()
    {
        var amount = ChosenAmount;

        if (amount <= 0)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("DcaAmountInvalid"));
            return;
        }

        var (start, end) = ChosenRange();

        if (ChosenMonths() == CustomMonths && start >= end)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("TurnoverRangeReversed"));
            return;
        }

        var chosen = Chosen();

        if (chosen.Count == 0)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("CryptoPickOne"));
            return;
        }

        if (chosen.Count > DcaPlanner.MostTracks)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format(
                "DcaTooMany", DcaPlanner.MostTracks, chosen.Count));
            return;
        }

        await RunAsync(FetchButton, async cancellation =>
        {
            var progress = new Progress<string>(message => ShowStatus(InfoBarSeverity.Informational, message));

            var board = await DcaPlanner.LoadBoardAsync(
                Services.CryptoCloses, chosen, ChosenFrequency, amount, start, end, progress, cancellation);

            _board = board;

            ApplyPreviewSettings();

            ShowMoment(1);

            var skipped = board.Skipped.Count > 0
                ? " " + Strings.Format("DcaSkipped", string.Join("、", board.Skipped))
                : string.Empty;

            ShowFetched((board.Comparing
                ? Strings.Format(
                    "CryptoDcaBoardFetched",
                    board.Tracks.Count,
                    board.Dates.Count,
                    DcaRenderer.Iso(board.Start),
                    DcaRenderer.Iso(board.End))
                : Strings.Format(
                    "CryptoDcaFetched",
                    board.Dates.Count,
                    DcaRenderer.Iso(board.Start),
                    DcaRenderer.Iso(board.End),
                    board.Buys)) + skipped,
                InfoBarSeverity.Success, board.Start, start,
                Strings.Format("CryptoRangeShort", DcaRenderer.Iso(board.Start)));
        }, TimeSpan.FromMinutes(6));
    }

    private void OnFetch(object sender, RoutedEventArgs e) => Fetch();

    // ---- playback --------------------------------------------------------------------

    private void ShowMoment(double progress)
    {
        Preview.Progress = progress;

        Scrub.ValueChanged -= OnScrub;
        Scrub.Value = progress;
        Scrub.ValueChanged += OnScrub;

        RefreshScrubText();
        Preview.Redraw();
    }

    private void OnPlanChanged(object sender, object e)
    {
        if (FreqCombo is null || RangeCombo is null)
        {
            return;
        }

        CustomRange.Visibility = ChosenMonths() == CustomMonths
            ? Visibility.Visible
            : Visibility.Collapsed;

        if (!_ready)
        {
            return;
        }

        SavePreferences();
    }

    private void OnCustomRangeChanged(object sender, DatePickerValueChangedEventArgs e)
    {
        if (!_ready)
        {
            return;
        }

        SavePreferences();
    }

    private void OnScrub(object sender, RangeBaseValueChangedEventArgs e) => _playback?.Seek(Scrub.Value);

    private void RefreshScrubText()
    {
        var total = VideoSettings.Duration;
        var at = TimeSpan.FromSeconds(total.TotalSeconds * Math.Clamp(Preview.Progress, 0, 1));

        ScrubText.Text = Strings.Format("StudioScrubPosition", Clock(at), Clock(total));
    }

    private void OnPlay(object sender, RoutedEventArgs e)
    {
        if (!_playback.IsPlaying && Preview.Progress >= 0.999)
        {
            _playback.Seek(0);
        }

        _playback.Toggle();
    }

    void IPlaybackHost.ShowMoment(double progress) => ShowMoment(progress);

    void IPlaybackHost.ShowPlaybackState(bool playing) => SetPlaybackState(playing);

    private void SetPlaybackState(bool playing)
    {
        var label = Strings.Get(playing ? "StudioPause.Content" : "StudioPlay.Content");

        PlayIcon.Glyph = playing ? "\uE769" : "\uE768";

        ToolTipService.SetToolTip(PlayButton, label);
        Microsoft.UI.Xaml.Automation.AutomationProperties.SetName(PlayButton, label);
    }

    TimeSpan IPlaybackHost.PlaybackDuration => VideoSettings.Duration;

    // ---- export ----------------------------------------------------------------------

    private async void OnExport(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || _board is not { } board || App.Window is not { } window)
        {
            return;
        }

        if (!await MarketMotionStudio.Views.SubscriptionOffer.PermitAsync(XamlRoot, window))
        {
            return;
        }

        var format = VideoSettings.Format;
        var margins = VideoSettings.Margins;
        var duration = VideoSettings.Duration;
        var label = ResolvedTitle();

        CancelButton.IsEnabled = true;

        var limit = TimeSpan.FromMinutes(5) + (duration * 4);

        await RunAsync(ExportButton, async cancellation =>
        {
            var folder = await OutputFolder.TryGetAsync() ?? await OutputFolder.ChooseAsync(window);

            if (folder is null)
            {
                ShowStatus(InfoBarSeverity.Informational, Strings.Get("StudioExportCancelled"));
                return;
            }

            var clock = System.Diagnostics.Stopwatch.StartNew();

            var report = new Progress<double>(fraction =>
                ShowStatus(InfoBarSeverity.Informational, Strings.Format("StudioExporting", (int)(fraction * 100))));

            var file = await VideoExporter.EncodeAsync(
                renderer, format, margins, duration, folder,
                VideoExporter.VideoName(label, board.Start, board.End, format),
                report, cancellation);

            clock.Stop();

            var properties = await file.GetBasicPropertiesAsync();

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioExported",
                file.Name,
                (properties.Size / 1048576.0).ToString("0.0", CultureInfo.InvariantCulture),
                clock.Elapsed.TotalSeconds.ToString("0.0", CultureInfo.InvariantCulture),
                ((int)duration.TotalSeconds).ToString(CultureInfo.InvariantCulture),
                folder.Path));
        }, limit);

        CancelButton.IsEnabled = false;
    }

    private async void OnSaveCover(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || _board is not { } board || App.Window is not { } window)
        {
            return;
        }

        await RunAsync(CoverButton, async cancellation =>
        {
            var folder = await OutputFolder.TryGetAsync() ?? await OutputFolder.ChooseAsync(window);

            if (folder is null)
            {
                ShowStatus(InfoBarSeverity.Informational, Strings.Get("StudioCoverCancelled"));
                return;
            }

            var format = VideoSettings.Format;

            var file = await FrameExporter.SavePngAsync(
                renderer, format, VideoSettings.Margins, Preview.Progress, folder,
                FrameExporter.CoverName(ResolvedTitle(), board.Start, board.End, format),
                cancellation);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioCoverSaved", file.Name, format.Width, format.Height, folder.Path));
        }, TimeSpan.FromSeconds(90));
    }

    // ---- preferences -----------------------------------------------------------------

    private void RestorePreferences()
    {
        _prefs.Restoring = true;

        var amount = _prefs.GetDouble("Amount", 100);
        AmountBox.Text = amount > 0 ? amount.ToString("0.##", CultureInfo.InvariantCulture) : "100";

        var frequency = _prefs.GetString("Frequency", DcaFrequency.Weekly.ToString());
        var which = Array.FindIndex(Frequencies, f => f.Frequency.ToString() == frequency);
        FreqCombo.SelectedIndex = which >= 0 ? which : 1;

        var months = _prefs.GetInt("Months", 36);
        var index = Array.FindIndex(Ranges, r => r.Months == months);
        RangeCombo.SelectedIndex = index >= 0 ? index : 0;

        MotionCombo.SelectedIndex = _prefs.GetInt("Motion", (int)DcaMotion.Grow) == (int)DcaMotion.Scroll ? 1 : 0;
        WindowBox.Text = Math.Clamp(_prefs.GetInt("Window", DefaultWindow), MinWindow, MaxWindow)
            .ToString(CultureInfo.InvariantCulture);

        CrossCheck.IsChecked = _prefs.GetInt("CrossSafeRight", 0) != 0;

        var today = DateTimeOffset.Now;
        FromDate.Date = today.AddYears(-3);
        ToDate.Date = today;

        if (DateOnly.TryParse(_prefs.GetString("From", string.Empty), out var from))
        {
            FromDate.Date = new DateTimeOffset(from, TimeOnly.MinValue, TimeSpan.Zero);
        }

        if (DateOnly.TryParse(_prefs.GetString("To", string.Empty), out var to))
        {
            ToDate.Date = new DateTimeOffset(to, TimeOnly.MinValue, TimeSpan.Zero);
        }

        Coins.Select(_prefs.GetString("Coins", "BTC").Split(';', StringSplitOptions.RemoveEmptyEntries));

        VideoSettings.Restore(_prefs);
        TitlePanel.Restore(_prefs);

        _prefs.Restoring = false;
    }

    private void SavePreferences()
    {
        _prefs.Save("Amount", ChosenAmount > 0 ? ChosenAmount : 100);
        _prefs.Save("Frequency", ChosenFrequency.ToString());
        _prefs.Save("Months", ChosenMonths());
        _prefs.Save("Motion", (int)ChosenMotion());
        _prefs.Save("Window", ChosenWindow());
        _prefs.Save("CrossSafeRight", CrossSafeRight() ? 1 : 0);
        _prefs.Save("From", FromDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("To", ToDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("Coins", string.Join(";", Chosen().Select(c => c.Code)));

        VideoSettings.Save(_prefs);
        TitlePanel.Save(_prefs);
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();
}
