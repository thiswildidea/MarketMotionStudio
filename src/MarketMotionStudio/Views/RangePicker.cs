using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Pages;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace MarketMotionStudio.Views;

/// <summary>
/// Which span of days a page is talking about: the same five answers on the same two pages.
///
/// <para>
/// **One control and not two pickers, because the two pages must agree.** The double-screen frame
/// and the returns page are readings of one book over one interval; separate pickers would have
/// separate defaults, separate "近一年 means three hundred and sixty-five days or two hundred and
/// forty-three trading days" answers, and separate bugs, none of which either page could detect.
/// Both bind this and both read the same instance of the same rule.
/// </para>
///
/// <para>
/// **The spans end today and run back a number of days, not a number of sessions.** Asked what
/// "近一月" means a reader expects the last thirty days on the calendar, thirty trading days being
/// a figure they would have to be told — and the two differ by a third, which is not a rounding
/// error in a comparison anybody checks.
/// </para>
///
/// <para>
/// **Today is its own answer and not a shortcut to one.** A custom range of today to today is the
/// same numbers, but only one of them is also the switch that says "draw this in minutes"; taking
/// the slot away would leave the reader with two labels for one picture and no way to tell them
/// apart.
/// </para>
/// </summary>
public sealed class RangePicker : StackPanel
{
    /// <summary>The menu, in the order it reads: shortest span first.</summary>
    public static readonly (RangeSpan Span, string Key)[] Spans =
    [
        (RangeSpan.Today, "RangeSpanToday"),
        (RangeSpan.Week, "RangeSpanWeek"),
        (RangeSpan.Month, "RangeSpanMonth"),
        (RangeSpan.Year, "RangeSpanYear"),
        (RangeSpan.Custom, "RangeSpanCustom"),
    ];

    /// <summary>Raised when the reader settles on a span — including the first time it is set.</summary>
    public event EventHandler? Changed;

    private readonly ComboBox _menu = new() { HorizontalAlignment = HorizontalAlignment.Stretch };
    private readonly CalendarDatePicker _from = new() { HorizontalAlignment = HorizontalAlignment.Stretch };
    private readonly CalendarDatePicker _to = new() { HorizontalAlignment = HorizontalAlignment.Stretch };

    private StudioPreferences? _prefs;

    /// <summary>
    /// Stops the control's own populating and restoring from raising settled events.
    ///
    /// Every child raises its changed event as it is being filled, and the first value a picker
    /// gets is not the reader's choice. Without the guard each page would fetch on construction
    /// and then fetch again, which on this app is a request per holding.
    /// </summary>
    private bool _loading = true;

    public RangePicker()
    {
        Spacing = 8;

        foreach (var (span, key) in Spans)
        {
            _menu.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = span });
        }

        _menu.Header = Strings.Get("RangeSpanHeader");

        // The children carry their own ids rather than the panel borrowing them: a page host
        // asks for the picker by the panel's name, and anything that must act on the menu or the
        // days — a screen reader, a test — asks for these by theirs.
        Microsoft.UI.Xaml.Automation.AutomationProperties.SetAutomationId(_menu, "SpanPickerMenu");
        Microsoft.UI.Xaml.Automation.AutomationProperties.SetAutomationId(_from, "SpanPickerFrom");
        Microsoft.UI.Xaml.Automation.AutomationProperties.SetAutomationId(_to, "SpanPickerTo");

        _from.Header = Strings.Get("RangeSpanFrom");
        _from.MaxDate = DateTimeOffset.Now;
        _to.Header = Strings.Get("RangeSpanTo");
        _to.MaxDate = DateTimeOffset.Now;

        Children.Add(_menu);
        Children.Add(_from);
        Children.Add(_to);

        Loaded += (_, _) =>
        {
            _menu.SelectionChanged += OnMenuChanged;
            _from.DateChanged += OnDateChanged;
            _to.DateChanged += OnDateChanged;

            _loading = false;
        };
    }

    /// <summary>Which menu entry is chosen right now, Today when nothing is.</summary>
    public RangeSpan Span =>
        _menu.SelectedItem is ComboBoxItem { Tag: RangeSpan span } ? span : RangeSpan.Today;

    /// <summary>The stamp a remembered custom range is written and read in.</summary>
    private const string Stamp = "yyyy-MM-dd";

    /// <summary>
    /// The first day wanted, as far back as the span goes.
    ///
    /// Null only for a custom range whose start has not been picked yet, which is a request the
    /// pages decline to make rather than one they answer as "the beginning of time".
    /// </summary>
    public DateOnly? From
    {
        get
        {
            if (Span != RangeSpan.Custom)
            {
                return Today().AddDays(1 - Days(Span));
            }

            return Only(_from.Date);
        }
    }

    /// <summary>The last day wanted. Always today for a preset, which is what a preset means.</summary>
    public DateOnly? To => Span == RangeSpan.Custom ? Only(_to.Date) : Today();

    /// <summary>Whether the reader has asked for something this control can answer.</summary>
    public bool Ready => From is { } from && To is { } to && from <= to;

    /// <summary>Days back from today each preset reaches.</summary>
    private static int Days(RangeSpan span) => span switch
    {
        RangeSpan.Week => 7,
        RangeSpan.Month => 30,
        RangeSpan.Year => 365,
        _ => 1,
    };

    private static DateOnly Today() => DateOnly.FromDateTime(DateTime.Now);

    private static DateOnly? Only(DateTimeOffset? at) =>
        at is { } stamp ? DateOnly.FromDateTime(stamp.Date) : null;

    /// <summary>
    /// Hands the control the page's preferences, under which it remembers itself.
    ///
    /// The <em>shared</em> preferences rather than the page's own: which span the reader last
    /// looked at is a question about the book, and two pages answering it differently is the
    /// disagreement this whole control exists to prevent.
    /// </summary>
    public void Bind(StudioPreferences prefs)
    {
        _prefs = prefs;

        var saved = (RangeSpan)prefs.GetInt("Span", 0);
        var custom = prefs.GetString("SpanCustom", string.Empty).Split('~');

        var spec = DateTimeStyles.None;
        var variants = CultureInfo.InvariantCulture;

        _loading = true;

        if (custom.Length == 2 &&
            DateOnly.TryParseExact(custom[0], Stamp, variants, spec, out var from) &&
            DateOnly.TryParseExact(custom[1], Stamp, variants, spec, out var to))
        {
            _from.Date = new DateTimeOffset(from.ToDateTime(TimeOnly.MinValue), TimeSpan.Zero);
            _to.Date = new DateTimeOffset(to.ToDateTime(TimeOnly.MinValue), TimeSpan.Zero);
        }

        _menu.SelectedItem = _menu.Items
            .OfType<ComboBoxItem>()
            .FirstOrDefault(item => item.Tag is RangeSpan tag && tag == saved)
            ?? _menu.Items[0];

        ApplyVisibility();

        _loading = false;
    }

    /// <summary>
    /// The custom days' own boxes, shown only when the menu is on 自定义.
    ///
    /// Kept rather than hidden in place because two spare date pickers under a menu that says
    /// 近一周 are an argument the reader has to explain away: either they matter to the picture
    /// or they should not be on the panel.
    /// </summary>
    private void ApplyVisibility()
    {
        var custom = Span == RangeSpan.Custom;

        _from.Visibility = custom ? Visibility.Visible : Visibility.Collapsed;
        _to.Visibility = custom ? Visibility.Visible : Visibility.Collapsed;
    }

    private void OnMenuChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_loading)
        {
            return;
        }

        ApplyVisibility();

        // A custom range with an empty end has nothing to fetch, so the choice alone does not
        // settle anything: it waits for the days, which arrive one After the other.
        Save();

        if (Ready)
        {
            Changed?.Invoke(this, EventArgs.Empty);
        }
    }

    private void OnDateChanged(CalendarDatePicker sender, CalendarDatePickerDateChangedEventArgs args)
    {
        if (_loading)
        {
            return;
        }

        // Either picker picking an end before the start is corrected rather than refused — the
        // control is asking which two days, not which order they were thought of in.
        if (Ready && From is { } from && To is { } to && from > to)
        {
            _loading = true;

            if (ReferenceEquals(sender, _to))
            {
                _from.Date = _to.Date;
            }
            else
            {
                _to.Date = _from.Date;
            }

            _loading = false;
        }

        Save();

        if (Ready)
        {
            Changed?.Invoke(this, EventArgs.Empty);
        }
    }

    private void Save()
    {
        _prefs?.Save("Span", (int)Span);

        if (From is { } from && To is { } to)
        {
            // Written in the invariant format and read back the same way: a preference filed under
            // one Windows calendar and reopened under another is not a new question.
            var span = $"{from.ToString(Stamp, CultureInfo.InvariantCulture)}~" +
                       $"{to.ToString(Stamp, CultureInfo.InvariantCulture)}";

            _prefs?.Save("SpanCustom", span);
        }
    }

    /// <summary>
    /// What this control is asking for, said once and said to both pages: the first and last day,
    /// already involving whatever the menu means by the entry it is on.
    /// </summary>
    public (DateOnly From, DateOnly To)? Range =>
        From is { } from && To is { } to && from <= to ? (from, to) : null;
}

/// <summary>The answers on the range menu.</summary>
public enum RangeSpan
{
    /// <summary>今日 — one session, drawn in minutes.</summary>
    Today = 0,

    /// <summary>近一周 — seven days back.</summary>
    Week = 1,

    /// <summary>近一月 — thirty days back.</summary>
    Month = 2,

    /// <summary>近一年 — three hundred and sixty-five days back.</summary>
    Year = 3,

    /// <summary>自定义 — reader's own start and end.</summary>
    Custom = 4,
}
