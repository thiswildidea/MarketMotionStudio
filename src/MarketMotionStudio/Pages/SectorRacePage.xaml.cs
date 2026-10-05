using System.Collections.ObjectModel;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>One candidate in the custom-sector picker grid.</summary>
public sealed record SectorPick(string Code, string Name)
{
    public bool Picked { get; set; }
}

/// <summary>One stock on the stock roster, as a chip.</summary>
public sealed record RacePick(string Code, string Name);

/// <summary>One search suggestion, as the box displays it.</summary>
public sealed record RaceStockSuggestion(string Code, string Name)
{
    public string Display => $"{Name}  {Code}";

    public override string ToString() => Display;
}

/// <summary>
/// The sector race: horizontal bars overtaking one another, their order changing to the last
/// frame — the port of `sector_race_studio.html` on the shared stage.
///
/// Four rosters, two metrics, one fetch: the roster and the metric are both redraws rather
/// than re-fetches where the data allows (the metric always; the roster always, because a
/// different roster is different data).
/// </summary>
public sealed partial class SectorRacePage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    private readonly StudioPreferences _prefs = new("Sector.");

    /// <summary>
    /// The market in force. It names the built-in lists — two for the A-shares, one
    /// for each of the others — and it is the only thing that knows what the source's
    /// amount field is measured in, which is the difference between a figure and a
    /// figure out by ten thousand.
    /// </summary>
    private readonly MarketProfile _market = Markets.Of(MarketSettings.Current);

    private SectorRaceSeries? _series;

    private readonly ObservableCollection<SectorPick> _picker = [];
    private readonly ObservableCollection<RacePick> _stocks = [];

    private readonly DispatcherTimer _searchDebounce = new() { Interval = TimeSpan.FromMilliseconds(260) };

    private string _lastQuery = string.Empty;

    private RaceStockSuggestion? _pendingChoice;

    private static readonly (int Months, string Key)[] Ranges =
    [
        (1, "StudioRange1M"),
        (3, "StudioRange3M"),
        (6, "StudioRange6M"),
        (12, "StudioRange12M"),

        // Two years, which is what one request actually carries: 640 bars is about two and a half
        // years of sessions, so this menu used to stop a year short of the endpoint's own answer.
        (24, "StudioRange24M"),
        (0, "StudioRangeCustom"),
    ];

    /// <summary>
    /// The two built-in slots. Which list fills each is the market's to say: Shanghai
    /// offers industries and themes, Hong Kong offers the four Hang Seng sub-indices,
    /// New York the sector SPDRs. The slot is what the preference is saved against, so
    /// a person's choice of "the first list" survives a change of market.
    /// </summary>
    private static readonly Roster[] BuiltInRosters = [Roster.BuiltIn0, Roster.BuiltIn1];

    private static readonly Roster[] AlwaysRosters =
    [
        Roster.Custom,
        Roster.Stocks,
    ];

    private static readonly (RaceMetric Metric, string Key)[] Metrics =
    [
        (RaceMetric.Return, "SectorMetricReturn"),
        (RaceMetric.Amount, "SectorMetricAmount"),
    ];

    public SectorRacePage()
    {
        InitializeComponent();

        foreach (var (months, key) in Ranges)
        {
            RangeCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = months });
        }

        RangeCombo.SelectedIndex = 1;

        // The rosters and the metric are chosen from these; a combo with no items shows an
        // empty box that reads as a broken page, which is exactly what shipping without this
        // loop did.
        //
        // Only the built-in slots the market fills are offered. A second slot listing the
        // same four Hang Seng sub-indices twice would be a bug dressed as a choice.
        foreach (var slot in BuiltInRosters.Take(_market.Rosters.Length))
        {
            RosterCombo.Items.Add(new ComboBoxItem
            {
                Content = Strings.Get(_market.Rosters[(int)slot].LabelKey),
                Tag = slot,
            });
        }

        foreach (var roster in AlwaysRosters)
        {
            RosterCombo.Items.Add(new ComboBoxItem
            {
                Content = Strings.Get(roster is Roster.Custom ? "SectorListCustom" : "SectorListStocks"),
                Tag = roster,
            });
        }

        // The amount is 亿 of whatever the venue quotes in: 元 on the mainland and in
        // Hong Kong, dollars in New York. The label says which, because a bar labelled
        // with the wrong currency is a bar nobody can check.
        foreach (var (metric, key) in Metrics)
        {
            var label = metric is RaceMetric.Amount && !_market.AmountInWan
                ? "SectorMetricAmountUsd"
                : key;

            MetricCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(label), Tag = metric });
        }

        // One loop, not two. There used to be a second pass here that added both metrics again
        // with the currency-blind labels, so the menu read 涨幅 / 成交额 / 涨幅 / 成交额 and the
        // dollar markets' own label sat in the first slot of a pair.
        RosterCombo.SelectedIndex = 0;
        MetricCombo.SelectedIndex = 0;

        var today = DateTimeOffset.Now;
        FromDate.Date = today.AddMonths(-3);
        ToDate.Date = today;

        // The pickers stop where one request stops, so a date someone can choose is a date the
        // guard will not then refuse. See TencentKline.MostDaysPerRequest.
        var oldest = today.AddDays(-TencentKline.MostDaysPerRequest);
        FromDate.MinYear = oldest;
        FromDate.MaxYear = today;
        ToDate.MinYear = oldest;
        ToDate.MaxYear = today;

        // The pool is what the market's lists and one-tap instruments name between them,
        // so every candidate in it is quotable — the reason the A-share lists were
        // checked against the endpoint before being written down.
        var pool = Markets.Union(_market.Id);

        foreach (var entry in pool)
        {
            // The custom roster starts as the market's first built-in list, which is the
            // source's own default and the one a person is most likely to pare back from.
            _picker.Add(new SectorPick(entry.Code, InstrumentNames.Display(entry.Code, entry.Name))
            {
                Picked = _market.Rosters[0].Entries.Any(l => l.Code == entry.Code),
            });
        }

        SectorGrid.ItemsSource = _picker;
        PickedStocks.ItemsSource = _stocks;

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

        // Named before it has ever been pressed: the button is an icon, so the tooltip and
        // the name a screen reader announces are the only words it has, and neither can
        // wait for the first toggle to appear.
        SetPlaybackState(playing: false);

        _searchDebounce.Tick += async (_, _) =>
        {
            _searchDebounce.Stop();
            await SearchSuggestionsAsync();
        };

        _prefs.Restoring = true;
        VideoSettings.Restore(_prefs);
        RestorePreferences();
        _prefs.Restoring = false;

        ApplyPreviewSettings();
        RefreshCount();
    }

    protected override InfoBar StatusControl => Status;

    protected override string JobName => Strings.Get("SectorRacePageTitle.Text");

    // ---- the picture -------------------------------------------------------------------

    private RaceMetric ChosenMetric => MetricCombo.SelectedItem is ComboBoxItem { Tag: RaceMetric metric }
        ? metric
        : RaceMetric.Return;

    private string ChosenListLabel()
    {
        var key = ChosenRoster switch
        {
            Roster.Custom => "SectorListCustom",
            Roster.Stocks => "SectorListStocks",
            // Named by the market rather than by the page: the label on the chart has to
            // be the name of the list the bars came from, and only the profile knows it.
            _ => BuiltIn(ChosenRoster) is null
                ? "SectorListCustom"
                : _market.Rosters[(int)ChosenRoster].LabelKey,
        };

        return Strings.Get(key);
    }

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        if (_series is { } series)
        {
            Preview.Renderer = new SectorRaceRenderer(
                series, ChosenMetric, VideoSettings.Duration)
            {
                Title = VideoSettings.TitleText,
                ShowTitle = VideoSettings.ShowTitle,
                ListLabel = ChosenListLabel(),
                UnitWord = Strings.Get(ChosenRoster is Roster.Stocks
                    ? "SectorUnitStocks"
                    : "SectorUnitSectors"),
            };
        }
        else
        {
            _stage.Title = VideoSettings.TitleText.Length > 0
                ? VideoSettings.TitleText
                : Strings.Get("SectorRaceStageTitle");
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

    // ---- rosters -----------------------------------------------------------------------

    private enum Roster
    {
        BuiltIn0 = 0,
        BuiltIn1 = 1,
        Custom = 2,
        Stocks = 3,
    }

    private Roster ChosenRoster => RosterCombo.SelectedItem is ComboBoxItem { Tag: Roster roster }
        ? roster
        : Roster.BuiltIn0;

    /// <summary>
    /// The entries behind a built-in slot, or null if the market has no list in it.
    ///
    /// Named through <see cref="InstrumentNames"/> rather than carried as the market file
    /// spells them. The file holds the source's own Chinese — it is the fallback, and the
    /// right one for a code the search endpoint invents — but a race drawn from a built-in
    /// list has to answer in the language the app is running in, exactly as the picker's
    /// candidates and the typed-stock names already do. Taken raw, every row of a built-in
    /// race read Chinese in all fourteen languages while the header above it read English.
    /// </summary>
    private RaceEntry[]? BuiltIn(Roster roster) =>
        (int)roster < _market.Rosters.Length
            ? [.. _market.Rosters[(int)roster].Entries.Select(
                entry => new RaceEntry(entry.Code, InstrumentNames.Display(entry.Code, entry.Name)))]
            : null;

    private IReadOnlyList<RaceEntry> CurrentRoster()
    {
        var picked = _picker.Where(p => p.Picked).Select(p => new RaceEntry(p.Code, p.Name)).ToArray();
        var stocks = _stocks.Select(s => new RaceEntry(s.Code, s.Name)).ToArray();

        return ChosenRoster switch
        {
            Roster.Stocks => stocks,
            Roster.Custom => picked,
            // A market with one list answers the second slot with the first rather than
            // with nothing: the slot is unreachable from the menu, but a restored
            // preference can still name it.
            _ => BuiltIn(ChosenRoster) ?? BuiltIn(Roster.BuiltIn0) ?? [],
        };
    }

    private void OnRosterChanged(object sender, SelectionChangedEventArgs e)
    {
        if (SectorPicker is null || StockBox is null)
        {
            return;
        }

        var roster = ChosenRoster;

        SectorPicker.Visibility = roster is Roster.Custom ? Visibility.Visible : Visibility.Collapsed;
        StockBox.Visibility = roster is Roster.Stocks ? Visibility.Visible : Visibility.Collapsed;

        // A different roster is different data; keeping the old series would race the wrong
        // bars under the new controls.
        if (!_prefs.Restoring)
        {
            _series = null;
            ApplyPreviewSettings();
            RefreshCount();
            SavePreferences();
        }
    }

    private void OnPickToggled(object sender, RoutedEventArgs e)
    {
        if (_prefs.Restoring)
        {
            return;
        }

        _series = null;
        ApplyPreviewSettings();
        RefreshCount();
        SavePreferences();
    }

    private void RefreshCount()
    {
        var n = CurrentRoster().Count;
        var bad = n < SectorLists.Fewest || n > SectorLists.Most;

        CountText.Text = Strings.Format(bad ? "SectorCountBounds" : "SectorCount", n, SectorLists.Fewest, SectorLists.Most);
        CountText.Foreground = bad
            ? (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources["TextFillColorSecondaryBrush"]
            : (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources["TextFillColorSecondaryBrush"];
    }

    // ---- the metric ----------------------------------------------------------------------

    /// <summary>
    /// Switching the metric is a redraw of the same fetch — the two measures come out of the
    /// same bars, and going back to the network would spend a round trip on data already here.
    /// </summary>
    private void OnMetricChanged(object sender, SelectionChangedEventArgs e)
    {
        if (VideoSettings is null || Preview is null)
        {
            return;
        }

        ApplyPreviewSettings();
        SavePreferences();
    }

    // ---- stock search ---------------------------------------------------------------------

    private void OnSearchTextChanged(AutoSuggestBox sender, AutoSuggestBoxTextChangedEventArgs args)
    {
        if (args.Reason is not AutoSuggestionBoxTextChangeReason.UserInput)
        {
            return;
        }

        _lastQuery = sender.Text;
        _searchDebounce.Stop();
        _searchDebounce.Start();
    }

    private async Task SearchSuggestionsAsync()
    {
        var query = _lastQuery.Trim();
        if (query.Length == 0)
        {
            StockSearch.ItemsSource = null;
            return;
        }

        try
        {
            var found = await Services.Stocks.SearchAsync(query, _market, CancellationToken.None);

            var ordered = found
                .Take(8)
                .Select(r => new RaceStockSuggestion(r.Code, InstrumentNames.Display(r.Code, r.Name)))
                .ToArray();

            StockSearch.ItemsSource = ordered;
        }
        catch (Exception)
        {
            StockSearch.ItemsSource = null;
        }
    }

    private void OnSuggestionChosen(AutoSuggestBox sender, AutoSuggestBoxSuggestionChosenEventArgs args)
    {
        if (args.SelectedItem is RaceStockSuggestion chosen)
        {
            _pendingChoice = chosen;
            sender.Text = chosen.Display;
        }
    }

    private void OnSearchSubmitted(AutoSuggestBox sender, AutoSuggestBoxQuerySubmittedEventArgs args)
    {
        var (code, name) = _pendingChoice is { } pick
            ? (pick.Code, pick.Name)
            : (StockDirectory.Normalize(sender.Text), string.Empty);

        _pendingChoice = null;

        if (code is null)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("StockBadCode"));
            return;
        }

        AddStock(code, name);
    }

    private void AddStock(string code, string name)
    {
        // The vendor's names can carry spaces («五 粮 液») which stretch a row's label into its
        // value — stripped, and the name from the bars fetch overwrites this one anyway.
        name = new string([.. name.Where(c => !char.IsWhiteSpace(c))]);

        // A built-in code answers in the interface's language; anything else keeps
        // the name the search result carried.
        name = InstrumentNames.Display(code, name);

        if (_stocks.Any(s => s.Code == code))
        {
            StockSearch.Text = string.Empty;
            return;
        }

        if (_stocks.Count >= SectorLists.Most)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format("SectorTooManyStocks", SectorLists.Most));
            return;
        }

        _stocks.Add(new RacePick(code, name.Length > 0 ? name : code.ToUpperInvariant()));
        StockSearch.Text = string.Empty;

        _series = null;
        ApplyPreviewSettings();
        RefreshCount();
        SavePreferences();
    }

    private void OnStockRemove(object sender, RoutedEventArgs e)
    {
        if ((sender as FrameworkElement)?.Tag is not string code)
        {
            return;
        }

        var at = _stocks.ToList().FindIndex(s => s.Code == code);

        if (at >= 0)
        {
            _stocks.RemoveAt(at);
            _series = null;
            ApplyPreviewSettings();
            RefreshCount();
            SavePreferences();
        }
    }

    // ---- range ---------------------------------------------------------------------------

    private void OnRangeChanged(object sender, SelectionChangedEventArgs e)
    {
        if (CustomRange is null)
        {
            return;
        }

        var custom = RangeCombo.SelectedItem is ComboBoxItem { Tag: 0 };
        CustomRange.Visibility = custom ? Visibility.Visible : Visibility.Collapsed;

        SavePreferences();
    }

    private (DateOnly Start, DateOnly End) ChosenRange()
    {
        if (RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } && months > 0)
        {
            var today = DateOnly.FromDateTime(DateTime.Now);
            return (today.AddMonths(-months), today);
        }

        return (
            DateOnly.FromDateTime(FromDate.Date.DateTime),
            DateOnly.FromDateTime(ToDate.Date.DateTime));
    }

    // ---- fetching ------------------------------------------------------------------------

    private void OnFetch(object sender, RoutedEventArgs e)
    {
        var roster = CurrentRoster();
        var unit = Strings.Get(ChosenRoster is Roster.Stocks ? "SectorUnitStocks" : "SectorUnitSectors");

        if (roster.Count < SectorLists.Fewest)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format("SectorTooFew", SectorLists.Fewest, unit));
            return;
        }

        if (roster.Count > SectorLists.Most)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format("SectorTooMany", SectorLists.Most, unit));
            return;
        }

        var (start, end) = ChosenRange();

        if (start >= end)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("TurnoverRangeReversed"));
            return;
        }

        // A count of days against a ceiling that is a count of bars — see
        // TencentKline.MostDaysPerRequest. The old figure refused a two-year span the endpoint
        // answers in full, and a race is the page where a span is most likely to be set by hand.
        if (end.DayNumber - start.DayNumber > TencentKline.MostDaysPerRequest)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format("TurnoverRangeTooLong", TencentKline.MostDaysPerRequest));
            return;
        }

        _ = RunAsync(FetchButton, async cancellation =>
        {
            var progress = new Progress<string>(message =>
                ShowStatus(InfoBarSeverity.Informational, Strings.Format("SectorFetching", message)));

            var series = await SectorSeries.LoadAsync(
                Services.Quotes, _market, roster, start, end, progress, cancellation);

            _series = series;

            // A typed stock's name is corrected to what the endpoint actually calls it.
            if (ChosenRoster is Roster.Stocks)
            {
                for (var i = 0; i < _stocks.Count; i++)
                {
                    var match = series.Entries.FirstOrDefault(e => e.Code == _stocks[i].Code);

                    if (match is { Name.Length: > 0 } && match.Name != _stocks[i].Name)
                    {
                        _stocks[i] = new RacePick(match.Code, InstrumentNames.Display(match.Code, match.Name));
                    }
                }

                SavePreferences();
            }

            ApplyPreviewSettings();
            ShowMoment(1);

            var standings = series.Standings(ChosenMetric);
            var top = standings[0];
            var bottom = standings[^1];

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "SectorFetched",
                series.Racers,
                unit,
                series.Days,
                series.Entries[top.Index].Name,
                FormatValue(top.Value),
                series.Entries[bottom.Index].Name,
                FormatValue(bottom.Value)));
        }, TimeSpan.FromMinutes(3));
    }

    private string FormatValue(double value) =>
        (ChosenMetric is RaceMetric.Return && value > 0 ? "+" : string.Empty)
        + value.ToString(
            ChosenMetric is RaceMetric.Return ? "N2" : "N0",
            System.Globalization.CultureInfo.InvariantCulture)
        + (ChosenMetric is RaceMetric.Return ? "%" : Strings.Get("SectorUnitYi"));

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
        // playback wherever it had got to — and moving the position a press afterwards will
        // start from. See the longer note on MarketTurnoverPage.
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
        // At the end there is nothing left to run, and a play button that does nothing
        // reads as a broken one. Starting again is what the press meant: these clips run
        // for a minute or two, so watching one twice is an ordinary thing to do.
        //
        // Through the seek rather than by setting the preview's progress directly, so that
        // the position playback counts from is the position the picture is showing. Two
        // places to put the position are two places to disagree about it.
        if (!_playback.IsPlaying && Preview.Progress >= 0.999)
        {
            _playback.Seek(0);
        }

        _playback.Toggle();
    }

    void IPlaybackHost.ShowMoment(double progress) => ShowMoment(progress);

    void IPlaybackHost.ShowPlaybackState(bool playing) => SetPlaybackState(playing);

    /// <summary>
    /// Points the button at what it will do next: ▶ to run the animation, ⏸ to hold it.
    ///
    /// An icon carries no text of its own, so the same word that picks the glyph is put on
    /// the tooltip and on the name a screen reader announces. Without that the button is
    /// unnamed, and "unnamed button" is what a reader has to say about a control whose
    /// whole meaning is a shape.
    /// </summary>
    private void SetPlaybackState(bool playing)
    {
        var label = Strings.Get(playing ? "StudioPause.Content" : "StudioPlay.Content");

        PlayIcon.Glyph = playing ? "\uE769" : "\uE768";

        ToolTipService.SetToolTip(PlayButton, label);
        Microsoft.UI.Xaml.Automation.AutomationProperties.SetName(PlayButton, label);
    }

    TimeSpan IPlaybackHost.PlaybackDuration => VideoSettings.Duration;

    // ---- export -----------------------------------------------------------------------------

    private string RaceFileName(VideoFormat format, string extension)
    {
        var label = VideoSettings.TitleText.Length > 0
            ? VideoSettings.TitleText
            : Strings.Format(
                ChosenMetric is RaceMetric.Return ? "SectorAutoTitleReturn" : "SectorAutoTitleAmount",
                ChosenListLabel());

        var safe = new string([.. label.Where(c => !Path.GetInvalidFileNameChars().Contains(c))]).Trim();

        if (safe.Length > 40)
        {
            safe = safe[..40];
        }

        var metric = Strings.Get(ChosenMetric is RaceMetric.Return ? "SectorMetricReturnShort" : "SectorMetricAmountShort");

        return $"{safe}_{metric}_{_series!.Dates[0]:yyyy-MM-dd}_{_series.Dates[^1]:yyyy-MM-dd}_{format.NameSuffix}.{extension}";
    }

    private async void OnExport(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || _series is not { } series || App.Window is not { } window)
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
                RaceFileName(format, "mp4"),
                report, cancellation);

            clock.Stop();

            var properties = await file.GetBasicPropertiesAsync();

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioExported",
                file.Name,
                (properties.Size / 1048576.0).ToString("0.0", System.Globalization.CultureInfo.InvariantCulture),
                clock.Elapsed.TotalSeconds.ToString("0.0", System.Globalization.CultureInfo.InvariantCulture),
                ((int)duration.TotalSeconds).ToString(System.Globalization.CultureInfo.InvariantCulture),
                folder.Path));
        }, limit);

        CancelButton.IsEnabled = false;
    }

    private async void OnSaveCover(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || _series is not { } series || App.Window is not { } window)
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
                RaceFileName(format, "png"),
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

        _prefs.Save("Roster", (int)ChosenRoster);
        _prefs.Save("Metric", (int)ChosenMetric);
        _prefs.Save("Custom", string.Join(";", _picker.Where(p => p.Picked).Select(p => p.Code)));
        _prefs.Save("Stocks", string.Join(";", _stocks.Select(s => $"{s.Code}|{s.Name}")));
        _prefs.Save("Months", RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } ? months : 3);
        _prefs.Save("From", FromDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("To", ToDate.Date.ToString("yyyy-MM-dd"));
    }

    private void RestorePreferences()
    {
        // Restored by tag, not by position. The menu is shorter in a market with one
        // built-in list than in the A-share one, so the same tag sits at a different
        // index in each: read back as an index, "custom sectors" came back as
        // "watchlist stocks" — a different list, silently, with a row count under it
        // that still looked plausible.
        var saved = _prefs.GetInt("Roster", (int)Roster.BuiltIn0);
        var wanted = Enum.IsDefined(typeof(Roster), saved) ? (Roster)saved : Roster.BuiltIn0;

        RosterCombo.SelectedItem =
            RosterCombo.Items.OfType<ComboBoxItem>().FirstOrDefault(i => i.Tag is Roster r && r == wanted)
            // No second built-in list here. Fall back to the first, as CurrentRoster
            // does, rather than leave the page on a selection the menu does not offer.
            ?? RosterCombo.Items.OfType<ComboBoxItem>().FirstOrDefault(i => i.Tag is Roster.BuiltIn0)
            ?? RosterCombo.Items[0];
        MetricCombo.SelectedIndex = Math.Clamp(_prefs.GetInt("Metric", (int)RaceMetric.Return), 0, 1);

        var custom = _prefs.GetString("Custom", string.Empty);

        if (custom.Length > 0)
        {
            var codes = custom.Split(';', StringSplitOptions.RemoveEmptyEntries).ToHashSet();

            foreach (var pick in _picker)
            {
                pick.Picked = codes.Contains(pick.Code);
            }
        }

        foreach (var item in _prefs.GetString("Stocks", string.Empty).Split(';', StringSplitOptions.RemoveEmptyEntries))
        {
            var parts = item.Split('|');

            if (parts.Length == 2 && parts[0].Length > 0)
            {
                _stocks.Add(new RacePick(parts[0], parts[1]));
            }
        }

        var months = _prefs.GetInt("Months", 3);
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
