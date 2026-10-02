using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// The asset race: eight holdings, one per asset class, each measured against itself.
///
/// The fourteenth page, and the counterpart to the index race. That board races published
/// numbers; this one races things that can be held — a fund quoted on a mainland exchange, bought
/// with the same money through the same broker, and carrying the exchange rate inside it when what
/// it tracks is abroad. That is the only difference that matters and it drives the one that
/// decides the whole board:
///
/// **Adjusted, where the index race is unadjusted.** An index pays no dividend, so leaving its
/// series alone costs nothing. A fund does pay, and what it pays is invisible in its price: the
/// money-market fund's price barely moves across thirteen years while a holder earned a third,
/// and a Nasdaq fund that split its units looks, unadjusted, like it gained 136% over a decade in
/// which its index rose sixfold. Unadjusted, this board would put cash last — the one row here
/// that never fell — and understate the overseas row by a factor of five. The index race and this
/// board therefore share their arithmetic and nothing else, which is why they do not share a
/// loader: the reason has to be readable where the call is made.
///
/// **What the bar is.** The change each holding has made since *its own* first month inside the
/// range, in per cent. Not its price: 1.97 on a fund launched at 2.63 and 3.26 on one launched at
/// 2.66 are not two points on one scale. A row therefore joins on the month its own history begins
/// and is set to zero there, which is why the board fills in as the years pass — the commodity
/// fund starts in 2019 and is absent from every frame before it, rather than sitting at 0.00%
/// beneath everything that was ever down.
///
/// **Monthly.** One request per holding carries 430 months, the source's ceiling, so "longest"
/// costs eight requests rather than eight walks.
/// </summary>
public sealed partial class AssetRacePage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    private readonly StudioPreferences _prefs = new("AssetRace.");

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
        (0, "AssetRaceRangeMax"),
        (CustomMonths, "StudioRangeCustom"),
    ];

    private static readonly (string Key, string Label)[] Lists =
    [
        (AssetClassLists.AllKey, "AssetRaceListAll"),
        (AssetClassLists.EquityKey, "AssetRaceListEquity"),
        (AssetClassLists.NonEquityKey, "AssetRaceListNonEquity"),

        // One's own. Named by the sector race's own key, because that is the same offer: the
        // reader's list instead of one the app ships.
        (Watchlist.RosterKey, "SectorListStocks"),
    ];

    public AssetRacePage()
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

        // Ten years: long enough that the board is full of everything but the commodity fund —
        // which starts in 2019 — and short enough that the story is about this decade's money.
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

    protected override string JobName => Strings.Get("AssetRacePageTitle.Text");

    /// <summary>“大类资产” — what the frame says when no title was typed.</summary>
    private static string AutoTitle() => Strings.Get("AssetRacePageTitle.Text");

    private string ChosenKey() =>
        ListCombo.SelectedItem is ComboBoxItem { Tag: string chosen } ? chosen : AssetClassLists.AllKey;

    private IReadOnlyList<RaceEntry> ChosenList() =>
        ChosenKey() is Watchlist.RosterKey ? Watch.Entries : AssetClassLists.Of(ChosenKey());

    private string ChosenListName()
    {
        var key = ChosenKey();

        return Strings.Get(key switch
        {
            AssetClassLists.EquityKey => "AssetRaceListEquity",
            AssetClassLists.NonEquityKey => "AssetRaceListNonEquity",
            Watchlist.RosterKey => "SectorListStocks",
            _ => "AssetRaceListAll",
        });
    }

    /// <summary>
    /// What a row counts. The eight funds are "标的" because a fund is not a stock and one of
    /// them is not even a share; a reader's own list is made of stocks, and the header has to
    /// say so rather than call a share something it is not.
    /// </summary>
    private string ChosenUnit() =>
        Strings.Get(ChosenKey() is Watchlist.RosterKey ? "SectorUnitStocks" : "AssetRaceUnitAssets");

    // ---- the picture -------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        if (_series is { } series)
        {
            // The race renderer on its **return** metric, which is the one whose labels end in %.
            // Every holding is a row, so no `showTop`: this is not a field of sixty candidates
            // racing for fifteen places, it is eight asset classes and all eight are the board.
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
                : Strings.Get("AssetRaceStageTitle");
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
        // the eight funds under a caption reading 自选股 answers a question nobody asked, and it
        // looks entirely plausible while it does.
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

            var series = await AssetRace.LoadAsync(
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

            var standings = AssetRace.Standings(series);

            if (standings.Length == 0)
            {
                ShowStatus(InfoBarSeverity.Error, Strings.Get("AssetRaceTooFew"));
                return;
            }

            var leader = standings[0];
            var last = standings[^1];

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "AssetRaceFetched",
                AssetRace.Quoted(series),
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

        _prefs.Save("List", ListCombo.SelectedItem is ComboBoxItem { Tag: string key } ? key : AssetClassLists.AllKey);
        _prefs.Save("Months", RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } ? months : 120);
        _prefs.Save("From", FromDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("To", ToDate.Date.ToString("yyyy-MM-dd"));
    }

    private void RestorePreferences()
    {
        var key = _prefs.GetString("List", AssetClassLists.AllKey);

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
