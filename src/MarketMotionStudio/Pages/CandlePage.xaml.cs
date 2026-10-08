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

    /// <summary>
    /// Every session the minute endpoint returned, while the period is a minute one.
    ///
    /// Kept because the day control is filled from it: the source answers with the last
    /// several sessions and takes no dates, so the days on offer are only knowable from
    /// the one request — and choosing another of them is then a redraw rather than a
    /// second fetch.
    /// </summary>
    private MinuteSession? _minutes;

    /// <summary>
    /// Several instruments on one frame, once more than one is picked.
    ///
    /// Kept beside <see cref="_fetched"/> rather than instead of it: the two are different
    /// pictures of the same question and the page holds whichever was fetched last, so
    /// dropping back to one instrument drops this and not the other way round.
    /// </summary>
    private CandleBoard? _board;

    /// <summary>
    /// Whether the reader has touched the shared list on this page. Until they have, the
    /// page is the single-instrument one it always was and the list is only a row of
    /// names — a list shared with four other boards cannot be allowed to decide what this
    /// page fetches before anyone here has said anything about it.
    /// </summary>
    private bool _watchTouched;

    /// <summary>Which of those sessions is drawn, as the source names it, `20260930`.</summary>
    private string _day = string.Empty;

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
                     (CandlePeriod.Minute1, "CandlePeriodMinute1"),
                     (CandlePeriod.Minute5, "CandlePeriodMinute5"),
                     (CandlePeriod.Minute15, "CandlePeriodMinute15"),
                 })
        {
            var item = new ComboBoxItem { Content = Strings.Get(key), Tag = (int)period };

            // Switched off, on the markets where the source keeps no minute candles at
            // all — Hong Kong and New York among them. Not left out: a list that changes
            // length between markets asks "where did the others go", and three entries
            // that can only ever fail are worse than three that say why they are off.
            if (CandleLoader.IsMinute(period) && !_market.MinuteCandles)
            {
                item.IsEnabled = false;

                ToolTipService.SetToolTip(item, Strings.Get("CandleMinuteMarketNone"));
            }

            PeriodCombo.Items.Add(item);
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

        foreach (var (split, key) in new[]
                 {
                     (CandleSplit.Together, "CandleSplitTogether"),
                     (CandleSplit.Apart, "CandleSplitApart"),
                 })
        {
            SplitCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = (int)split });
        }

        PeriodCombo.SelectedIndex = 0;
        StyleCombo.SelectedIndex = 0;
        MotionCombo.SelectedIndex = 0;
        SplitCombo.SelectedIndex = 0;

        FillRanges();

        foreach (var entry in _market.CandleInstruments)
        {
            Presets.Items.Add(new MatrixPreset(entry.Code, InstrumentNames.Display(entry.Code, entry.Name)));
        }

        Favourites.ItemsSource = _favourites;

        // The shared list, read by this page only once a chip has been switched here — see
        // `_watchTouched` — because it is one list behind five boards, and a pick made on
        // another of them is not a request about this one.
        Watchlist.EnsureLoaded();

        Watch.Changed += OnWatchChanged;
        Watch.Notice += message => ShowStatus(InfoBarSeverity.Error, message);

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

    private CandleSplit ChosenSplit() => Chosen(SplitCombo, CandleSplit.Together);

    /// <summary>
    /// Whether the picture may run into the band the platform's own button rail covers. Read by
    /// both pictures this page draws — see <see cref="CandleRenderer"/> and
    /// <see cref="CandleRaceRenderer"/> — because both of them put ink in that band.
    /// </summary>
    private bool CrossSafeRight() => CrossCheck.IsChecked is true;

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
        var minute = CandleLoader.IsMinute(ChosenPeriod());

        // How far back, and which session, are the same question asked of two kinds of
        // period: the daily ones are asked for a span and the minute ones for a day,
        // because the minute endpoint takes no dates and keeps the last few sessions.
        // Swapped by visibility rather than by emptying a list, so no empty control is
        // left standing on the panel.
        RangeCombo.Visibility = minute ? Visibility.Collapsed : Visibility.Visible;
        DayCombo.Visibility = minute ? Visibility.Visible : Visibility.Collapsed;
        DayNote.Visibility = DayCombo.Visibility;
        CustomRange.Visibility = Visibility.Collapsed;

        if (minute)
        {
            return;
        }

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

    /// <summary>
    /// Fills the day control from what is on the frame, keeping the one being drawn where the
    /// new list still has it.
    ///
    /// Two sources and one question. One instrument is drawn on a session the source holds for
    /// it; a comparison on a day all of its instruments have, and only those — offering one the
    /// others lack would draw a board with a hole in it. Both lists are days that arrived with
    /// the fetch, so moving between them is a redraw and nothing else.
    ///
    /// Only whole sessions are offered. A part-day is a chart missing its own opening,
    /// and it would sit in the list as an ordinary date: nothing about the entry would
    /// say it starts at ten to eleven.
    /// </summary>
    private void FillDays()
    {
        IReadOnlyList<MinuteDay> offered = _minutes is { } session ? session.Whole : _board?.Days ?? [];

        _filling = true;

        DayCombo.Items.Clear();

        foreach (var day in offered)
        {
            DayCombo.Items.Add(new ComboBoxItem
            {
                Content = CandleLoader.Iso(day.Date),
                Tag = day.Id,
            });
        }

        var at = offered.ToList().FindIndex(d => d.Id == _day);

        // The newest, when the one being drawn is not among them: a preference saved
        // on another day is a preference for a day the source has since dropped, and
        // the latest session is the nearest thing to it.
        DayCombo.SelectedIndex = offered.Count == 0 ? -1 : at >= 0 ? at : offered.Count - 1;

        _filling = false;
    }

    /// <summary>The session chosen in the control, or null when there is none.</summary>
    private MinuteDay? ChosenDay() =>
        _minutes is { } session && DayCombo.SelectedItem is ComboBoxItem { Tag: string id }
            ? session.Find(id)
            : null;

    /// <summary>
    /// Draws the session chosen, or the latest whole one.
    ///
    /// Not a fetch, on either picture: every day in the list arrived in the same request, so
    /// moving between them costs a redraw and the preview follows the control as it is used.
    /// </summary>
    private void ApplyDay()
    {
        var id = DayCombo.SelectedItem is ComboBoxItem { Tag: string chosen } ? chosen : string.Empty;

        if (_minutes is { } session)
        {
            var day = ChosenDay() ?? session.Latest;

            _day = day.Id;
            _fetched = CandleMinutes.ForDay(session, day);
        }
        else if (_board is { } board && id.Length > 0)
        {
            _day = id;
            _board = CandleBoardLoader.On(board, id);
        }
        else
        {
            return;
        }

        ApplyPreviewSettings();
    }

    private void OnDayChanged(object sender, SelectionChangedEventArgs e)
    {
        if (!_ready || _filling || (_minutes is null && _board is null))
        {
            return;
        }

        ApplyDay();

        // Parked on the last frame, as a fresh fetch is: the day's closing figures are
        // what someone looks at before deciding whether to export.
        ShowMoment(1);

        SavePreferences();
    }

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

        if (_board is { } board)
        {
            // Split into panels, the frame is about at most three of them: the picks past the
            // third are not drawn, and — this is the part that has to be done here rather than in
            // the renderer — they are dropped from the **board** as well, so that the axis the
            // panels are read against is the union of the days the *drawn* instruments traded.
            // A board still carrying them would stretch the dates to cover an instrument with no
            // panel, and the picture would be short by its own left-hand third for no visible
            // reason. Rebuilt from the series in hand: a redraw, not a fetch.
            var split = ChosenSplit() is CandleSplit.Apart;
            var drawn = split ? CandleBoardLoader.Only(board, CandleBoardLoader.MostPanels) : board;

            // The axis reaches as far as the furthest any curve got, either way: returns go
            // down as well as up, and an axis scaled to the rises alone would draw the falls
            // off the bottom of the plot.
            var plan = AnimationPlan.For(
                VideoSettings.Duration, drawn.Count,
                Math.Max(Math.Abs(drawn.Peak), Math.Abs(drawn.Trough)));

            Preview.Renderer = split
                ? new CandleSplitRenderer(
                    drawn, plan, ChosenMotion(), ChosenWindow(), CrossSafeRight())
                {
                    Title = title,
                    ShowTitle = showTitle,
                }
                : new CandleRaceRenderer(
                    drawn, plan, ChosenMotion(), ChosenWindow(), CrossSafeRight())
                {
                    Title = title,
                    ShowTitle = showTitle,
                };
        }
        else if (_fetched is { } fetched)
        {
            var plan = AnimationPlan.For(VideoSettings.Duration, fetched.Count, fetched.High);

            Preview.Renderer = new CandleRenderer(
                fetched, plan, ChosenStyle(), ChosenMotion(), ChosenWindow(),
                AveragesCheck.IsChecked is true, VolumeCheck.IsChecked is true, CrossSafeRight())
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

        VideoSettings.TitlePlaceholder = _board is { } comparing
            ? string.Join(" / ", comparing.Tracks.Select(t => t.Name))
            : Strings.Format("CandleDefaultTitle", _instrumentName,
                Strings.Get(CandleLoader.NameKey(ChosenPeriod())));

        // The window is a term of the scrolling motion alone; offered at any other
        // time it reads as a setting the chart is ignoring.
        WindowBox.IsEnabled = ChosenMotion() is CandleMotion.Scroll;

        // A day control with no days in it is not a choice: before the first fetch there are
        // none to offer, and greyed it says so instead of standing there looking broken.
        // Filled by the fetch, by whichever of the two pictures it is.
        DayCombo.IsEnabled = DayCombo.Items.Count > 0;

        // Three more that a comparison does not read: the four styles are ways of drawing
        // *candles*, and a frame of percentages has none, while the averages and the volume
        // belong to one instrument's bars. Offered anyway they would be three settings the
        // frame was silently ignoring — the thing the window box above is guarded against.
        StyleCombo.IsEnabled = _board is null;
        AveragesCheck.IsEnabled = _board is null;
        VolumeCheck.IsEnabled = _board is null;

        // The layout, on the other hand, is a comparison's own setting — one instrument is one
        // chart however it is arranged. Its note goes with it, and only while there is a panel per
        // instrument to explain: the limit of three is not a fact about the overlaid frame.
        SplitCombo.IsEnabled = _board is not null;
        SplitNote.Visibility = _board is not null && ChosenSplit() is CandleSplit.Apart
            ? Visibility.Visible
            : Visibility.Collapsed;

        var ready = _fetched is not null || _board is not null;

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
            : _board is { } board
                ? string.Join(" / ", board.Tracks.Select(t => t.Name))
                : Strings.Format("CandleDefaultTitle", _instrumentName,
                    Strings.Get(CandleLoader.NameKey(ChosenPeriod())));

    /// <summary>
    /// The span the frame covers — the dates an export is named after — or null when the
    /// frame is the placeholder and there is nothing to write.
    ///
    /// <para>
    /// **One place, because this page is the only one that draws two pictures from two
    /// fields.** Sixteen other pages have a single source and ask about that one; here the
    /// comparison keeps a board and clears the series, on purpose, and the two agree on
    /// nothing but these two dates. Each export handler asking about the series alone
    /// therefore returned without a word on every comparison: the button was enabled (its
    /// enablement is `_fetched is not null || _board is not null`), a finished frame was on
    /// screen, and pressing it did nothing at all. That is how "导出 MP4 没反应" arrives —
    /// no dialog, no status line, no file, and no fault in the log.
    /// </para>
    ///
    /// <para>
    /// Both are read here rather than in each handler so that the guard and the button can
    /// never disagree: every path that clears one of these fields calls
    /// <see cref="ApplyPreviewSettings"/> on the way out, which is where both are decided.
    /// </para>
    /// </summary>
    private (DateOnly Start, DateOnly End)? FrameSpan =>
        _board is { } board
            ? (board.Start, board.End)
            : _fetched is { } fetched
                ? (fetched.Start, fetched.End)
                : null;

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

    /// <summary>
    /// What this frame is about: the instruments switched on in the shared list, or — until
    /// the reader has switched any — the one the page is naming.
    /// </summary>
    private IReadOnlyList<RaceEntry> Chosen() =>
        _watchTouched
            ? Watch.SelectedEntries
            : _instrumentCode.Length > 0
                ? [new RaceEntry(_instrumentCode, _instrumentName)]
                : [];

    /// <summary>
    /// A chip switched on or off: what the frame is about has changed, and what was last
    /// fetched no longer answers to it.
    ///
    /// Nothing is fetched here. A chip is a switch and a reader deciding between four
    /// instruments clicks four of them, and four requests for the three states passed
    /// through on the way would be three requests about a picture nobody asked to see.
    /// The fetch is the button's, as it is everywhere else on this page.
    /// </summary>
    private void OnWatchChanged(object? sender, EventArgs e)
    {
        _watchTouched = true;
        _fetched = null;
        _board = null;
        _minutes = null;
        _day = string.Empty;

        DayCombo.Items.Clear();

        SavePreferences();
        ApplyPreviewSettings();
    }

    private void ChooseInstrument(string code, string name)
    {
        _instrumentCode = code;
        _instrumentName = InstrumentNames.Display(code, name);

        // Onto the shared list, and switched on for this frame in one press — a pick that
        // arrived on the list but switched off would draw nothing at all, which reads as a
        // broken row rather than as a setting. Which is also why a press here counts as
        // having touched the list: from this point the chips are what the page fetches.
        if (!Watchlist.Has(code) && !Watchlist.Add(code, name))
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format("SectorTooManyStocks", Watchlist.Most));
        }
        else
        {
            _watchTouched = true;
            Watch.Include(code);
        }

        // The candles in the frame belong to the instrument they were fetched for. A
        // new pick drops them rather than leaving them standing under a title that no
        // longer names them — and drops the sessions with them, because the day list is
        // one instrument's days. A comparison goes with them: one instrument chosen by
        // name is the single-instrument page again.
        _fetched = null;
        _board = null;
        _minutes = null;
        _day = string.Empty;

        DayCombo.Items.Clear();

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
        //
        // And only while the period actually asks for a span. A minute period takes no dates
        // at all — its days are the ones the source still holds, and they are chosen from the
        // list below — so a saved custom span would leave two date pickers on the panel that
        // the fetch never reads, right underneath the control that replaced them.
        CustomRange.Visibility = ChosenMonths() == CandleLoader.CustomMonths
            && !CandleLoader.IsMinute(ChosenPeriod())
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

        var chosen = Chosen();

        if (chosen.Count == 0)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("CandlePickNone"));
            return;
        }

        // Refused rather than trimmed, for the reason every other board refuses it: a
        // frame drawn from six of the nine instruments somebody ticked answers about a
        // list nobody chose, and looks entirely plausible while it does.
        if (chosen.Count > CandleBoardLoader.MostTracks)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format(
                "SectorTooManyStocks", CandleBoardLoader.MostTracks));

            return;
        }

        // More than one instrument is a different picture, not a bigger one: their prices
        // have no common axis, so the frame draws what each did as a percentage instead.
        // Taken here, before the single-instrument path below, because both paths ask the
        // source the same questions about the period and the span and both refusals above
        // are the same for either.
        if (chosen.Count > 1)
        {
            await FetchComparison(chosen, months, from, to);

            return;
        }

        _instrumentCode = chosen[0].Code;
        _instrumentName = InstrumentNames.Display(chosen[0].Code, chosen[0].Name);

        var display = _instrumentName.Length > 0 ? _instrumentName : _instrumentCode;

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

            if (CandleLoader.IsMinute(period))
            {
                var session = await CandleMinutes.LoadAsync(
                    Services.Quotes, _instrumentCode, display, period, progress, cancellation);

                if (session.Whole.Count == 0)
                {
                    // Nothing came back whole: the sessions the source still holds are
                    // the one running now, or one cut in half by the request's own
                    // length. Drawing either would be a day missing its own opening,
                    // presented as a day.
                    ShowStatus(InfoBarSeverity.Error, Strings.Get("CandleMinuteNoWhole"));
                    return;
                }

                _minutes = session;

                FillDays();
                ApplyDay();
                ShowMoment(1);

                var drawn = _fetched!;

                ShowStatus(InfoBarSeverity.Success, Strings.Format(
                    "CandleMinuteFetched",
                    drawn.Name,
                    CandleLoader.Iso(drawn.Start),
                    drawn.Count,
                    session.Whole.Count));

                return;
            }

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

    /// <summary>
    /// Several instruments' candles on one frame.
    ///
    /// Asked for as one board rather than as N charts, because the axis is the thing they
    /// have to share: two instruments fetched separately and drawn together is only a
    /// comparison if each point on one answers to the same moment on the other, and that
    /// is decided where the bars are put on the axis, not where they are painted.
    /// </summary>
    private async Task FetchComparison(
        IReadOnlyList<RaceEntry> chosen, int months, DateOnly from, DateOnly to)
    {
        var period = ChosenPeriod();

        // Six minutes, not the single-instrument path's three: one instrument reaching back
        // a dozen years is up to six requests answered one after another, and this path asks
        // for as many as six of them.
        await RunAsync(FetchButton, async cancellation =>
        {
            var progress = new Immediate<string>(
                message => ShowStatus(InfoBarSeverity.Informational, message));

            var board = await CandleBoardLoader.LoadAsync(
                Services.Quotes, chosen, period, months, from, to, progress, cancellation, _day);

            if (board.Tracks.Count < 2)
            {
                // Fewer than two came back, so there is nothing to compare: a "comparison"
                // of one curve is a single-instrument chart under a title that says
                // otherwise, and of none is an empty frame. Named rather than counted —
                // which instrument the period could not supply is what has to be acted on.
                ShowStatus(InfoBarSeverity.Error, Strings.Format(
                    "PositionSkipped", board.Skipped.Count, string.Join(", ", board.Skipped)));

                return;
            }

            _board = board;

            // The single-instrument series is dropped rather than kept alongside: the frame
            // is one or the other, and a stale chart standing behind a comparison would be
            // drawn the moment the reader dropped back to one pick.
            _fetched = null;
            _minutes = null;

            // And the day control follows the board rather than being emptied. A comparison
            // is drawn on one day, and the days on offer are the ones all of these
            // instruments have: left blank it was a control standing there promising a
            // choice it was not offering.
            _day = board.Drawn?.Id ?? string.Empty;

            FillDays();

            ApplyPreviewSettings();

            ShowMoment(1);

            var fetched = Strings.Format(
                "CandleFetched",
                board.Count,
                Strings.Get(CandleLoader.NameKey(period)),
                CandleLoader.Iso(board.Start),
                CandleLoader.Iso(board.End));

            // Picked past the third, in the layout that draws one panel per instrument: drawn,
            // they would be a fourth panel on top of one of the other three, so they are left out
            // of the picture — and said out loud here rather than left for the reader to notice by
            // counting the panels. Named, like the instruments the period could not supply: which
            // ones are missing is what has to be acted on.
            var beyond = ChosenSplit() is CandleSplit.Apart
                ? board.Tracks.Skip(CandleBoardLoader.MostPanels).Select(track => track.Name).ToList()
                : [];

            var notes = new List<string>();

            if (board.Skipped.Count > 0)
            {
                notes.Add(Strings.Format(
                    "PositionSkipped", board.Skipped.Count, string.Join(", ", board.Skipped)));
            }

            if (beyond.Count > 0)
            {
                notes.Add(Strings.Format(
                    "CandleSplitTrimmed", CandleBoardLoader.MostPanels, string.Join(", ", beyond)));
            }

            ShowStatus(
                notes.Count == 0 ? InfoBarSeverity.Success : InfoBarSeverity.Warning,
                notes.Count == 0 ? fetched : $"{fetched} {string.Join(" ", notes)}");
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
        // Asked of `FrameSpan`, not of the series: the comparison is a board and clears the
        // series on purpose, so a guard reading `_fetched` turned every press on a comparison
        // into a silent return. See the note on `FrameSpan`.
        if (Preview.Renderer is not { } renderer || FrameSpan is not { } span || App.Window is not { } window)
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
                VideoExporter.VideoName(label, span.Start, span.End, format),
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
        // The same guard as the video's, for the same reason — a cover of a comparison was
        // equally silent, and the cover is the one export with no subscription in front of it.
        if (Preview.Renderer is not { } renderer || FrameSpan is not { } span || App.Window is not { } window)
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
                FrameExporter.CoverName(ResolvedTitle(), span.Start, span.End, format),
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
        Select(SplitCombo, _prefs.GetInt("Split", 0));

        // A minute period remembered from a market that has minute candles, on a market
        // that does not: the preference is this page's, the market is the whole app's, and
        // the two are chosen independently. Falls back to the daily period rather than
        // fetching nothing for ever.
        if (CandleLoader.IsMinute(ChosenPeriod()) && !_market.MinuteCandles)
        {
            Select(PeriodCombo, (int)CandlePeriod.Daily);
        }

        _day = _prefs.GetString("Day", string.Empty);

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
        CrossCheck.IsChecked = _prefs.GetInt("CrossSafeRight", 0) != 0;

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
        _prefs.Save("Split", (int)ChosenSplit());
        _prefs.Save("Months", ChosenMonths());
        _prefs.Save("From", FromDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("To", ToDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("Window", ChosenWindow());
        _prefs.Save("Day", _day);
        _prefs.Save("Averages", AveragesCheck.IsChecked is true ? 1 : 0);
        _prefs.Save("Volume", VolumeCheck.IsChecked is true ? 1 : 0);
        _prefs.Save("CrossSafeRight", CrossSafeRight() ? 1 : 0);
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
