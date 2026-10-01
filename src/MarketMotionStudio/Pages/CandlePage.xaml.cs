using System.Collections.ObjectModel;
using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// The candle page: one instrument's prices as candles, over a period and a span.
///
/// The question it is asked with is an instrument and a stretch of time — "show me
/// 贵州茅台's last three years" — and an index, a stock and an ETF are all answered
/// the same way, because the source quotes all three out of the same endpoint and
/// the chart draws what comes back.
///
/// Three of its controls re-fetch and four do not, and the line between them is
/// which one changes the *data*: the period and the span ask the source for a
/// different series, while the style, the motion, the window and the two overlays
/// ask the same bars a different question. Changing a second kind redraws without
/// a request, which is what makes flipping between the four styles something to
/// do while watching rather than something to wait for.
///
/// No renderer of its own pipeline: <see cref="CandleRenderer"/> draws the frames,
/// this page is a loader that turns a code and two terms into the series it draws —
/// the same split the other pages make.
/// </summary>
public sealed partial class CandlePage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    /// <summary>Remembers this page's parameters. Prefixed, because the video panel is shared.</summary>
    private readonly StudioPreferences _prefs = new("Candle.");

    /// <summary>The per-stock page's preferences container, used for the watchlist key only —
    /// one list shared by every page that names one instrument.</summary>
    private readonly StudioPreferences _watchlist = new("Stock.");

    private CandleSeries? _fetched;

    /// <summary>The market in force: it names the presets, it is what the search is
    /// filtered to, and its venue decides where the candles come from.</summary>
    private readonly MarketProfile _market = Markets.Of(MarketSettings.Current);

    private string _instrumentCode;

    private string _instrumentName = string.Empty;

    private StockSuggestion? _pendingChoice;

    private string _lastQuery = string.Empty;

    private readonly ObservableCollection<StockFavourite> _favourites = [];

    private readonly DispatcherTimer _searchDebounce = new() { Interval = TimeSpan.FromMilliseconds(260) };

    /// <summary>
    /// Whether the page is finished being built. The combo boxes raise
    /// <c>SelectionChanged</c> while the constructor is filling them, and a handler
    /// that fetched on the first assignment would start a request before there was
    /// an instrument to ask for.
    /// </summary>
    private bool _ready;

    public CandlePage()
    {
        InitializeComponent();

        foreach (var (period, key) in new[]
                 {
                     (CandlePeriod.Daily, "CandlePeriodDaily"),
                     (CandlePeriod.Weekly, "CandlePeriodWeekly"),
                     (CandlePeriod.Monthly, "CandlePeriodMonthly"),
                 })
        {
            PeriodCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = (int)period });
        }

        foreach (var (style, key) in new[]
                 {
                     (CandleStyle.Candles, "CandleStyleCandles"),
                     (CandleStyle.Bars, "CandleStyleBars"),
                     (CandleStyle.Line, "CandleStyleLine"),
                     (CandleStyle.Area, "CandleStyleArea"),
                 })
        {
            StyleCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = (int)style });
        }

        foreach (var (motion, key) in new[]
                 {
                     (CandleMotion.Grow, "CandleMotionGrow"),
                     (CandleMotion.Scroll, "CandleMotionScroll"),
                 })
        {
            MotionCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = (int)motion });
        }

        PeriodCombo.SelectedIndex = 0;
        StyleCombo.SelectedIndex = 0;
        MotionCombo.SelectedIndex = 0;

        FillRanges();

        foreach (var entry in _market.CandleInstruments)
        {
            Presets.Items.Add(new MatrixPreset(entry.Code, InstrumentNames.Display(entry.Code, entry.Name)));
        }

        Favourites.ItemsSource = _favourites;

        _searchDebounce.Tick += async (_, _) =>
        {
            _searchDebounce.Stop();
            await SearchSuggestionsAsync();
        };

        // The default the frame will actually use, before anything is fetched: the
        // market's own first one-tap instrument.
        _instrumentCode = _market.CandleInstruments[0].Code;
        _instrumentName = InstrumentNames.Display(
            _market.CandleInstruments[0].Code, _market.CandleInstruments[0].Name);

        VideoSettings.AllowHideTitle = true;
        VideoSettings.Changed += (_, _) =>
        {
            ApplyPreviewSettings();
            SavePreferences();
        };

        _stage.Subtitle = Strings.Get("StudioStageNoData");
        _stage.Credit = Strings.Get("StudioCredit");

        Preview.Renderer = _stage;

        _playback = new Playback(this);

        // Named before it has ever been pressed: the button is an icon, so the tooltip and
        // the name a screen reader announces are the only words it has.
        SetPlaybackState(playing: false);

        // After every control exists and every handler is attached, so a restored value
        // reaches the preview through the same path a typed one does.
        RestorePreferences();
        ApplyPreviewSettings();

        _ready = true;
    }

    protected override InfoBar StatusControl => Status;

    /// <summary>Reuses the page title as the job label, as the other pages do.</summary>
    protected override string JobName => Strings.Get("CandlePageTitle.Text");

    // ---- the choices --------------------------------------------------------------

    private static T Chosen<T>(ComboBox combo, T fallback) where T : struct, Enum =>
        combo.SelectedItem is ComboBoxItem { Tag: int value } ? (T)Enum.ToObject(typeof(T), value) : fallback;

    private CandlePeriod ChosenPeriod() => Chosen(PeriodCombo, CandlePeriod.Daily);

    private CandleStyle ChosenStyle() => Chosen(StyleCombo, CandleStyle.Candles);

    private CandleMotion ChosenMotion() => Chosen(MotionCombo, CandleMotion.Grow);

    private int ChosenMonths() =>
        RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } ? months : 12;

    /// <summary>
    /// How many candles a scrolling window holds.
    ///
    /// Clamped rather than trusted, and silently: a window of one candle is a chart
    /// with no chart in it, and a window wider than the series is the whole series,
    /// which is the other motion under a different name.
    /// </summary>
    private int ChosenWindow()
    {
        var text = WindowBox.Text.Trim();

        var window = int.TryParse(text, NumberStyles.Integer, CultureInfo.CurrentUICulture, out var parsed)
            ? parsed
            : int.TryParse(text, NumberStyles.Integer, CultureInfo.InvariantCulture, out parsed) ? parsed : 0;

        return Math.Clamp(window, 5, 360);
    }

    /// <summary>
    /// Rebuilds the span list for the period in force, keeping the same span where
    /// the new period offers it.
    ///
    /// A period's spans are its own: "ten years" is thirty-six monthly candles and
    /// two and a half thousand daily ones, and offering the latter would be offering
    /// a barcode fetched six requests at a time.
    ///
    /// The custom span is appended to every period's list, because two dates are a
    /// question every period can be asked. It carries
    /// <see cref="CandleLoader.CustomMonths"/> rather than a count so that it stays
    /// distinguishable from the monthly list's own "as far back as available", which
    /// is a span too.
    /// </summary>
    private void FillRanges()
    {
        var months = ChosenMonths();
        var ranges = CandleLoader.Ranges(ChosenPeriod());

        // Filling the list moves its selection, which raises SelectionChanged — and
        // that handler fetches. Without this the period change would start two
        // fetches, one from the list being rebuilt and one from its own handler,
        // and two runs reporting to one status line is a status line that stops
        // making sense.
        _filling = true;

        RangeCombo.Items.Clear();

        foreach (var range in ranges)
        {
            RangeCombo.Items.Add(
                new ComboBoxItem { Content = Strings.Get(range.Key), Tag = range.Months });
        }

        RangeCombo.Items.Add(
            new ComboBoxItem { Content = Strings.Get("StudioRangeCustom"), Tag = CandleLoader.CustomMonths });

        var at = ranges.ToList().FindIndex(r => r.Months == months);

        RangeCombo.SelectedIndex = at >= 0
            ? at
            : months == CandleLoader.CustomMonths ? ranges.Length : Math.Min(1, ranges.Length - 1);

        _filling = false;
    }

    /// <summary>The two dates in the pickers. The span in force only when custom is chosen.</summary>
    private (DateOnly From, DateOnly To) CustomSpan() =>
        (DateOnly.FromDateTime(FromDate.Date.DateTime), DateOnly.FromDateTime(ToDate.Date.DateTime));

    /// <summary>Whether <see cref="FillRanges"/> is rebuilding the list; see there.</summary>
    private bool _filling;

    // ---- preview ---------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        var title = ResolvedTitle();
        var showTitle = VideoSettings.ShowTitle;

        if (_fetched is { } fetched)
        {
            var plan = AnimationPlan.For(VideoSettings.Duration, fetched.Count, fetched.High);

            Preview.Renderer = new CandleRenderer(
                fetched, plan, ChosenStyle(), ChosenMotion(), ChosenWindow(),
                AveragesCheck.IsChecked is true, VolumeCheck.IsChecked is true)
            {
                Title = title,
                ShowTitle = showTitle,
            };
        }
        else
        {
            _stage.Title = title;
            _stage.ShowTitle = showTitle;
            Preview.Renderer = _stage;
        }

        VideoSettings.TitlePlaceholder = Strings.Format(
            "CandleDefaultTitle", _instrumentName, Strings.Get(CandleLoader.NameKey(ChosenPeriod())));

        // The window is a term of the scrolling motion alone; offered at any other
        // time it reads as a setting the chart is ignoring.
        WindowBox.IsEnabled = ChosenMotion() is CandleMotion.Scroll;

        var ready = _fetched is not null;

        PlayButton.IsEnabled = ready;
        ExportButton.IsEnabled = ready;
        CoverButton.IsEnabled = ready;

        RefreshScrubText();
        Preview.Redraw();
    }

    /// <summary>
    /// The title the frame will draw: the typed one, or the default naming the current
    /// instrument and period.
    /// </summary>
    private string ResolvedTitle() =>
        VideoSettings.TitleText.Length > 0
            ? VideoSettings.TitleText
            : Strings.Format("CandleDefaultTitle", _instrumentName,
                Strings.Get(CandleLoader.NameKey(ChosenPeriod())));

    // ---- search ----------------------------------------------------------------------

    private void OnSearchTextChanged(AutoSuggestBox sender, AutoSuggestBoxTextChangedEventArgs args)
    {
        // Only a typed change asks for suggestions; choosing one assigns the text in code.
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
            InstrumentSearch.ItemsSource = null;
            return;
        }

        try
        {
            var found = await Services.Stocks.SearchAsync(query, _market, CancellationToken.None);

            var ordered = found
                .Where(r => _market.Accepts(r.Code))
                .Take(12)
                .Select(r => new StockSuggestion(r.Code, r.Name, r.Code[..2].ToUpperInvariant()))
                .ToArray();

            InstrumentSearch.ItemsSource = ordered;
        }
        catch (Exception)
        {
            // A failed suggestion list is a quiet failure: the person is still typing.
            InstrumentSearch.ItemsSource = null;
        }
    }

    private void OnSuggestionChosen(AutoSuggestBox sender, AutoSuggestBoxSuggestionChosenEventArgs args)
    {
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
            ChooseInstrument(pick.Code, pick.Name);
            return;
        }

        var code = StockDirectory.Normalize(sender.Text);

        if (code is null)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("StockBadCode"));
            return;
        }

        if (!_market.Accepts(code))
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format("WrongMarket", _market.Name));
            return;
        }

        ChooseInstrument(code, code);
    }

    private void OnPresetClick(object sender, RoutedEventArgs e)
    {
        if ((sender as FrameworkElement)?.Tag is string code)
        {
            var name = Presets.Items.OfType<MatrixPreset>().FirstOrDefault(p => p.Code == code)?.Name ?? code;
            ChooseInstrument(code, name);
        }
    }

    // ---- favourites ------------------------------------------------------------------

    /// <summary>Serialised as `code|name;…` under the shared watchlist key — see <see cref="_watchlist"/>.</summary>
    private const string FavouriteKey = "Favourites";

    private void LoadFavourites()
    {
        var raw = _watchlist.GetString(FavouriteKey, string.Empty);

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
        _watchlist.Save(FavouriteKey, string.Join(";", _favourites.Select(f => $"{f.Code}|{f.Name}")));
    }

    private void OnAddFavourite(object sender, RoutedEventArgs e)
    {
        if (_fetched is not { } fetched)
        {
            ShowStatus(InfoBarSeverity.Informational, Strings.Get("StockFavNeedData"));
            return;
        }

        if (_favourites.Any(f => f.Code == fetched.Code))
        {
            return;
        }

        _favourites.Add(new StockFavourite(fetched.Code, fetched.Name));
        SaveFavourites();
    }

    private void OnFavouriteClick(object sender, RoutedEventArgs e)
    {
        if ((sender as FrameworkElement)?.Tag is string code)
        {
            var name = _favourites.FirstOrDefault(f => f.Code == code)?.Name ?? code;
            ChooseInstrument(code, name);
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

    // ---- fetching --------------------------------------------------------------------

    private void ChooseInstrument(string code, string name)
    {
        _instrumentCode = code;
        _instrumentName = InstrumentNames.Display(code, name);

        // The candles in the frame belong to the instrument they were fetched for. A
        // new pick drops them rather than leaving them standing under a title that no
        // longer names them.
        _fetched = null;
        ApplyPreviewSettings();

        Fetch();
    }

    private void OnPeriodChanged(object sender, SelectionChangedEventArgs e)
    {
        if (!_ready)
        {
            return;
        }

        // A new period is a new series, so the spans on offer change with it.
        FillRanges();
        SavePreferences();

        Fetch();
    }

    private void OnRangeChanged(object sender, SelectionChangedEventArgs e)
    {
        // Raised while the constructor fills the list, before CustomRange has been
        // reached by it — the same null check the other pages carry, for the same reason.
        if (CustomRange is null)
        {
            return;
        }

        // Set before the guard below rather than after it: restoring a saved custom span
        // selects an entry while the page is still unready, and the two pickers have to
        // come up with it.
        CustomRange.Visibility = ChosenMonths() == CandleLoader.CustomMonths
            ? Visibility.Visible
            : Visibility.Collapsed;

        if (!_ready || _filling)
        {
            return;
        }

        SavePreferences();
        Fetch();
    }

    /// <summary>
    /// A change to how the fetched bars are drawn. Nothing here asks the source for
    /// anything, so nothing here fetches: the four styles, the two motions, the
    /// window's width and the two overlays are all readings of one series.
    /// </summary>
    private void OnLookChanged(object sender, object e)
    {
        if (!_ready)
        {
            return;
        }

        ApplyPreviewSettings();
        SavePreferences();
    }

    private async void Fetch()
    {
        var display = _instrumentName.Length > 0 ? _instrumentName : _instrumentCode;
        var period = ChosenPeriod();
        var months = ChosenMonths();
        var custom = months == CandleLoader.CustomMonths;
        var (from, to) = custom ? CustomSpan() : default;

        // A custom span is the only one that can be wrong in a way the source would
        // answer badly — it would report "too few days" for dates in the wrong order,
        // and for a span past what one walk holds it would answer with the newest
        // candles alone, which draws a chart that is short by its first years and looks
        // like a chart. Both are refused here, before a request is made.
        if (custom)
        {
            if (from >= to)
            {
                ShowStatus(InfoBarSeverity.Error, Strings.Get("TurnoverRangeReversed"));
                return;
            }

            if (CandleLoader.WantedFor(period, from, to) > CandleLoader.MostCandles)
            {
                ShowStatus(InfoBarSeverity.Error, Strings.Format(
                    "CandleRangeTooLong",
                    Strings.Get(CandleLoader.NameKey(period)),
                    CandleLoader.MostCandles));

                return;
            }
        }

        // Three minutes: a daily chart three years back is two requests, and a
        // monthly one reaching forty is one, but a slow answer should not be
        // indistinguishable from a hang.
        await RunAsync(FetchButton, async cancellation =>
        {
            // Reported straight through rather than through Progress<T>, which posts
            // its callback to the dispatcher. Posted, the callback the loader makes in
            // its last loop pass lands *after* the success line this block ends with —
            // and the status bar finishes on "0:120 …" for a fetch that worked. The
            // whole walk already runs on the UI thread, so there is nothing to marshal.
            var progress = new Immediate<string>(
                message => ShowStatus(InfoBarSeverity.Informational, message));

            var fetched = custom
                ? await CandleLoader.LoadAsync(
                    Services.Quotes, _instrumentCode, display, period, from, to, progress, cancellation)
                : await CandleLoader.LoadAsync(
                    Services.Quotes, _instrumentCode, display, period, months, progress, cancellation);

            _fetched = fetched;
            _instrumentName = InstrumentNames.Display(fetched.Code, fetched.Name);

            ApplyPreviewSettings();

            // Parked on the last frame: the closing figures are what someone wants to
            // look at before deciding whether to export.
            ShowMoment(1);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "CandleFetched",
                fetched.Count,
                Strings.Get(CandleLoader.NameKey(period)),
                CandleLoader.Iso(fetched.Start),
                CandleLoader.Iso(fetched.End)));
        }, TimeSpan.FromMinutes(3));
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
        // reads as a broken one. Starting again is what the press meant.
        //
        // Through the seek rather than by setting the preview's progress directly, so that
        // the position playback counts from is the position the picture is showing.
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
    /// </summary>
    private void SetPlaybackState(bool playing)
    {
        var label = Strings.Get(playing ? "StudioPause.Content" : "StudioPlay.Content");

        PlayIcon.Glyph = playing ? "\uE769" : "\uE768";

        ToolTipService.SetToolTip(PlayButton, label);
        Microsoft.UI.Xaml.Automation.AutomationProperties.SetName(PlayButton, label);
    }

    TimeSpan IPlaybackHost.PlaybackDuration => VideoSettings.Duration;

    // ---- export ---------------------------------------------------------------------

    private async void OnExport(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || _fetched is not { } fetched || App.Window is not { } window)
        {
            return;
        }

        // Read before the work starts, so touching a slider mid-export cannot change the
        // format halfway through the file.
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
                VideoExporter.VideoName(label, fetched.Start, fetched.End, format),
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
        if (Preview.Renderer is not { } renderer || _fetched is not { } fetched || App.Window is not { } window)
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
                FrameExporter.CoverName(ResolvedTitle(), fetched.Start, fetched.End, format),
                cancellation);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioCoverSaved", file.Name, format.Width, format.Height, folder.Path));
        }, TimeSpan.FromSeconds(90));
    }

    // ---- preferences -----------------------------------------------------------------

    private void RestorePreferences()
    {
        _prefs.Restoring = true;

        Select(PeriodCombo, _prefs.GetInt("Period", 0));
        Select(StyleCombo, _prefs.GetInt("Style", 0));
        Select(MotionCombo, _prefs.GetInt("Motion", 0));

        // The span list belongs to the period, so it is filled from the restored
        // period and then the restored span is looked for among what it offers.
        FillRanges();
        Select(RangeCombo, _prefs.GetInt("Months", 12));

        // A year, so the two pickers say something sensible the first time the custom span
        // is chosen instead of opening on today and today.
        var today = DateTimeOffset.Now;
        FromDate.Date = today.AddYears(-1);
        ToDate.Date = today;

        if (DateOnly.TryParse(_prefs.GetString("From", string.Empty), out var from))
        {
            FromDate.Date = new DateTimeOffset(from, TimeOnly.MinValue, TimeSpan.Zero);
        }

        if (DateOnly.TryParse(_prefs.GetString("To", string.Empty), out var to))
        {
            ToDate.Date = new DateTimeOffset(to, TimeOnly.MinValue, TimeSpan.Zero);
        }

        WindowBox.Text = Math.Clamp(_prefs.GetInt("Window", 60), 5, 360)
            .ToString(CultureInfo.InvariantCulture);

        AveragesCheck.IsChecked = _prefs.GetInt("Averages", 1) != 0;
        VolumeCheck.IsChecked = _prefs.GetInt("Volume", 1) != 0;

        var code = _prefs.GetString("Code", _market.CandleInstruments[0].Code);

        // A code saved under another market is not carried over: it would fetch from a
        // venue whose presets and search results this page no longer shows.
        if (_market.Accepts(code))
        {
            _instrumentCode = code;

            // The stored name is only a hint: the code decides.
            var name = _prefs.GetString("Name", string.Empty);

            _instrumentName = InstrumentNames.Display(code, name.Length > 0 ? name : code);
        }

        VideoSettings.Restore(_prefs);
        LoadFavourites();

        _prefs.Restoring = false;
    }

    private void SavePreferences()
    {
        _prefs.Save("Period", (int)ChosenPeriod());
        _prefs.Save("Style", (int)ChosenStyle());
        _prefs.Save("Motion", (int)ChosenMotion());
        _prefs.Save("Months", ChosenMonths());
        _prefs.Save("From", FromDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("To", ToDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("Window", ChosenWindow());
        _prefs.Save("Averages", AveragesCheck.IsChecked is true ? 1 : 0);
        _prefs.Save("Volume", VolumeCheck.IsChecked is true ? 1 : 0);
        _prefs.Save("Code", _instrumentCode);
        _prefs.Save("Name", _instrumentName);

        VideoSettings.Save(_prefs);
    }

    /// <summary>
    /// Picks a combo box's entry by the identifier it carries rather than by position.
    ///
    /// The stored value is the enumeration's number, and a list whose entries are
    /// fewer than the enumeration — or whose order differs — would silently answer a
    /// different question if the number were used as an index.
    /// </summary>
    private static void Select(ComboBox combo, int tag)
    {
        var at = combo.Items.OfType<ComboBoxItem>().ToList().FindIndex(i => i.Tag is int value && value == tag);

        if (at >= 0)
        {
            combo.SelectedIndex = at;
        }
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();

    /// <summary>
    /// An <see cref="IProgress{T}"/> that calls back where it was reported from.
    ///
    /// <see cref="Progress{T}"/> captures the context it was built on and posts, which
    /// is the right thing when the work is on a pool thread and the report is not the
    /// last word. Here the work is already on the UI thread and the report can be the
    /// last word, so posting reorders it against the line that follows.
    /// </summary>
    private sealed class Immediate<T>(Action<T> report) : IProgress<T>
    {
        public void Report(T value) => report(value);
    }
}
