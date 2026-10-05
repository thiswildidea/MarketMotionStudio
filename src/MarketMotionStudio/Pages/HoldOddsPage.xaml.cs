using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// The hold odds: the same eight holdings the asset race runs, scored on how often holding them
/// worked rather than on how much they made.
///
/// The fourteenth page answers "what did it earn" and the fifteenth "what did it cost on the way".
/// Both are drawn on one entry and one exit — the two ends of the range — and neither can tell a
/// holder anything about the months between them, which are the months a holder actually chooses
/// from. This board runs every entry there was: bought on each month inside the range, held for the
/// same length of time, and counted once it finished. Over the last ten years the Nasdaq fund was
/// ahead on all eighty-four of its three-year entries and the Hong Kong fund on forty per cent of
/// them — two rows the asset race separates by ten years of total return and this board separates
/// by whether walking in worked at all.
///
/// **The bar is a share of entries, not a return.** 69% on the CSI 300 fund is sixty-nine months
/// out of a hundred on which a three-year hold ended ahead, and the bar is drawn on the race
/// renderer's percentage metric because that is what it is. It is not a forecast and it is not a
/// probability: it is the record, and the record is what a holder who could not have picked their
/// month was actually looking at.
///
/// **The axis is a set of finishing months.** Nothing bought in the last three years of the range
/// has finished, and counting an unfinished entry as a loss would bend every row down at the end
/// for no reason but the calendar — so the board opens on the first month an entry could have
/// finished on, and a row joins on the month its sixth one did.
///
/// Adjusted, monthly, and measured from each holding's own first month — all three for the reasons
/// the asset race gives. This board is the third on that roster and shares it, so a holding looks
/// like the same holding on all three.
/// </summary>
public sealed partial class HoldOddsPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();

    private readonly Playback _playback;

    private readonly StudioPreferences _prefs = new("HoldOdds.");

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

    /// <summary>
    /// How long each entry is held. Three years by default: long enough that a holding has to have
    /// done something rather than drifted, short enough that ten years still holds eighty-four
    /// separate entries rather than three.
    /// </summary>
    private static readonly (int Months, string Key)[] Holds =
    [
        (12, "HoldOddsHold1Y"),
        (24, "HoldOddsHold2Y"),
        (36, "HoldOddsHold3Y"),
        (60, "HoldOddsHold5Y"),
    ];

    // The roster is the asset race's, and so are its names: the same eight holdings appear on all
    // three boards, and a group called two different things on boards that are meant to be read
    // together is a group the reader has to translate.
    private static readonly (string Key, string Label)[] Lists =
    [
        (AssetClassLists.AllKey, "AssetRaceListAll"),
        (AssetClassLists.EquityKey, "AssetRaceListEquity"),
        (AssetClassLists.NonEquityKey, "AssetRaceListNonEquity"),

        // One's own. Named by the sector race's own key, because that is the same offer: the
        // reader's list instead of one the app ships.
        (Watchlist.RosterKey, "SectorListStocks"),
    ];

    public HoldOddsPage()
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

        // Ten years: long enough that the board carries eighty-four entries per row and short
        // enough that the record is this decade's.
        RangeCombo.SelectedIndex = 2;

        foreach (var (months, key) in Holds)
        {
            HoldCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = months });
        }

        HoldCombo.SelectedIndex = 2;

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

    protected override string JobName => Strings.Get("HoldOddsPageTitle.Text");

    /// <summary>“持有胜率” — what the frame says when no title was typed.</summary>
    private static string AutoTitle() => Strings.Get("HoldOddsPageTitle.Text");

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

    /// <summary>How many months each entry is held for.</summary>
    private int ChosenHold() =>
        HoldCombo.SelectedItem is ComboBoxItem { Tag: int months } ? months : 36;

    // ---- the picture -------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        if (_series is { } series)
        {
            // The race renderer on its **return** metric, which is the one whose labels end in %:
            // a share of entries is a percentage and has to read as one. Every holding is a row, so
            // no `showTop` — this is not a field of sixty candidates racing for fifteen places, it
            // is eight asset classes and all eight are the board.
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
                : Strings.Get("HoldOddsStageTitle");
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

    private void OnHoldChanged(object sender, SelectionChangedEventArgs e)
    {
        // A different holding period is a different set of entries over the same months, so the
        // board that was fetched no longer answers what the panel asks.
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

        var hold = ChosenHold();
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

            var series = await HoldOdds.LoadAsync(
                Services.Quotes, list, start, end, hold, progress, cancellation);

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

            var standings = HoldOdds.Standings(series);

            if (standings.Length == 0)
            {
                ShowStatus(InfoBarSeverity.Error, Strings.Get("HoldOddsTooFew"));
                return;
            }

            var best = standings[0];
            var worst = standings[^1];

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "HoldOddsFetched",
                HoldOdds.Quoted(series),
                series.Days,
                hold.ToString(CultureInfo.InvariantCulture),
                series.Entries[best.Index].Name,
                FormatRate(best.Value),
                series.Entries[worst.Index].Name,
                FormatRate(worst.Value)));
        }, TimeSpan.FromMinutes(6));
    }

    /// <summary>“69.0%” — a share of entries, so no sign: there is no such thing as a negative one.</summary>
    private static string FormatRate(double value) =>
        value.ToString("0.0", CultureInfo.InvariantCulture) + "%";

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

        _prefs.Save("List", ListCombo.SelectedItem is ComboBoxItem { Tag: string key } ? key : AssetClassLists.AllKey);
        _prefs.Save("Months", RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } ? months : 120);
        _prefs.Save("Hold", ChosenHold());
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

        var hold = _prefs.GetInt("Hold", 36);
        var holdMatch = HoldCombo.Items.OfType<ComboBoxItem>().FirstOrDefault(i => i.Tag is int h && h == hold);

        if (holdMatch is not null)
        {
            HoldCombo.SelectedItem = holdMatch;
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
