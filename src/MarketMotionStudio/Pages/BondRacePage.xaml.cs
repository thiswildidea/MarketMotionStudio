using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// The bond race: nine bond indices, each measured against itself.
///
/// The seventeenth page, and the board that fills the one asset class the asset race only
/// gestured at — that board has a single government-bond ETF among eight rows, and one row is not
/// a view of a market that is larger than the share market it sits behind.
///
/// **Every row is an index, and that is the whole of what separates this board from the asset
/// race.** Those eight are funds, bought with money, so they are drawn adjusted and what they
/// show is what a holder earned. These nine are published numbers: the source ignores the
/// adjustment parameter for an index, so what comes back is the quote, and a bond's coupon —
/// which is most of what a bond pays — is not in it. So the two boards are drawn from opposite
/// calls on the same endpoint, and the note under the menu says so, because a reader who put the
/// +43.70% on the treasury row beside the asset race's bond fund would be comparing a price to a
/// payout.
///
/// **What the bar is.** The change each index has made since *its own* first month inside the
/// range, in per cent. Not its level: 230.95 on an index that started at 100 and 310.17 on one
/// that started at 207 are not two points on one scale. A row therefore joins on the month its
/// own history begins and is set to zero there.
///
/// **The roster is fixed and it is short by one.** 中证全债 was asked for and does not exist on
/// this source — the code that looks like it stopped publishing in 2015, and a sweep of the whole
/// index code space found no total-bond index at all. What fills those seats is the deepest credit
/// the source does answer. The list is a judgement, and it is written down in
/// <see cref="BondLists"/> where somebody can audit it.
///
/// **Monthly.** One request per index carries 430 months, the source's ceiling, so "longest" costs
/// nine requests rather than nine walks.
/// </summary>
public sealed partial class BondRacePage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    private readonly StudioPreferences _prefs = new("BondRace.");

    private SectorRaceSeries? _series;

    /// <summary>
    /// -1 is the custom span and 0 is "as far back as the source goes", which is what the plan
    /// and holding pages already mean by 0.
    /// </summary>
    private const int CustomMonths = -1;

    private static readonly (int Months, string Key)[] Ranges =
    [
        (36, "DcaRange3Y"),
        (60, "DcaRange5Y"),
        (120, "DcaRange10Y"),
        (0, "BondRaceRangeMax"),
        (CustomMonths, "StudioRangeCustom"),
    ];

    private static readonly (string Key, string Label)[] Lists =
    [
        (BondLists.AllKey, "BondRaceListAll"),
        (BondLists.PureKey, "BondRaceListPure"),
        (BondLists.ConvertKey, "BondRaceListConvert"),
    ];

    public BondRacePage()
    {
        InitializeComponent();

        foreach (var (key, label) in Lists)
        {
            ListCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(label), Tag = key });
        }

        ListCombo.SelectedIndex = 0;

        foreach (var (months, key) in Ranges)
        {
            RangeCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = months });
        }

        // Ten years: long enough that every one of the nine is on the board from the first frame —
        // 深证转债 begins in 2014-08, five years before a ten-year window opens — and short enough
        // that the story is about this decade's money.
        RangeCombo.SelectedIndex = 2;

        var today = DateTimeOffset.Now;
        FromDate.Date = today.AddYears(-5);
        ToDate.Date = today;

        VideoSettings.AllowHideTitle = true;

        VideoSettings.Changed += (_, _) =>
        {
            ApplyPreviewSettings();
            VideoSettings.Save(_prefs);
        };

        _stage.Subtitle = Strings.Get("StudioStageNoData");
        _stage.Credit = Strings.Get("StudioCredit");

        Preview.Renderer = _stage;

        _playback = new Playback(this);

        // Named before it has ever been pressed: the button is an icon, so the tooltip and the
        // name a screen reader announces are the only words it has.
        SetPlaybackState(playing: false);

        _prefs.Restoring = true;
        VideoSettings.Restore(_prefs);
        RestorePreferences();
        _prefs.Restoring = false;

        ApplyPreviewSettings();
    }

    protected override InfoBar StatusControl => Status;

    protected override string JobName => Strings.Get("BondRacePageTitle.Text");

    /// <summary>“债市固收竞速” — what the frame says when no title was typed.</summary>
    private static string AutoTitle() => Strings.Get("BondRacePageTitle.Text");

    private string ChosenKey() =>
        ListCombo.SelectedItem is ComboBoxItem { Tag: string chosen } ? chosen : BondLists.AllKey;

    private IReadOnlyList<RaceEntry> ChosenList() => BondLists.Of(ChosenKey());

    private string ChosenListName()
    {
        var key = ChosenKey();

        return Strings.Get(key switch
        {
            BondLists.PureKey => "BondRaceListPure",
            BondLists.ConvertKey => "BondRaceListConvert",
            _ => "BondRaceListAll",
        });
    }

    // ---- the picture -------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        if (_series is { } series)
        {
            // The race renderer on its **return** metric, which is the one whose labels end in %.
            // Every index is a row, so no `showTop`: this is not a field of sixty candidates
            // racing for fifteen places, it is nine bond indices and all nine are the board.
            Preview.Renderer = new SectorRaceRenderer(series, RaceMetric.Return, VideoSettings.Duration)
            {
                Title = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : AutoTitle(),
                ShowTitle = VideoSettings.ShowTitle,
                ListLabel = ChosenListName(),
                // What a row counts: all nine are bond indices, and the header has to say so
                // rather than call an index a share or an asset. One word for every group,
                // because the roster is fixed — unlike the asset race there is no reader's own
                // list here for the counting word to change under.
                UnitWord = Strings.Get("BondRaceUnitBonds"),

                // Monthly, so the header counts months — the renderer's own fallback names
                // trading days, and the page says it because the page is what asked for months.
                SpanWord = Strings.Get("MarketCapUnitMonths"),
            };
        }
        else
        {
            _stage.Title = VideoSettings.TitleText.Length > 0
                ? VideoSettings.TitleText
                : Strings.Get("BondRaceStageTitle");
            _stage.ShowTitle = VideoSettings.ShowTitle;
            Preview.Renderer = _stage;
        }

        var ready = _series is not null;

        PlayButton.IsEnabled = ready;
        ExportButton.IsEnabled = ready;
        CoverButton.IsEnabled = ready;

        RefreshScrubText();
        Preview.Redraw();
    }

    // ---- range ---------------------------------------------------------------------------

    private void OnListChanged(object sender, SelectionChangedEventArgs e)
    {
        // A different group is a different board, so whatever was fetched is no longer what the
        // panel describes, and it is dropped rather than left standing: a frame still drawn from
        // the nine under a caption reading 可转债 answers a question nobody asked, and it looks
        // entirely plausible while it does.
        if (!_prefs.Restoring)
        {
            _series = null;
        }

        // Nothing is fetched until the button is pressed — see the same rule on the candle page.
        SavePreferences();
        ApplyPreviewSettings();
    }

    private void OnRangeChanged(object sender, SelectionChangedEventArgs e)
    {
        if (CustomRange is null)
        {
            return;
        }

        var custom = RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } && months == CustomMonths;

        CustomRange.Visibility = custom ? Visibility.Visible : Visibility.Collapsed;

        SavePreferences();
    }

    private (DateOnly Start, DateOnly End) ChosenRange()
    {
        if (RangeCombo.SelectedItem is ComboBoxItem { Tag: int months })
        {
            var today = DateOnly.FromDateTime(DateTime.Now);

            if (months > 0)
            {
                return (today.AddMonths(-months), today);
            }

            if (months == 0)
            {
                // "As far back as there is" — asked for generously and trimmed by the loader,
                // which clips to the range and keeps whatever the source answers with. The oldest
                // of the nine starts in 2003-02, so this is a twenty-three year board at most.
                return (today.AddYears(-30), today);
            }
        }

        return (
            DateOnly.FromDateTime(FromDate.Date.DateTime),
            DateOnly.FromDateTime(ToDate.Date.DateTime));
    }

    // ---- fetching ------------------------------------------------------------------------

    private void OnFetch(object sender, RoutedEventArgs e)
    {
        var (start, end) = ChosenRange();

        if (start >= end)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("TurnoverRangeReversed"));
            return;
        }

        var list = ChosenList();

        _ = RunAsync(FetchButton, async cancellation =>
        {
            var progress = new Progress<string>(message =>
                ShowStatus(InfoBarSeverity.Informational, Strings.Format("SectorFetching", message)));

            var series = await BondRace.LoadAsync(
                Services.Quotes, list, start, end, progress, cancellation);

            _series = series;

            ApplyPreviewSettings();
            ShowMoment(1);

            var standings = BondRace.Standings(series);

            if (standings.Length == 0)
            {
                ShowStatus(InfoBarSeverity.Error, Strings.Get("AssetRaceTooFew"));
                return;
            }

            var leader = standings[0];
            var last = standings[^1];

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "BondRaceFetched",
                BondRace.Quoted(series),
                series.Days,
                series.Entries[leader.Index].Name,
                FormatValue(leader.Value),
                series.Entries[last.Index].Name,
                FormatValue(last.Value)));
        }, TimeSpan.FromMinutes(6));
    }

    private static string FormatValue(double value) =>
        (value >= 0 ? "+" : "−") + Math.Abs(value).ToString("0.00", CultureInfo.InvariantCulture) + "%";

    // ---- preview transport -----------------------------------------------------------------

    private void ShowMoment(double progress)
    {
        Preview.Progress = progress;

        Scrub.ValueChanged -= OnScrub;
        Scrub.Value = progress;
        Scrub.ValueChanged += OnScrub;

        RefreshScrubText();
        Preview.Redraw();
    }

    private void OnScrub(object sender, RangeBaseValueChangedEventArgs e)
    {
        // Moving the slider is an instruction to look at one moment, which means stopping the
        // playback wherever it had got to. See the longer note on MarketTurnoverPage.
        _playback?.Seek(Scrub.Value);
    }

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

    // ---- export -----------------------------------------------------------------------------

    private string CapFileName(VideoFormat format, string extension)
    {
        var label = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : AutoTitle();

        var safe = new string([.. label.Where(c => !Path.GetInvalidFileNameChars().Contains(c))]).Trim();

        if (safe.Length > 40)
        {
            safe = safe[..40];
        }

        return $"{safe}_{_series!.Dates[0]:yyyy-MM-dd}_{_series.Dates[^1]:yyyy-MM-dd}_{format.NameSuffix}.{extension}";
    }

    private async void OnExport(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || _series is null || App.Window is not { } window)
        {
            return;
        }

        // One gate, asked by every page. Writing the file — as opposed to
        // drawing it — is what the subscription buys, and the one place allowed
        // to answer that is asked before anything is read for the encode.
        if (!await MarketMotionStudio.Views.SubscriptionOffer.PermitAsync(XamlRoot, window))
        {
            return;
        }

        var format = VideoSettings.Format;
        var margins = VideoSettings.Margins;
        var duration = VideoSettings.Duration;

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
                CapFileName(format, "mp4"),
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
        if (Preview.Renderer is not { } renderer || _series is null || App.Window is not { } window)
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
                CapFileName(format, "png"),
                cancellation);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioCoverSaved", file.Name, format.Width, format.Height, folder.Path));
        }, TimeSpan.FromSeconds(90));
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();

    // ---- persistence ---------------------------------------------------------------------------

    private void SavePreferences()
    {
        if (_prefs.Restoring)
        {
            return;
        }

        _prefs.Save("List", ListCombo.SelectedItem is ComboBoxItem { Tag: string key } ? key : BondLists.AllKey);
        _prefs.Save("Months", RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } ? months : 120);
        _prefs.Save("From", FromDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("To", ToDate.Date.ToString("yyyy-MM-dd"));
    }

    private void RestorePreferences()
    {
        var key = _prefs.GetString("List", BondLists.AllKey);

        ListCombo.SelectedItem =
            ListCombo.Items.OfType<ComboBoxItem>().FirstOrDefault(i => i.Tag is string c && c == key)
            ?? ListCombo.Items[0];

        var months = _prefs.GetInt("Months", 120);
        var match = RangeCombo.Items.OfType<ComboBoxItem>().FirstOrDefault(i => i.Tag is int m && m == months);

        if (match is not null)
        {
            RangeCombo.SelectedItem = match;
        }

        if (DateOnly.TryParse(_prefs.GetString("From", string.Empty), out var from))
        {
            FromDate.Date = new DateTimeOffset(from, TimeOnly.MinValue, TimeSpan.Zero);
        }

        if (DateOnly.TryParse(_prefs.GetString("To", string.Empty), out var to))
        {
            ToDate.Date = new DateTimeOffset(to, TimeOnly.MinValue, TimeSpan.Zero);
        }
    }
}
