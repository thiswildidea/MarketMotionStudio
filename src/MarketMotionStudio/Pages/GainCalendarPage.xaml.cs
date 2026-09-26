using System.Collections.ObjectModel;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// The gain-loss calendar as its own page, on any A-share stock or index — the form the
/// whole-market page offers as one view of three, freed from that page's fixed series.
///
/// No renderer of its own: the calendar grid is metric-driven and takes a
/// <see cref="TurnoverSeries"/>, so this page is a different *loader* — one instrument's daily
/// bars shaped into that record — behind the same <see cref="CalendarHeatmapRenderer"/> drawing
/// <see cref="Metric.Return"/>. One render path, a fifth page on it.
/// </summary>
public sealed partial class GainCalendarPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    /// <summary>
    /// The ranges offered, as a number of months. Zero means the custom range, which is the only
    /// one that consults the date pickers. The same set as the whole-market page: the bars
    /// endpoint's ~640-day ceiling applies to one instrument as much as to three.
    /// </summary>
    private static readonly (int Months, string Key)[] Ranges =
    [
        (1, "StudioRange1M"),
        (3, "StudioRange3M"),
        (6, "StudioRange6M"),
        (12, "StudioRange12M"),
        (0, "StudioRangeCustom"),
    ];

    /// <summary>Remembers this page's parameters. Prefixed, because the video panel is shared.</summary>
    private readonly StudioPreferences _prefs = new("GainCalendar.");

    /// <summary>
    /// The per-stock page's preferences container, used for the watchlist key only. The watchlist
    /// is one list shared by both pages — a favourite is a fact about the instrument, not about
    /// the page it was added on — so it is read and written under that page's prefix deliberately.
    /// </summary>
    private readonly StudioPreferences _watchlist = new("Stock.");

    /// <summary>
    /// The fetched series with its instrument, or null before anything has been fetched. Held
    /// rather than re-fetched: the duration slider re-paces the same data, and a re-fetch would
    /// be a round trip to arrive at the same numbers.
    /// </summary>
    private InstrumentCalendarSeries? _fetched;

    /// <summary>What the search last settled on, so a fetch without a suggestion still knows its name.</summary>
    /// <summary>Replaced at construction by the market's own first one-tap instrument.</summary>
    private string _instrumentCode = "sh000001";

    private string _instrumentName = string.Empty;

    private StockSuggestion? _pendingChoice;

    private string _lastQuery = string.Empty;

    private readonly ObservableCollection<StockFavourite> _favourites = [];

    private readonly DispatcherTimer _searchDebounce = new() { Interval = TimeSpan.FromMilliseconds(260) };

    /// <summary>
    /// The market in force: it names the presets, it is what the search is filtered
    /// to, and it is the one thing that can say whether a typed code belongs here.
    /// </summary>
    private readonly MarketProfile _market = Markets.Of(MarketSettings.Current);

    public GainCalendarPage()
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

        // The presets are the market's own one-tap instruments: an A-share index on a
        // page set to Hong Kong would be a button that fetches from a venue the rest of
        // the page has stopped naming.
        foreach (var index in _market.BroadIndices)
        {
            Presets.Items.Add(new MatrixPreset(index.Code, index.Name));
        }

        Favourites.ItemsSource = _favourites;

        _searchDebounce.Tick += async (_, _) =>
        {
            _searchDebounce.Stop();
            await SearchSuggestionsAsync();
        };

        // The default the frame will actually use, before anything is fetched: the
        // market's own first one-tap instrument, which is the one its presets lead with.
        _instrumentCode = _market.BroadIndices[0].Code;
        _instrumentName = _market.BroadIndices[0].Name;

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

        // After every control exists and every handler is attached, so a restored value reaches
        // the preview through the same path a typed one does.
        RestorePreferences();
        ApplyPreviewSettings();
    }

    protected override InfoBar StatusControl => Status;

    /// <summary>Reuses the page title as the job label, as the other pages do.</summary>
    protected override string JobName => Strings.Get("GainCalendarPageTitle.Text");

    // ---- preview -------------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        var title = ResolvedTitle();
        var showTitle = VideoSettings.ShowTitle;

        if (_fetched is { } fetched)
        {
            var plan = AnimationPlan.For(VideoSettings.Duration, fetched.Series.Count, fetched.Series.Peak);

            Preview.Renderer = new CalendarHeatmapRenderer(fetched.Series, plan, Metric.Return)
                { Title = title, ShowTitle = showTitle };
        }
        else
        {
            _stage.Title = title;
            _stage.ShowTitle = showTitle;
            Preview.Renderer = _stage;
        }

        VideoSettings.TitlePlaceholder = Strings.Format("GainCalendarDefaultTitle", _instrumentName);

        var ready = _fetched is not null;

        PlayButton.IsEnabled = ready;
        ExportButton.IsEnabled = ready;
        CoverButton.IsEnabled = ready;

        RefreshScrubText();
        Preview.Redraw();
    }

    /// <summary>
    /// The title the frame will draw: the typed one, or the default naming the current
    /// instrument. Resolved here rather than in the renderer because the default follows the
    /// *page's* instrument, not the metric's fixed one.
    /// </summary>
    private string ResolvedTitle() =>
        VideoSettings.TitleText.Length > 0
            ? VideoSettings.TitleText
            : Strings.Format("GainCalendarDefaultTitle", _instrumentName);

    private (DateOnly Start, DateOnly End) ChosenRange()
    {
        var months = RangeCombo.SelectedItem is ComboBoxItem { Tag: int m } ? m : 3;

        if (months == 0)
        {
            return (DateOnly.FromDateTime(FromDate.Date.DateTime), DateOnly.FromDateTime(ToDate.Date.DateTime));
        }

        var today = DateOnly.FromDateTime(DateTime.Now);
        return (today.AddMonths(-months), today);
    }

    // ---- search -------------------------------------------------------------------------

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

    /// <summary>
    /// Suggestions while a person types; a code, a Chinese name or pinyin all resolve here.
    /// Filtered to A-shares — this page's bars endpoint speaks nothing else, so a Hong Kong row
    /// would be a suggestion that refuses on click.
    /// </summary>
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
            // A failed suggestion list is a quiet failure: the person is still typing, and a
            // status line flashing under every keystroke is worse than no suggestions.
            InstrumentSearch.ItemsSource = null;
        }
    }

    private void OnSuggestionChosen(AutoSuggestBox sender, AutoSuggestBoxSuggestionChosenEventArgs args)
    {
        // Held rather than read from the submit event's args — this projection of AutoSuggestBox
        // does not carry ChosenItem there, and the field survives either way.
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

        // A code the normalizer can read but the market in force does not quote: the
        // reader's next step is different from the one above, so it says which market.
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

    // ---- favourites ---------------------------------------------------------------------

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
            // The name is worth remembering alongside the code, and it is only in hand after a
            // fetch — a favourite without a name is a code nobody recognises later.
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

    // ---- fetching -----------------------------------------------------------------------

    /// <summary>
    /// Sets the instrument and fetches it. Name and code are both taken because the suggestion,
    /// the preset or the favourite already knows the name — the loader re-reads it from the
    /// response anyway, and the fetched value is the one that sticks.
    /// </summary>
    private void ChooseInstrument(string code, string name)
    {
        _instrumentCode = code;
        _instrumentName = name;

        Fetch();
    }

    private async void Fetch()
    {
        var (start, end) = ChosenRange();
        var display = _instrumentName.Length > 0 ? _instrumentName : _instrumentCode;

        await RunAsync(FetchButton, async cancellation =>
        {
            var progress = new Progress<string>(message => ShowStatus(InfoBarSeverity.Informational, message));

            var fetched = await InstrumentCalendar.LoadAsync(
                Services.Quotes, _market, _instrumentCode, display, start, end, progress, cancellation);

            _fetched = fetched;
            _instrumentName = fetched.Name;
            ApplyPreviewSettings();

            // Parked on the last frame: the closing statistics are what someone wants to look at
            // before deciding whether to export, and frame zero shows an empty grid instead.
            ShowMoment(1);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "GainCalendarFetched",
                fetched.Series.Count,
                TurnoverRenderer.Iso(fetched.Series.Dates[0]),
                TurnoverRenderer.Iso(fetched.Series.Dates[^1]),
                fetched.Series.UpDays,
                fetched.Series.DownDays));
        }, TimeSpan.FromMinutes(2));
    }

    private void OnFetch(object sender, RoutedEventArgs e) => Fetch();

    // ---- playback -----------------------------------------------------------------------

    /// <summary>
    /// Moves the preview and the scrub bar together, without the slider's own handler stopping
    /// the playback that might be driving it.
    /// </summary>
    private void ShowMoment(double progress)
    {
        Preview.Progress = progress;

        Scrub.ValueChanged -= OnScrub;
        Scrub.Value = progress;
        Scrub.ValueChanged += OnScrub;

        RefreshScrubText();
        Preview.Redraw();
    }

    private void OnRangeChanged(object sender, SelectionChangedEventArgs e)
    {
        // Raised by the selection assignment in the constructor, before CustomRange exists.
        if (CustomRange is null)
        {
            return;
        }

        var custom = RangeCombo.SelectedItem is ComboBoxItem { Tag: 0 };
        CustomRange.Visibility = custom ? Visibility.Visible : Visibility.Collapsed;

        SavePreferences();
    }

    private void OnScrub(object sender, RangeBaseValueChangedEventArgs e)
    {
        // Moving the slider is an instruction to look at one moment, which means stopping the
        // playback wherever it had got to.
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

    void IPlaybackHost.ShowMoment(double progress) => ShowMoment(progress);

    void IPlaybackHost.ShowPlaybackState(bool playing) =>
        PlayButton.Content = Strings.Get(playing ? "StudioPause.Content" : "StudioPlay.Content");

    TimeSpan IPlaybackHost.PlaybackDuration => VideoSettings.Duration;

    // ---- export -------------------------------------------------------------------------

    private async void OnExport(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || _fetched is not { } fetched || App.Window is not { } window)
        {
            return;
        }

        // Read before the work starts, so touching a slider mid-export cannot change the format
        // halfway through the file.
        var format = VideoSettings.Format;
        var margins = VideoSettings.Margins;
        var duration = VideoSettings.Duration;
        var label = ResolvedTitle();

        CancelButton.IsEnabled = true;

        // Generous, and proportional to what is being asked for. The timeout is a backstop
        // against a wedged pipeline, not a schedule.
        var limit = TimeSpan.FromMinutes(5) + (duration * 4);

        Diagnostics.CrashLog.Note($"export: clicked, {format.Width}x{format.Height} dur={duration}");

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
                VideoExporter.VideoName(label, fetched.Series.Dates[0], fetched.Series.Dates[^1], format),
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
                FrameExporter.CoverName(ResolvedTitle(), fetched.Series.Dates[0], fetched.Series.Dates[^1], format),
                cancellation);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioCoverSaved", file.Name, format.Width, format.Height, folder.Path));
        }, TimeSpan.FromSeconds(90));
    }

    // ---- preferences --------------------------------------------------------------------

    private void RestorePreferences()
    {
        _prefs.Restoring = true;

        var months = _prefs.GetInt("Months", 3);
        var index = Array.FindIndex(Ranges, r => r.Months == months);
        RangeCombo.SelectedIndex = index >= 0 ? index : 1;

        if (DateTime.TryParse(_prefs.GetString("From", string.Empty), out var from))
        {
            FromDate.Date = from;
        }

        if (DateTime.TryParse(_prefs.GetString("To", string.Empty), out var to))
        {
            ToDate.Date = to;
        }

        var code = _prefs.GetString("Code", _market.BroadIndices[0].Code);

        // A code saved under another market is not carried over: it would fetch from a
        // venue whose presets and search results this page no longer shows.
        if (_market.Accepts(code))
        {
            _instrumentCode = code;

            // The name as it was spelled at fetch time. A stale name is refreshed by the next
            // fetch; carrying it costs one key and keeps the placeholder honest meanwhile.
            var name = _prefs.GetString("Name", string.Empty);

            _instrumentName = name.Length > 0 ? name : _market.BroadIndices[0].Name;
        }

        VideoSettings.Restore(_prefs);
        LoadFavourites();

        _prefs.Restoring = false;
    }

    private void SavePreferences()
    {
        _prefs.Save("Months", RangeCombo.SelectedItem is ComboBoxItem { Tag: int m } ? m : 3);
        _prefs.Save("From", FromDate.Date.ToString("O"));
        _prefs.Save("To", ToDate.Date.ToString("O"));
        _prefs.Save("Code", _instrumentCode);
        _prefs.Save("Name", _instrumentName);

        VideoSettings.Save(_prefs);
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();
}
