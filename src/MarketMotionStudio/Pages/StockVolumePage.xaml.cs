using System.Collections.ObjectModel;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>One saved instrument, for the chips row.</summary>
public sealed record StockFavourite(string Code, string Name)
{
    public string CodeUpper => Code.ToUpperInvariant();

    public override string ToString() => $"{Name} {CodeUpper}";
}

/// <summary>One search suggestion, as the box itself displays it.</summary>
public sealed record StockSuggestion(string Code, string Name, string Kind)
{
    public string Display => $"{Market.InstrumentNames.Display(Code, Name)}  {Code}  {Kind}";

    public override string ToString() => Display;
}

/// <summary>
/// One stock's volume against its turnover rate, as two stacked panels — the port of
/// `stock_dual_studio.html`, on the shared stage the whole-market page already draws on.
///
/// The two modes ask the source different questions and so trade controls: a multi-day span is
/// chosen freely, a single day is one of the few the minute endpoint still holds, and the fetch
/// fills that list rather than the page guessing at dates.
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

    /// <summary>
    /// The market in force, fixed for the life of the page. It decides whether the
    /// intraday mode exists at all and how the source's volume field is read, so it
    /// is taken once rather than asked for at each use.
    /// </summary>
    private readonly MarketProfile _market = Markets.Of(MarketSettings.Current);

    /// <summary>The fetched series, or null before anything has been fetched.</summary>
    private StockPanelSeries? _series;

    private readonly ObservableCollection<StockFavourite> _favourites = [];

    /// <summary>
    /// Debounces the suggestion search. A suggestion list that arrived per keystroke would flicker
    /// and race; 260 ms is shorter than a person's pause and longer than a keystroke.
    /// </summary>
    private readonly DispatcherTimer _searchDebounce = new() { Interval = TimeSpan.FromMilliseconds(260) };

    private string _lastQuery = string.Empty;

    /// <summary>The suggestion a person picked, held until the submit event follows it.</summary>
    private StockSuggestion? _pendingChoice;

    private bool _restoringDay;

    private static readonly (int Months, string Key)[] Ranges =
    [
        (1, "StudioRange1M"),
        (3, "StudioRange3M"),
        (6, "StudioRange6M"),
        (12, "StudioRange12M"),
        (24, "StudioRange24M"),
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

        // The minute endpoint answers a US code with an empty body, so on that market
        // there is no intraday mode to offer and no reason to show a choice of one:
        // the whole group goes, not just the radio that would have no data behind it.
        if (!_market.Intraday)
        {
            ModeGroup.Visibility = Visibility.Collapsed;
        }

        var today = DateTimeOffset.Now;
        FromDate.Date = today.AddMonths(-3);
        ToDate.Date = today;

        // The pickers stop where one request stops. A date someone can choose and a date the guard
        // then refuses is a control arguing with itself, and the guard is the one that is right —
        // see TencentKline.MostDaysPerRequest. Same shape as the plan and holding pages.
        var oldest = today.AddDays(-TencentKline.MostDaysPerRequest);
        FromDate.MinYear = oldest;
        FromDate.MaxYear = today;
        ToDate.MinYear = oldest;
        ToDate.MaxYear = today;

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

        // Named before it has ever been pressed: the button is an icon, so the tooltip and
        // the name a screen reader announces are the only words it has, and neither can
        // wait for the first toggle to appear.
        SetPlaybackState(playing: false);

        Favourites.ItemsSource = _favourites;

        _searchDebounce.Tick += async (_, _) =>
        {
            _searchDebounce.Stop();
            await SearchSuggestionsAsync();
        };

        // After the handlers are attached, so a restored value reaches the preview the same way a
        // typed one does.
        _prefs.Restoring = true;
        VideoSettings.Restore(_prefs);
        RestorePreferences();
        _prefs.Restoring = false;

        ApplyPreviewSettings();
    }

    protected override InfoBar StatusControl => Status;

    protected override string JobName => Strings.Get("StockVolumePageTitle.Text");

    // ---- the picture ------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        var showTitle = VideoSettings.ShowTitle;
        var typed = VideoSettings.TitleText;

        if (_series is { } series)
        {
            var plan = AnimationPlan.For(VideoSettings.Duration, series.Count, series.VolumePeak);

            Preview.Renderer = new StockDualRenderer(series, plan)
            {
                Title = typed,
                ShowTitle = showTitle,
                Code = series.Code,
            };
        }
        else
        {
            _stage.Title = typed.Length > 0 ? typed : Strings.Get("StockVolumeStageTitle");
            _stage.ShowTitle = showTitle;
            Preview.Renderer = _stage;
        }

        // Everything that needs a series is switched together, in the one place that knows whether
        // there is one. A button that is live over an empty frame reads as broken, not as "later".
        var ready = _series is not null;

        PlayButton.IsEnabled = ready;
        ExportButton.IsEnabled = ready;
        CoverButton.IsEnabled = ready;

        RefreshScrubText();
        Preview.Redraw();
    }

    // ---- search -----------------------------------------------------------------------

    private void OnSearchTextChanged(AutoSuggestBox sender, AutoSuggestBoxTextChangedEventArgs args)
    {
        // Only a typed change asks for suggestions. Choosing a suggestion assigns the text in
        // code, which would otherwise ask the source to suggest for the name just settled on.
        if (args.Reason is not AutoSuggestionBoxTextChangeReason.UserInput)
        {
            return;
        }

        _lastQuery = sender.Text;
        _searchDebounce.Stop();
        _searchDebounce.Start();
    }

    /// <summary>Suggestions while a person types; a code, a name or pinyin all resolve here.</summary>
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

            // Codes before names: what a person types first is usually a code, and the
            // venue prefix sorts the market's own venues to the top of the list.
            var ordered = found
                .OrderBy(r => r.Code.Length)
                .ThenBy(r => r.Code, StringComparer.Ordinal)
                .Take(12)
                .Select(r => new StockSuggestion(r.Code, r.Name, r.Code[..2].ToUpperInvariant()))
                .ToArray();

            StockSearch.ItemsSource = ordered;
        }
        catch (Exception)
        {
            // A failed suggestion list is a quiet failure by design: the person is still typing,
            // and a status line flashing under every keystroke is worse than no suggestions.
            StockSearch.ItemsSource = null;
        }
    }

    private void OnSuggestionChosen(AutoSuggestBox sender, AutoSuggestBoxSuggestionChosenEventArgs args)
    {
        // The choice is held rather than read from the submit event's args — this projection of
        // AutoSuggestBox does not carry ChosenItem there, and the field survives either way.
        if (args.SelectedItem is StockSuggestion chosen)
        {
            _pendingChoice = chosen;
            sender.Text = chosen.Display;
        }
    }

    private void OnSearchSubmitted(AutoSuggestBox sender, AutoSuggestBoxQuerySubmittedEventArgs args)
    {
        if (_pendingChoice is { } pick)
        {
            _pendingChoice = null;
            sender.Text = pick.Code;
            Fetch(pick.Code);
            return;
        }

        var code = StockDirectory.Normalize(sender.Text);

        if (code is null)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("StockBadCode"));
            return;
        }

        Fetch(code);
    }

    // ---- favourites -------------------------------------------------------------------

    /// <summary>Serialised as `code|name;…` — one settings key, parsed without a JSON dependency.</summary>
    private const string FavouriteKey = "Favourites";

    private void LoadFavourites()
    {
        var raw = _prefs.GetString(FavouriteKey, string.Empty);

        foreach (var item in raw.Split(';', StringSplitOptions.RemoveEmptyEntries))
        {
            var parts = item.Split('|');

            if (parts.Length == 2 && parts[0].Length > 0)
            {
                _favourites.Add(new StockFavourite(parts[0], parts[1]));
            }
        }
    }

    private void SaveFavourites()
    {
        _prefs.Save(FavouriteKey, string.Join(";", _favourites.Select(f => $"{f.Code}|{f.Name}")));
    }

    private void OnAddFavourite(object sender, RoutedEventArgs e)
    {
        if (_series is not { } series)
        {
            // The name is worth remembering alongside the code, and it is only in hand after a
            // fetch — a favourite without a name is a code nobody recognises later.
            ShowStatus(InfoBarSeverity.Informational, Strings.Get("StockFavNeedData"));
            return;
        }

        if (_favourites.Any(f => f.Code == series.Code))
        {
            return;
        }

        _favourites.Add(new StockFavourite(series.Code, series.Name));
        SaveFavourites();
    }

    private void OnFavouriteClick(object sender, RoutedEventArgs e)
    {
        if ((sender as FrameworkElement)?.Tag is string code)
        {
            StockSearch.Text = code;
            Fetch(code);
        }
    }

    private void OnFavouriteRemove(object sender, RoutedEventArgs e)
    {
        if ((sender as FrameworkElement)?.Tag is not string code)
        {
            return;
        }

        var at = _favourites.ToList().FindIndex(f => f.Code == code);

        if (at >= 0)
        {
            _favourites.RemoveAt(at);
            SaveFavourites();
        }
    }

    // ---- mode, range and day ------------------------------------------------------------

    private bool Intraday => IntradayMode.IsChecked is true;

    /// <summary>
    /// The two modes ask different questions of the source, so they need different controls rather
    /// than the same ones meaning different things. A multi-day span is chosen freely; a single
    /// day can only be one of the few the intraday endpoint still holds.
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
        TradingDayNote.Visibility = daily ? Visibility.Collapsed : Visibility.Visible;

        CustomRange.Visibility = daily && RangeCombo.SelectedItem is ComboBoxItem { Tag: 0 }
            ? Visibility.Visible
            : Visibility.Collapsed;

        // The series of one mode says nothing about the other's; keeping it would draw the
        // previous mode's picture under the new mode's controls.
        if (!_prefs.Restoring)
        {
            _series = null;
            ApplyPreviewSettings();
            ShowStatus(InfoBarSeverity.Informational, Strings.Get(daily ? "StockDailyHint" : "StockIntradayHint"));
            SavePreferences();
        }
    }

    private void OnRangeChanged(object sender, SelectionChangedEventArgs e)
    {
        // Raised by the selection assignment in the constructor, before the rest of the page's
        // controls have been reached.
        if (CustomRange is null || DailyMode is null)
        {
            return;
        }

        var custom = DailyMode.IsChecked is true && RangeCombo.SelectedItem is ComboBoxItem { Tag: 0 };
        CustomRange.Visibility = custom ? Visibility.Visible : Visibility.Collapsed;

        SavePreferences();
    }

    /// <summary>
    /// A day picked from the list the fetch filled. Not a re-fetch of the same day as the current
    /// series — that guard is what stops the selection the fetch itself makes from asking for the
    /// data it was just given.
    /// </summary>
    private void OnTradingDayChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_restoringDay || TradingDayCombo.SelectedItem is not ComboBoxItem { Tag: string day })
        {
            return;
        }

        if (_series is { } series && series.Day == day)
        {
            return;
        }

        Fetch(StockDirectory.Normalize(StockSearch.Text) ?? string.Empty, day);
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

    // ---- fetching -----------------------------------------------------------------------

    private void OnFetch(object sender, RoutedEventArgs e)
    {
        var code = StockDirectory.Normalize(StockSearch.Text);

        if (code is null)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("StockBadCode"));
            return;
        }

        Fetch(code);
    }

    private void Fetch(string code, string? day = null)
    {
        if (code.Length == 0)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("StockBadCode"));
            return;
        }

        // A favourite saved under another market, or a code typed with another venue's
        // prefix. The bars endpoint would answer either, which is the problem: the page
        // would quietly draw a market the setting says it is not on.
        if (!_market.Accepts(code))
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format("WrongMarket", _market.Name));
            return;
        }

        var intraday = Intraday;
        var (start, end) = ChosenRange();

        if (!intraday)
        {
            if (start >= end)
            {
                ShowStatus(InfoBarSeverity.Error, Strings.Get("TurnoverRangeReversed"));
                return;
            }

            // A count of days, and the ceiling is a count of bars. See
            // TencentKline.MostDaysPerRequest for why the two are not the same number and why the
            // day figure is the cautious one: 640 days was refusing a two-year span the endpoint
            // would have answered in full.
            if (end.DayNumber - start.DayNumber > TencentKline.MostDaysPerRequest)
            {
                ShowStatus(InfoBarSeverity.Error, Strings.Format("TurnoverRangeTooLong", TencentKline.MostDaysPerRequest));
                return;
            }
        }

        _ = RunAsync(FetchButton, async cancellation =>
        {
            var progress = new Progress<string>(message => ShowStatus(InfoBarSeverity.Informational, message));

            var series = intraday
                ? await StockSeries.LoadIntradayAsync(
                    Services.Http, Services.Stocks, _market, code, day, progress, cancellation)
                : await StockSeries.LoadDailyAsync(
                    Services.Quotes, Services.Stocks, _market, code, start, end, progress, cancellation);

            _series = series;

            StockSearch.Text = series.Code;
            ChosenText.Text = Strings.Format("StockChosen",
                Market.InstrumentNames.Display(series.Code, series.Name), series.Code.ToUpperInvariant());

            // The day list is filled from what the source actually holds, and the chosen day is
            // marked — without the guard this assignment would ask for the data just received.
            if (intraday && series.AvailableDays is { Count: > 0 } days)
            {
                _restoringDay = true;
                TradingDayCombo.Items.Clear();

                foreach (var id in days)
                {
                    TradingDayCombo.Items.Add(new ComboBoxItem
                    {
                        Content = id.Length >= 8 ? $"{id[4..6]}-{id[6..8]}" : id,
                        Tag = id,
                        IsSelected = id == series.Day,
                    });
                }

                _restoringDay = false;
            }

            ApplyPreviewSettings();

            // Parked on the last frame, the way the source tool does: the closing annotations are
            // what someone checks before deciding to export.
            ShowMoment(1);

            var suffix = series.HasRate ? string.Empty : " " + Strings.Get(series.RateIsCumulative ? "StockNoFloatShares" : "StockNoRate");

            ShowStatus(InfoBarSeverity.Success, series.RateIsCumulative
                ? Strings.Format("StockFetchedIntraday",
                    Market.InstrumentNames.Display(series.Code, series.Name), series.Code.ToUpperInvariant(), series.Count,
                    StockPanelSeries.Round(series.FinalRate, 2)) + suffix
                : Strings.Format("StockFetchedDaily",
                    Market.InstrumentNames.Display(series.Code, series.Name), series.Code.ToUpperInvariant(), series.Count,
                    StockPanelSeries.Round(series.VolumeAverage, series.VolumeDecimals),
                    series.VolumeUnit,
                    StockPanelSeries.Round(series.VolumePeak, series.VolumeDecimals),
                    StockPanelSeries.Round(series.RateAverage, 2),
                    StockPanelSeries.Round(series.RatePeak, 2)) + suffix);

            SavePreferences();
        }, TimeSpan.FromMinutes(2));
    }

    // ---- preview transport ---------------------------------------------------------------

    private void ShowMoment(double progress)
    {
        Preview.Progress = progress;

        // Detached for the assignment: the handler exists to stop playback when a person moves the
        // thumb, and playback moving it is not that.
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

    // ---- export --------------------------------------------------------------------------

    /// <summary>The file name both the video and the cover use: who, what and how big.</summary>
    private static string StockFileName(StockPanelSeries series, VideoFormat format, string extension) =>
        $"{Safe(series.Name)}_{series.Code}_{series.FileNameSpan}_{format.NameSuffix}.{extension}";

    private static string Safe(string label)
    {
        var safe = new string([.. label.Where(c => !Path.GetInvalidFileNameChars().Contains(c))]).Trim();

        return safe.Length > 40 ? safe[..40] : (safe.Length == 0 ? "stock" : safe);
    }

    private async void OnExport(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || _series is not { } series || App.Window is not { } window)
        {
            return;
        }

        var format = VideoSettings.Format;
        var margins = VideoSettings.Margins;
        var duration = VideoSettings.Duration;

        CancelButton.IsEnabled = true;

        var limit = TimeSpan.FromMinutes(5) + (duration * 4);

        Diagnostics.CrashLog.Note($"export: clicked, stock {series.Code} {format.Width}x{format.Height} dur={duration}");

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
                StockFileName(series, format, "mp4"),
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

    /// <summary>Saves the frame currently on screen as a full-resolution PNG.</summary>
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
                StockFileName(series, format, "png"),
                cancellation);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioCoverSaved", file.Name, format.Width, format.Height, folder.Path));
        }, TimeSpan.FromSeconds(90));
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();

    // ---- persistence -----------------------------------------------------------------------

    private void SavePreferences()
    {
        if (_prefs.Restoring)
        {
            return;
        }

        _prefs.Save("Code", StockSearch.Text);
        _prefs.Save("Intraday", Intraday);
        _prefs.Save("Months", RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } ? months : 3);
        _prefs.Save("From", FromDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("To", ToDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("Day", _series?.Day ?? string.Empty);
    }

    private void RestorePreferences()
    {
        LoadFavourites();

        var code = _prefs.GetString("Code", string.Empty);

        if (code.Length > 0)
        {
            StockSearch.Text = code;
        }

        // A saved preference for the intraday mode is honoured only where the minute
        // data exists: on a market without it the radio is not on screen and checking
        // it here would restore a mode the page has stopped offering.
        if (_market.Intraday && _prefs.GetBool("Intraday", false))
        {
            IntradayMode.IsChecked = true;
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
