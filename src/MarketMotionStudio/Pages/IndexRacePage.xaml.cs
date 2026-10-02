using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// The index race: twelve indices from three markets, each measured against itself.
///
/// The thirteenth page, and the only board here that is not one market's. Every other race is
/// drawn from the market the settings page chose, and every entrant on it is quoted by the same
/// venue; this one puts Shanghai, Hong Kong and New York on one axis, so it never asks the
/// market setting what is in force. That is also why the groups exist: "which indices" is this
/// page's own question, and all twelve is the answer it opens on.
///
/// **What the bar is.** The change each index has made since *its own* first month inside the
/// range, in per cent. Not its level: 3,800 on the 上证指数 and 5,700 on the S&amp;P are not two
/// points on one scale, and a board drawn on levels would be a board about where each index
/// happened to start counting. Each row therefore joins on the month the source's history for it
/// begins and is set to zero there — which is why the frame fills in as the years pass, and why
/// 恒生科技 is simply absent from the 2010 frames rather than sitting at 0.00% below everything.
///
/// **Adjusted prices, since this board took a reader's own list.** It was unadjusted, for the
/// reason the A+H page still has: an adjustment rebases a series, and two rebased series are not
/// comparable. The source does not rebase an index — asked for an adjustment it answers with the
/// same rows — so every number already on this board is unchanged, while a stock on an unadjusted
/// series is not merely off but wrong: Apple reads +193% that way and +1183% with its split and
/// dividends put back. What the board now carries is a difference in kind between its rows: an
/// index row is a price return, because an index is not a holding, and a stock row is a total
/// one. See the loader's note.
///
/// **Monthly.** One request per index carries 430 months — the source's ceiling — so "longest"
/// costs twelve requests rather than twelve walks, and the three markets' mismatched holidays
/// never meet: a day Shanghai lacked and New York had would either drop out of every row or be
/// carried forward into a claim that nothing moved.
/// </summary>
public sealed partial class IndexRacePage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    private readonly StudioPreferences _prefs = new("IndexRace.");

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
        (0, "IndexRaceRangeMax"),
        (CustomMonths, "StudioRangeCustom"),
    ];

    private static readonly (string Key, string Label)[] Lists =
    [
        (WorldIndexLists.AllKey, "IndexRaceListAll"),
        (WorldIndexLists.AShareKey, "IndexRaceListAShare"),
        (WorldIndexLists.HongKongKey, "IndexRaceListHongKong"),
        (WorldIndexLists.UnitedStatesKey, "IndexRaceListUnitedStates"),

        // One's own. Named by the sector race's own key, because that is the same offer: the
        // reader's list instead of one the app ships. See the class note for what putting a
        // stock on this board does to the one thing the board's old rule was protecting.
        (Watchlist.RosterKey, "SectorListStocks"),
    ];

    public IndexRacePage()
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

        // Ten years: long enough that the board is full — the youngest index here starts in 2020
        // — and short enough that the story is about this decade's markets.
        RangeCombo.SelectedIndex = 2;

        var today = DateTimeOffset.Now;
        FromDate.Date = today.AddYears(-5);
        ToDate.Date = today;

        // The picker has no panel of its own to write into, so what it has to say is said here.
        Watch.Notice += message => ShowStatus(InfoBarSeverity.Error, message);

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

    protected override string JobName => Strings.Get("IndexRacePageTitle.Text");

    /// <summary>“指数长跑” — what the frame says when no title was typed.</summary>
    private static string AutoTitle() => Strings.Get("IndexRacePageTitle.Text");

    private string ChosenKey() =>
        ListCombo.SelectedItem is ComboBoxItem { Tag: string chosen } ? chosen : WorldIndexLists.AllKey;

    private IReadOnlyList<RaceEntry> ChosenList() =>
        ChosenKey() is Watchlist.RosterKey ? Watch.Entries : WorldIndexLists.Of(ChosenKey());

    private string ChosenListName()
    {
        var key = ChosenKey();

        return Strings.Get(key switch
        {
            WorldIndexLists.AShareKey => "IndexRaceListAShare",
            WorldIndexLists.HongKongKey => "IndexRaceListHongKong",
            WorldIndexLists.UnitedStatesKey => "IndexRaceListUnitedStates",
            Watchlist.RosterKey => "SectorListStocks",
            _ => "IndexRaceListAll",
        });
    }

    /// <summary>
    /// What a row counts: an index on the built-in groups, a stock on the reader's own.
    /// </summary>
    private string ChosenUnit() =>
        Strings.Get(ChosenKey() is Watchlist.RosterKey ? "SectorUnitStocks" : "IndexRaceUnitIndices");

    // ---- the picture -------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        if (_series is { } series)
        {
            // The race renderer on its **return** metric, which is the one whose labels end in %.
            // Every entrant is a row, so no `showTop`: this is not a field of sixty candidates
            // racing for fifteen places, it is twelve named indices and all twelve are the board.
            Preview.Renderer = new SectorRaceRenderer(series, RaceMetric.Return, VideoSettings.Duration)
            {
                Title = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : AutoTitle(),
                ShowTitle = VideoSettings.ShowTitle,
                ListLabel = ChosenListName(),
                UnitWord = ChosenUnit(),

                // Monthly, so the header counts months — the renderer's own fallback names
                // trading days, and the page says it because the page is what asked for months.
                SpanWord = Strings.Get("MarketCapUnitMonths"),
            };
        }
        else
        {
            _stage.Title = VideoSettings.TitleText.Length > 0
                ? VideoSettings.TitleText
                : Strings.Get("IndexRaceStageTitle");
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
        // Shown only for the one group it feeds. Done while a restore is running too — a
        // remembered choice of one's own list has to come back with the list under it.
        Watch.Visibility = ChosenKey() is Watchlist.RosterKey ? Visibility.Visible : Visibility.Collapsed;

        // A different group is a different board, so whatever was fetched is no longer what the
        // panel describes, and it is dropped rather than left standing: a frame still drawn from
        // the twelve indices under a caption reading 自选股 answers a question nobody asked, and
        // it looks entirely plausible while it does.
        if (!_prefs.Restoring)
        {
            _series = null;
        }

        // Nothing is fetched until the button is pressed — see the same rule on the candle page.
        SavePreferences();
        ApplyPreviewSettings();
    }

    private void OnWatchChanged(object? sender, EventArgs e)
    {
        // A pick added or removed here changes the board on every roster page, all four sharing
        // one list, and on this one it retires the series that was fetched from the old one.
        _series = null;
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
                // which clips to the range and keeps whatever the source answers with.
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

        // Two rows is a comparison, not a board. The built-in groups are all above this, so it
        // is the reader's own list that can be short — and a list can be emptied without the
        // page noticing, one chip at a time.
        if (list.Count < Watchlist.Fewest)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format("SectorTooFew", Watchlist.Fewest, ChosenUnit()));
            return;
        }

        _ = RunAsync(FetchButton, async cancellation =>
        {
            var progress = new Progress<string>(message =>
                ShowStatus(InfoBarSeverity.Informational, Strings.Format("SectorFetching", message)));

            var series = await IndexRace.LoadAsync(
                Services.Quotes, list, start, end, progress, cancellation);

            _series = series;

            // A typed pick is renamed to what the endpoint calls it, which is also the name the
            // other three boards will read off the shared list.
            if (ChosenKey() is Watchlist.RosterKey)
            {
                foreach (var entry in series.Entries)
                {
                    Watchlist.Rename(entry.Code, InstrumentNames.Display(entry.Code, entry.Name));
                }
            }

            ApplyPreviewSettings();
            ShowMoment(1);

            var standings = IndexRace.Standings(series);

            if (standings.Length == 0)
            {
                ShowStatus(InfoBarSeverity.Error, Strings.Get("IndexRaceTooFew"));
                return;
            }

            var leader = standings[0];
            var last = standings[^1];

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "IndexRaceFetched",
                IndexRace.Quoted(series),
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

        _prefs.Save("List", ListCombo.SelectedItem is ComboBoxItem { Tag: string key } ? key : WorldIndexLists.AllKey);
        _prefs.Save("Months", RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } ? months : 120);
        _prefs.Save("From", FromDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("To", ToDate.Date.ToString("yyyy-MM-dd"));
    }

    private void RestorePreferences()
    {
        var key = _prefs.GetString("List", WorldIndexLists.AllKey);

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
