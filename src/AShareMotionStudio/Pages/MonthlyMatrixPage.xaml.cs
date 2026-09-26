using System.Collections.ObjectModel;
using AShareMotionStudio.Localization;
using AShareMotionStudio.Market;
using AShareMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

// System.Progress, named in full because the WinUI namespace carries a Progress control
// that shadows it inside this file's lambda bodies.
using StringProgress = System.Progress<string>;

namespace AShareMotionStudio.Pages;

/// <summary>One broad-index preset button.</summary>
public sealed record MatrixPreset(string Code, string Name);

/// <summary>One search suggestion, as the box displays it.</summary>
public sealed record MatrixSuggestion(string Code, string Name)
{
    public string Display => $"{Name}  {Code}";

    public override string ToString() => Display;
}

/// <summary>
/// The monthly matrix: one instrument's years × months, or several instruments' months side by
/// side — the port of `monthly_matrix_studio.html` on the shared stage.
///
/// It is a page of its own rather than a fourth form of the daily pages because its clock is
/// monthly: one request holds a decade, and a range selector tuned to daily bars would say
/// things the matrix cannot honour.
/// </summary>
public sealed partial class MonthlyMatrixPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    private readonly StudioPreferences _prefs = new("Matrix.");

    private MatrixSpec? _spec;

    /// <summary>The year kind's chosen instrument.</summary>
    private RaceEntry _target = new("sh000001", "上证指数");

    private readonly ObservableCollection<MatrixPreset> _presets = [];
    private readonly ObservableCollection<SectorPick> _picker = [];
    private readonly ObservableCollection<RacePick> _stocks = [];

    private readonly DispatcherTimer _searchDebounce = new() { Interval = TimeSpan.FromMilliseconds(260) };
    private readonly DispatcherTimer _stockSearchDebounce = new() { Interval = TimeSpan.FromMilliseconds(260) };

    private string _lastQuery = string.Empty;
    private string _lastStockQuery = string.Empty;

    private MatrixSuggestion? _pendingChoice;
    private MatrixSuggestion? _pendingStockChoice;

    /// <summary>The compare kind's bounds: fewer than two is not a comparison, more than fourteen does not fit.</summary>
    private const int FewestCompare = 2;

    private const int MostCompare = 14;

    private static readonly int[] YearChoices = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 0];

    private static readonly int[] MonthChoices = [6, 12, 18, 24, 36, 48];

    public MonthlyMatrixPage()
    {
        InitializeComponent();

        foreach (var years in YearChoices)
        {
            YearsCombo.Items.Add(new ComboBoxItem
            {
                Content = years > 0
                    ? string.Format(System.Globalization.CultureInfo.InvariantCulture, "{0}", years)
                    : Strings.Get("MatrixYearsAll"),
                Tag = years,
            });
        }

        YearsCombo.SelectedIndex = Array.IndexOf(YearChoices, 10);

        foreach (var months in MonthChoices)
        {
            MonthsCombo.Items.Add(new ComboBoxItem { Content = $"{months}", Tag = months });
        }

        MonthsCombo.SelectedIndex = Array.IndexOf(MonthChoices, 12);

        // The compare kind's roster, sharing the race page's rosters — the candidate pool is
        // the union the race page already defines, plus the broad indices this page adds.
        foreach (var entry in MonthlySeries.BroadIndices.Concat(SectorLists.Union()))
        {
            _picker.Add(new SectorPick(entry.Code, entry.Name));
        }

        SectorGrid.ItemsSource = _picker;
        PickedStocks.ItemsSource = _stocks;

        foreach (var index in MonthlySeries.BroadIndices.Take(6))
        {
            _presets.Add(new MatrixPreset(index.Code, index.Name));
        }

        Presets.ItemsSource = _presets;

        foreach (var (roster, key) in Rosters)
        {
            RosterCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = roster });
        }

        RosterCombo.SelectedIndex = 0;

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

        _searchDebounce.Tick += async (_, _) => { _searchDebounce.Stop(); await SearchAsync(_lastQuery, TargetSearch, isStockSearch: false); };
        _stockSearchDebounce.Tick += async (_, _) => { _stockSearchDebounce.Stop(); await SearchAsync(_lastStockQuery, StockSearch, isStockSearch: true); };

        _prefs.Restoring = true;
        VideoSettings.Restore(_prefs);
        RestorePreferences();
        _prefs.Restoring = false;

        ApplyPreviewSettings();
        RefreshCount();
    }

    protected override InfoBar StatusControl => Status;

    protected override string JobName => Strings.Get("MatrixPageTitle.Text");

    // ---- the picture -------------------------------------------------------------------

    private bool IsYearMode => YearMode.IsChecked is true;

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        if (_spec is { } spec)
        {
            Preview.Renderer = new MatrixRenderer(spec, VideoSettings.Duration)
            {
                Title = VideoSettings.TitleText,
                ShowTitle = VideoSettings.ShowTitle,
            };
        }
        else
        {
            _stage.Title = VideoSettings.TitleText.Length > 0
                ? VideoSettings.TitleText
                : Strings.Get("MatrixStageTitle");
            _stage.ShowTitle = VideoSettings.ShowTitle;
            Preview.Renderer = _stage;
        }

        var ready = _spec is not null;

        PlayButton.IsEnabled = ready;
        ExportButton.IsEnabled = ready;
        CoverButton.IsEnabled = ready;

        RefreshScrubText();
        Preview.Redraw();
    }

    // ---- mode --------------------------------------------------------------------------

    private void OnModeChanged(object sender, RoutedEventArgs e)
    {
        if (YearBox is null || CompareBox is null)
        {
            return;
        }

        var year = IsYearMode;

        YearBox.Visibility = year ? Visibility.Visible : Visibility.Collapsed;
        CompareBox.Visibility = year ? Visibility.Collapsed : Visibility.Visible;

        if (!_prefs.Restoring)
        {
            _spec = null;
            ApplyPreviewSettings();
            RefreshCount();
            SavePreferences();
        }
    }

    // ---- the year kind's target ---------------------------------------------------------

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

    private async Task SearchAsync(string query, AutoSuggestBox box, bool isStockSearch)
    {
        query = query.Trim();

        if (query.Length == 0)
        {
            box.ItemsSource = null;
            return;
        }

        try
        {
            var found = await Services.Stocks.SearchAsync(query, CancellationToken.None);

            var ordered = found
                .Take(8)
                .Select(r => new MatrixSuggestion(r.Code, r.Name))
                .ToArray();

            box.ItemsSource = ordered;
        }
        catch (Exception)
        {
            box.ItemsSource = null;
        }
    }

    private void OnSuggestionChosen(AutoSuggestBox sender, AutoSuggestBoxSuggestionChosenEventArgs args)
    {
        if (args.SelectedItem is MatrixSuggestion chosen)
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

        SetTarget(code, name);
    }

    private void SetTarget(string code, string name)
    {
        _target = new RaceEntry(code, name.Length > 0 ? name : code.ToUpperInvariant());
        ChosenText.Text = Strings.Format("MatrixChosen", _target.Name, _target.Code.ToUpperInvariant());
        SavePreferences();
    }

    private void OnPresetClick(object sender, RoutedEventArgs e)
    {
        if ((sender as FrameworkElement)?.Tag is string code)
        {
            var preset = _presets.FirstOrDefault(p => p.Code == code);

            SetTarget(code, preset?.Name ?? string.Empty);
        }
    }

    private void OnYearsChanged(object sender, SelectionChangedEventArgs e)
    {
        if (!_prefs.Restoring)
        {
            SavePreferences();
        }
    }

    // ---- the compare kind's roster --------------------------------------------------------

    private enum Roster
    {
        Level1 = 0,
        Themes = 1,
        BroadIndices = 2,
        Custom = 3,
        Stocks = 4,
    }

    private static readonly (Roster Roster, string Key)[] Rosters =
    [
        (Roster.Level1, "SectorListLevel1"),
        (Roster.Themes, "SectorListTheme"),
        (Roster.BroadIndices, "MatrixListIndices"),
        (Roster.Custom, "SectorListCustom"),
        (Roster.Stocks, "SectorListStocks"),
    ];

    private Roster ChosenRoster => RosterCombo.SelectedItem is ComboBoxItem { Tag: Roster roster }
        ? roster
        : Roster.Level1;

    private IReadOnlyList<RaceEntry> CurrentRoster()
    {
        var picked = _picker.Where(p => p.Picked).Select(p => new RaceEntry(p.Code, p.Name)).ToArray();
        var stocks = _stocks.Select(s => new RaceEntry(s.Code, s.Name)).ToArray();

        return ChosenRoster switch
        {
            Roster.Level1 => SectorLists.Level1,
            Roster.Themes => SectorLists.Themes,
            Roster.BroadIndices => MonthlySeries.BroadIndices,
            Roster.Stocks => stocks,
            _ => picked,
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

        if (!_prefs.Restoring)
        {
            _spec = null;
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

        _spec = null;
        ApplyPreviewSettings();
        RefreshCount();
        SavePreferences();
    }

    private void RefreshCount()
    {
        if (IsYearMode)
        {
            CountText.Text = string.Empty;
            return;
        }

        var n = CurrentRoster().Count;
        var bad = n < FewestCompare || n > MostCompare;

        CountText.Text = Strings.Format(bad ? "MatrixCountBounds" : "SectorCount", n, FewestCompare, MostCompare);
    }

    private void OnStockSearchTextChanged(AutoSuggestBox sender, AutoSuggestBoxTextChangedEventArgs args)
    {
        if (args.Reason is not AutoSuggestionBoxTextChangeReason.UserInput)
        {
            return;
        }

        _lastStockQuery = sender.Text;
        _stockSearchDebounce.Stop();
        _stockSearchDebounce.Start();
    }

    private void OnStockSuggestionChosen(AutoSuggestBox sender, AutoSuggestBoxSuggestionChosenEventArgs args)
    {
        if (args.SelectedItem is MatrixSuggestion chosen)
        {
            _pendingStockChoice = chosen;
            sender.Text = chosen.Display;
        }
    }

    private void OnStockSearchSubmitted(AutoSuggestBox sender, AutoSuggestBoxQuerySubmittedEventArgs args)
    {
        var (code, name) = _pendingStockChoice is { } pick
            ? (pick.Code, pick.Name)
            : (StockDirectory.Normalize(sender.Text), string.Empty);

        _pendingStockChoice = null;

        if (code is null)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("StockBadCode"));
            return;
        }

        AddStock(code, name);
    }

    private void AddStock(string code, string name)
    {
        name = new string([.. name.Where(c => !char.IsWhiteSpace(c))]);

        if (_stocks.Any(s => s.Code == code))
        {
            StockSearch.Text = string.Empty;
            return;
        }

        if (_stocks.Count >= MostCompare)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format("MatrixTooManyTargets", MostCompare));
            return;
        }

        _stocks.Add(new RacePick(code, name.Length > 0 ? name : code.ToUpperInvariant()));
        StockSearch.Text = string.Empty;

        _spec = null;
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
            _spec = null;
            ApplyPreviewSettings();
            RefreshCount();
            SavePreferences();
        }
    }

    private void OnMonthsChanged(object sender, SelectionChangedEventArgs e)
    {
        if (!_prefs.Restoring)
        {
            SavePreferences();
        }
    }

    // ---- fetching -------------------------------------------------------------------------

    private void OnFetch(object sender, RoutedEventArgs e)
    {
        if (IsYearMode)
        {
            FetchYear();
        }
        else
        {
            FetchCompare();
        }
    }

    private void FetchYear()
    {
        var years = YearsCombo.SelectedItem is ComboBoxItem { Tag: int y } ? y : 10;

        _ = RunAsync(FetchButton, async cancellation =>
        {
            // IProgress rather than the concrete type: Report is an explicit interface
            // implementation on Progress<T>, invisible on the class itself.
            IProgress<string> progress = new StringProgress(message =>
                ShowStatus(InfoBarSeverity.Informational, message));

            progress.Report(Strings.Format("MatrixFetching", _target.Name));

            var (name, series) = await MonthlySeries.FetchAsync(Services.Http, _target.Code, cancellation);

            if (name.Length > 0 && name != _target.Name)
            {
                _target = _target with { Name = name };
                ChosenText.Text = Strings.Format("MatrixChosen", _target.Name, _target.Code.ToUpperInvariant());
            }

            _spec = MatrixSpecs.Year(_target.Name, _target.Code, series, years);

            ApplyPreviewSettings();
            ShowMoment(1);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "MatrixFetched",
                _spec.Title,
                _spec.Span,
                _spec.Cells.Count,
                _spec.Stats[0].Label,
                _spec.Stats[0].Value,
                _spec.Stats[1].Label,
                _spec.Stats[1].Value));
        }, TimeSpan.FromMinutes(2));
    }

    private void FetchCompare()
    {
        var roster = CurrentRoster();
        var unit = Strings.Get("SectorUnitSectors");

        if (roster.Count < FewestCompare)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format("MatrixTooFewTargets", FewestCompare, unit));
            return;
        }

        if (roster.Count > MostCompare)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format("MatrixTooManyTargets", MostCompare));
            return;
        }

        var months = MonthsCombo.SelectedItem is ComboBoxItem { Tag: int n } ? n : 12;
        var label = (RosterCombo.SelectedItem as ComboBoxItem)?.Content as string ?? string.Empty;

        _ = RunAsync(FetchButton, async cancellation =>
        {
            IProgress<string> progress = new StringProgress(message =>
                ShowStatus(InfoBarSeverity.Informational, Strings.Format("MatrixFetching", message)));

            var fetched = new List<(string Code, string Name, IReadOnlyList<MonthlyPoint> Series)>();

            for (var i = 0; i < roster.Count; i++)
            {
                progress.Report($"{roster[i].Name} ({i + 1}/{roster.Count})");

                var (name, series) = await MonthlySeries.FetchAsync(Services.Http, roster[i].Code, cancellation);

                fetched.Add((roster[i].Code, roster[i].Name.Length > 0 ? roster[i].Name : name, series));
            }

            // A typed stock's name is corrected to what the endpoint calls it.
            if (ChosenRoster is Roster.Stocks)
            {
                for (var i = 0; i < _stocks.Count; i++)
                {
                    var match = fetched.FirstOrDefault(f => f.Code == _stocks[i].Code);

                    if (match.Name.Length > 0 && match.Name != _stocks[i].Name)
                    {
                        _stocks[i] = new RacePick(match.Code, match.Name);
                    }
                }

                SavePreferences();
            }

            _spec = MatrixSpecs.Compare(fetched, label, months);

            ApplyPreviewSettings();
            ShowMoment(1);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "MatrixFetched",
                _spec.Title,
                _spec.Span,
                _spec.Cells.Count,
                _spec.Stats[0].Label,
                _spec.Stats[0].Value,
                _spec.Stats[1].Label,
                _spec.Stats[1].Value));
        }, TimeSpan.FromMinutes(3));
    }

    // ---- preview transport ------------------------------------------------------------------

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

    // ---- export ---------------------------------------------------------------------------

    private string MatrixFileName(VideoFormat format, string extension)
    {
        var label = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : _spec!.Title;

        var safe = new string([.. label.Where(c => !Path.GetInvalidFileNameChars().Contains(c))]).Trim();

        if (safe.Length > 40)
        {
            safe = safe[..40];
        }

        return $"月度矩阵_{safe}_{format.NameSuffix}.{extension}";
    }

    private async void OnExport(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || _spec is null || App.Window is not { } window)
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
                MatrixFileName(format, "mp4"),
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
        if (Preview.Renderer is not { } renderer || _spec is null || App.Window is not { } window)
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
                MatrixFileName(format, "png"),
                cancellation);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioCoverSaved", file.Name, format.Width, format.Height, folder.Path));
        }, TimeSpan.FromSeconds(90));
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();

    // ---- persistence -------------------------------------------------------------------------

    private void SavePreferences()
    {
        if (_prefs.Restoring)
        {
            return;
        }

        _prefs.Save("YearMode", IsYearMode);
        _prefs.Save("TargetCode", _target.Code);
        _prefs.Save("TargetName", _target.Name);
        _prefs.Save("Years", YearsCombo.SelectedItem is ComboBoxItem { Tag: int y } ? y : 10);
        _prefs.Save("Roster", (int)ChosenRoster);
        _prefs.Save("Custom", string.Join(";", _picker.Where(p => p.Picked).Select(p => p.Code)));
        _prefs.Save("Stocks", string.Join(";", _stocks.Select(s => $"{s.Code}|{s.Name}")));
        _prefs.Save("Months", MonthsCombo.SelectedItem is ComboBoxItem { Tag: int n } ? n : 12);
    }

    private void RestorePreferences()
    {
        if (!_prefs.GetBool("YearMode", true))
        {
            CompareMode.IsChecked = true;
        }

        var code = _prefs.GetString("TargetCode", "sh000001");
        var name = _prefs.GetString("TargetName", "上证指数");

        _target = new RaceEntry(code, name);
        ChosenText.Text = Strings.Format("MatrixChosen", _target.Name, _target.Code.ToUpperInvariant());

        var years = _prefs.GetInt("Years", 10);
        var yearIndex = Array.IndexOf(YearChoices, years);
        YearsCombo.SelectedIndex = yearIndex >= 0 ? yearIndex : Array.IndexOf(YearChoices, 10);

        var roster = Math.Clamp(_prefs.GetInt("Roster", 0), 0, 4);
        var rosterMatch = RosterCombo.Items.OfType<ComboBoxItem>()
            .FirstOrDefault(i => i.Tag is Roster r && (int)r == roster);

        if (rosterMatch is not null)
        {
            RosterCombo.SelectedItem = rosterMatch;
        }

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

        var months = _prefs.GetInt("Months", 12);
        var monthIndex = Array.IndexOf(MonthChoices, months);
        MonthsCombo.SelectedIndex = monthIndex >= 0 ? monthIndex : Array.IndexOf(MonthChoices, 12);
    }
}
