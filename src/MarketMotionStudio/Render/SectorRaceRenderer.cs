using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using Microsoft.Graphics.Canvas;
using Microsoft.Graphics.Canvas.Brushes;
using Microsoft.Graphics.Canvas.Geometry;
using Microsoft.Graphics.Canvas.Text;
using Windows.Foundation;
using Windows.UI;

namespace MarketMotionStudio.Render;

/// <summary>
/// The sector race: horizontal bars overtaking one another, their order changing to the last
/// frame — the port of `sector_race_studio.html`'s render path.
///
/// What makes it smooth is that **the ranking itself is interpolated**. The naive approach —
/// snap each row to its new position every time a trading day passes — moves the whole field in
/// steps. Instead every day's ranking is precomputed, playback maps to a fractional day index,
/// and a row's vertical position is its two neighbouring days' ranks eased with a smoothstep
/// while its length interpolates linearly: two rows that trade places cross over smoothly
/// rather than swapping. The whole thing is a pure function of the frame's progress, which is
/// what lets a scrubbed preview and a frame-by-frame export agree.
///
/// The axis range is interpolated per day too, for the same reason — otherwise the whole field
/// rescales in one jump at each midnight — with fixed headroom on both ends because the value
/// labels sit outside the bar's end until the bar is long enough to hold them inside.
/// </summary>
public sealed class SectorRaceRenderer : IFrameRenderer
{
    /// <summary>The left gutter's name column, in baseline pixels.</summary>
    private const double GutterLeft = 176;

    /// <summary>The right gutter's value-label column.</summary>
    private const double GutterRight = 130;

    /// <summary>
    /// The largest a row's text is allowed to be, in baseline pixels.
    ///
    /// This was 30, and 30 was a size the frame mostly never reached: the text used to be measured
    /// against the **row** (34% of the pitch), so a board of eight rows asked for 50 and got the
    /// cap, while a board of fifteen — the market-cap race, the densest in the app — asked for 27
    /// and got 27. Every board in the app looked like the cap except the one with the most rows to
    /// fit, which is the one whose text most needed the room. On the preview, drawn at about a
    /// third of the frame, 27 baseline pixels is a glyph eight *screen* pixels tall, and a CJK
    /// character has no strokes left at eight pixels: it reads as a grey smudge, while the sector
    /// race next to it in the menu reads as words.
    /// </summary>
    private const double LabelCap = 36;

    /// <summary>
    /// What share of its own bar a row's text may take up.
    ///
    /// Against the bar rather than against the row, because the bar is what the text has to sit on
    /// or beside: the row pitch sets how close two rows are, and the bar sets how tall each one is
    /// drawn. Tying the text to the pitch made a row that draws a *thin* bar report the same size
    /// as a row twice its height, which is why the dense board came out smallest of all.
    /// </summary>
    private const double LabelOfBar = 0.72;

    /// <summary>Baseline rows between the plot's bottom and the credit.</summary>
    private const double CreditGap = 74;

    private const double HeaderTopFraction = 0.278;

    private readonly SectorRaceSeries _series;

    private readonly RaceMetric _metric;

    /// <summary>The per-day ranking: rank[k][i] is racer k's position on day i, 0 leading.</summary>
    private readonly int[][] _rank;

    /// <summary>
    /// Per racer, the first day it is on the board for; past the end for one that never is.
    ///
    /// A field whose rows do not all start together — the index race carries 1950 next to 2020 —
    /// and the row has to be *out* of the ranking and not merely at the bottom of it: a racer
    /// ranked last still holds a place, and a board of twelve that shows five would draw its five
    /// rows with seven holes between them, because the holes are the places the absent ones are
    /// keeping warm.
    /// </summary>
    private readonly int[] _starts;

    /// <summary>The axis range per day, precomputed with its headroom.</summary>
    private readonly double[] _axisMin;

    private readonly double[] _axisMax;

    /// <param name="showTop">
    /// How many of the field's places the frame shows. The sector race passes nothing — every
    /// entrant is a row — while a market-cap board passes fifteen: it is handed a field of sixty
    /// listings and asks for the fifteen that were largest at each moment, which is what makes its
    /// membership change over time.
    /// </param>
    /// <param name="rankByMagnitude">
    /// Rank by size rather than by signed value, for a board whose rows can go either way.
    ///
    /// Off by default, because a race of cumulative returns or of turnovers is a race *up*: the
    /// signed value is the standing. A board of the largest single-day moves is the other kind,
    /// where −7.7% belongs next to +8.1% and a signed sort buries every drop under every rise.
    /// Only the ranking changes — the bar still grows to whichever side of the zero axis its own
    /// sign says.
    ///
    /// **A constructor argument and not a property**, which is the one thing this page's first
    /// build got wrong: the whole ranking table is precomputed here, before an object initialiser
    /// runs, so `new SectorRaceRenderer(...) { RankByMagnitude = true }` sorted by sign and said
    /// nothing. The frame drew the eight biggest rises and the seven smallest falls — a plausible
    /// picture of the wrong board — while the page's own status line, which ranked by magnitude
    /// itself, reported the correct days. Nothing in the UI could tell the two apart.
    /// </param>
    public SectorRaceRenderer(
        SectorRaceSeries series, RaceMetric metric, TimeSpan duration, int showTop = int.MaxValue,
        bool rankByMagnitude = false)
    {
        _series = series;
        _metric = metric;
        _rankByMagnitude = rankByMagnitude;
        Duration = duration;
        TotalMs = duration.TotalMilliseconds;
        _showTop = Math.Clamp(showTop, 1, Math.Max(1, series.Racers));

        var values = series.ReturnsOrAmounts(metric);

        _rank = new int[series.Racers][];

        _starts = new int[series.Racers];

        for (var k = 0; k < series.Racers; k++)
        {
            _rank[k] = new int[series.Days];
            _starts[k] = Math.Max(0, series.StartOf(k));
        }

        var field = new List<int>(series.Racers);
        var order = new int[series.Racers];

        for (var i = 0; i < series.Days; i++)
        {
            // Only the rows on the board are ranked. The rest are filed after them, in roster
            // order, so that a row joining later does not disturb the order of the ones already
            // racing — and so that their places are the ones below the frame's last row, where
            // nothing is drawn anyway.
            field.Clear();

            for (var k = 0; k < series.Racers; k++)
            {
                if (i >= _starts[k])
                {
                    field.Add(k);
                }
            }

            for (var n = 0; n < field.Count; n++)
            {
                order[n] = field[n];
            }

            // Magnitude, when the page asks for it: a board of the day's biggest moves either
            // way wants −7% beside +8%, and ranking the signed values would file every drop
            // below every rise however small the rise was.
            Array.Sort(order, 0, field.Count, Comparer<int>.Create(
                (a, b) => Rank(values[b][i]).CompareTo(Rank(values[a][i]))));

            var absent = field.Count;

            for (var k = 0; k < series.Racers; k++)
            {
                if (i >= _starts[k])
                {
                    continue;
                }

                order[absent++] = k;
            }

            for (var pos = 0; pos < order.Length; pos++)
            {
                _rank[order[pos]][i] = pos;
            }
        }

        // The axis range per day, with the headroom the labels need. Both ends: the labels sit
        // outside the bar's end, so without room the longest bar pushes its label into the names.
        //
        // Measured over the **rows the frame shows**, not over the whole field. A market-cap board
        // is handed sixty listings and draws fifteen; scaling to all sixty would leave the bars in
        // the top of the frame at a fifth of their width, because whoever is sixtieth is included
        // in a range only that row needs.
        _axisMin = new double[series.Days];
        _axisMax = new double[series.Days];

        for (var i = 0; i < series.Days; i++)
        {
            var low = double.MaxValue;
            var high = double.MinValue;

            for (var k = 0; k < series.Racers; k++)
            {
                // Neither a row below the frame's last place nor one that has not joined yet:
                // the first is off the bottom, the second is not on the board at all, and a zero
                // from the second would pull the axis towards a value nobody drew.
                if (_rank[k][i] >= _showTop || i < _starts[k])
                {
                    continue;
                }

                low = Math.Min(low, values[k][i]);
                high = Math.Max(high, values[k][i]);
            }

            if (low > high)
            {
                low = high = 0;
            }

            var lo = Math.Min(low, 0);
            var hi = Math.Max(high, 0);
            var span = (hi - lo) is var s && s == 0 ? 1 : s;

            _axisMin[i] = lo < 0 ? lo - (span * 0.22) : lo;
            _axisMax[i] = hi > 0 ? hi + (span * 0.16) : hi;
        }
    }

    /// <summary>Rows the frame shows, at most.</summary>
    private readonly int _showTop;

    public string Title { get; set; } = string.Empty;

    public bool ShowTitle { get; set; } = true;

    /// <summary>
    /// Leave out a row whose value is zero at this moment, for a field whose rows have not all
    /// happened yet.
    ///
    /// The extreme-day board carries twenty-four candidate days and draws fifteen, and a day
    /// that is still in the future has no move to show. Ranked by magnitude it sits at the
    /// bottom of the field, which is not far enough: with only five days behind it the frame
    /// still had fifteen rows on it, ten of them reading 0.00%. A row that has not happened
    /// yet is not on the board at all, which is also how the board comes to fill up as the
    /// years pass.
    /// </summary>
    public bool HideEmptyRows { get; set; }

    /// <summary>
    /// Colour the bar by the sign of its value rather than by a hash of its code.
    ///
    /// One colour per row is what lets a viewer follow a company up a market-cap board. A board
    /// of single-day moves has nothing to follow — every row is one day, and what the viewer is
    /// reading is which way it went. So the bar is red for a rise and green for a fall, the
    /// pair this app uses everywhere, and the hashed palette is left to the pages whose rows
    /// are things that persist.
    /// </summary>
    public bool ColourBySign { get; set; }

    /// <summary>Read once, in the constructor: the ranking table depends on it.</summary>
    private readonly bool _rankByMagnitude;

    private double Rank(double value) => _rankByMagnitude ? Math.Abs(value) : value;

    /// <summary>
    /// The resource key for the amount metric's unit word. Overridable because the metric is
    /// 亿 *of something* and only the page knows what: the sector race's turnover is 亿元, a
    /// market-cap race's is 亿元, 亿港元 or 亿美元 depending on the market in force, and a label
    /// naming the wrong currency is a label nobody can check.
    /// </summary>
    public string UnitKey { get; set; } = "SectorUnitYi";

    /// <summary>The metric's own unit word, on every value label.</summary>
    private string Unit => _metric is RaceMetric.Return ? "%" : Strings.Get(UnitKey);

    private int Decimals => _metric is RaceMetric.Return ? 2 : 0;

    public void Draw(CanvasDrawingSession session, FrameContext context)
    {
        var t = context.Progress * TotalMs;

        context.Backdrop.Fill(session, context, Palette.Background);

        var state = StateAt(t);
        DrawAxis(session, context, t, state);
        DrawRows(session, context, t, state);
        DrawFooter(session, context, t);
        DrawHeader(session, context, t, state);
        DrawProgress(session, context);
    }

    /// <summary>Animation shape: the source's own proportions.</summary>
    private double TotalMs { get; set; }

    public TimeSpan Duration { get; set; }

    private double IntroMs => Math.Min(2200, TotalMs * 0.05);

    private double FinaleStart => TotalMs - FinaleMs;

    private double FinaleMs => Math.Clamp(TotalMs * 0.12, 2500, 8000);

    private double RaceSpan => Math.Max(1, TotalMs - IntroMs - FinaleMs);

    /// <summary>
    /// Everything one moment needs: each racer's value, its interpolated slot, and the
    /// interpolated axis range. A pure function of the time — no state carried between frames.
    /// </summary>
    private (double[] Values, double[] Slots, int[] Finals, double AxisMin, double AxisMax, int DayIndex) StateAt(double t)
    {
        var values = _series.ReturnsOrAmounts(_metric);

        var p = Easing.Ramp(t, IntroMs, RaceSpan);
        var pos = p * (_series.Days - 1);

        var i0 = (int)Math.Clamp(Math.Floor(pos), 0, _series.Days - 2);
        var i1 = Math.Min(_series.Days - 1, i0 + 1);
        var f = _series.Days > 1 ? Math.Clamp(pos - i0, 0, 1) : 0;
        var fe = SmoothStep(f);

        var vals = new double[_series.Racers];
        var slots = new double[_series.Racers];
        var finals = new int[_series.Racers];

        for (var k = 0; k < _series.Racers; k++)
        {
            vals[k] = Lerp(values[k][i0], values[k][i1], f);
            slots[k] = Lerp(_rank[k][i0], _rank[k][i1], fe);
            finals[k] = _rank[k][^1];
        }

        return (vals, slots, finals,
            Lerp(_axisMin[i0], _axisMin[i1], f),
            Lerp(_axisMax[i0], _axisMax[i1], f),
            (int)Math.Round(pos));
    }

    private void DrawAxis(
        CanvasDrawingSession session, FrameContext context, double t,
        (double[] Values, double[] Slots, int[] Finals, double AxisMin, double AxisMax, int DayIndex) state)
    {
        var a = Easing.Ramp(t, 400, 1200);
        if (a <= 0)
        {
            return;
        }

        var (top, bottom) = PlotArea(context);
        var (x0, _) = PlotColumns(context);
        var zx = ZeroX(context, state);

        session.DrawLine(
            new((float)zx, (float)(top - context.Px(10))),
            new((float)zx, (float)(bottom + context.Px(10))),
            Ink.Fade(Palette.Grid, a),
            (float)Math.Max(1, context.Px(2)));
    }

    private void DrawRows(
        CanvasDrawingSession session, FrameContext context, double t,
        (double[] Values, double[] Slots, int[] Finals, double AxisMin, double AxisMax, int DayIndex) state)
    {
        var (top, bottom) = PlotArea(context);
        var (x0, x1) = PlotColumns(context);
        var plotW = x1 - x0;

        // The rows the frame shows, which is not the number of racers on a board: sixty listings
        // race for fifteen places, and the row height is set by the places.
        var rows = Math.Min(_showTop, Math.Max(1, _series.Racers));
        var rowH = (bottom - top) / rows;
        var barH = Math.Min(rowH * 0.64, context.Px(96));
        var nameSize = Math.Min(LabelCap, (barH / context.Scale) * LabelOfBar);

        var span = (state.AxisMax - state.AxisMin) is var s && s == 0 ? 1 : s;
        var zx = x0 + ((0 - state.AxisMin) / span) * plotW;

        // Trailing rows first, so a leader overlaps whoever it is passing.
        var order = Enumerable.Range(0, _series.Racers).OrderByDescending(k => state.Slots[k]).ToArray();

        // Not `using`: the name format is cached across frames. See NameFormat.
        var nameFormat = NameFormat(session, context, nameSize);

        using var strongFormat = Ink.Format(context.Px(nameSize), bold: true);
        using var valueFormat = Ink.Format(context.Px(nameSize), bold: true);

        var lastRow = rows - 1;

        var raw = _series.ReturnsOrAmounts(_metric);

        foreach (var k in order)
        {
            // Not on the board yet — see the note on `_starts`. This is the row the index race
            // keeps leaving out: an index whose history begins after the board's first month has
            // no change to show, and drawing it at 0.00% would rank it above every index that
            // was ever down.
            if (state.DayIndex < _starts[k])
            {
                continue;
            }

            // A row whose day has not come yet is not on the board — see HideEmptyRows.
            if (HideEmptyRows && raw[k][state.DayIndex] == 0)
            {
                continue;
            }

            // A field is wider than the board, so a row can be off the bottom of it. Rather than
            // have a listing pop in at the moment it takes fifteenth place, it fades over the
            // place below — which is also what makes "who is falling out" legible.
            var overflow = state.Slots[k] - lastRow;
            var fade = overflow <= 0 ? 1 : Math.Max(0, 1 - overflow);

            if (fade <= 0)
            {
                continue;
            }

            var intro = Easing.Ramp(t, 300 + (k * 60), 700);
            if (intro <= 0)
            {
                continue;
            }

            intro = Math.Min(intro, fade);

            // By the code, not by the index: the field is sixty listings and the palette has
            // sixteen colours, so index-based colours would repeat between rows that can stand
            // next to each other. Hashed, two listings that happen to share a colour are two
            // listings that are unlikely to be adjacent.
            // The same two tones Palette.Return ends on at full depth, so a bar's colour and
            // the value label beside it agree about which way the day went.
            var colour = ColourBySign
                ? (state.Values[k] >= 0 ? Rgb(0xEF, 0x44, 0x44) : Rgb(0x22, 0xC5, 0x5E))
                : Palette.Race16[Palette.RaceIndex(_series.Entries[k].Code)];
            var yc = top + ((state.Slots[k] + 0.5) * rowH);
            var vx = x0 + ((state.Values[k] - state.AxisMin) / span) * plotW;

            var left = Math.Min(zx, vx);
            var right = Math.Max(zx, vx);
            var w = Math.Max(context.Px(3), (right - left) * Easing.OutCubic(intro));
            var bx = vx >= zx ? zx : zx - w;

            // The champion gets a glow through the closing stretch, so the final frame has a focus.
            var champion = t > FinaleStart && state.Finals[k] == 0;

            void Bar(CanvasDrawingSession ds)
            {
                using var brush = new CanvasLinearGradientBrush(
                    ds,
                    [
                        new CanvasGradientStop { Position = 0f, Color = Ink.Fade(colour, 0.55) },
                        new CanvasGradientStop { Position = 1f, Color = Ink.Fade(colour, 0.98) },
                    ])
                {
                    StartPoint = new((float)bx, 0),
                    EndPoint = new((float)(bx + w), 0),
                };

                ds.FillRoundedRectangle(
                    (float)bx, (float)(yc - (barH / 2)), (float)w, (float)barH,
                    (float)context.Px(6), (float)context.Px(6), brush);
            }

            if (champion)
            {
                // shadowBlur 26 → sigma ~13.
                Ink.Glow(session, context.Px(13), 0.85, Bar);
            }

            Bar(session);

            // The name sits in the left gutter, right-aligned against the plot.
            //
            // White for **every** row, not only the champion's. It used to be pale blue
            // (#C9D8F5) with the leader in white, which made the one thing on this board that is
            // not data the dimmest thing on it: at the preview's third of the frame the pale blue
            // reads as grey, and a name is read before a bar is. The champion is marked by its
            // glow instead — a mark that costs nobody else any contrast.
            var nameColour = Color.FromArgb(0xFF, 0xFF, 0xFF, 0xFF);

            Ink.RightMiddle(session, _series.Entries[k].Name,
                x0 - context.Px(NameRightGap), yc, nameFormat, nameColour, intro);

            // The value follows the bar's end outside it; a bar long enough holds its own label
            // inside. Outside, the axis's proportional headroom cannot guarantee room for a label
            // of fixed pixel width — the longest bar is the one that would push its label into
            // the names, and by construction it is also the one long enough to hold it inside.
            var text = ValueText(state.Values[k]);
            var textWidth = Ink.Measure(session, text, valueFormat);
            var inside = w >= textWidth + context.Px(26);

            // Inside, the label is written *on* the bar, so the ink has to be chosen from that bar's
            // own colour and not from the frame. White is right on the dark half of the palette and
            // unreadable on the light half — white on the amber this board hands out is 2.1:1,
            // under the 3:1 floor even for large text — and the market-cap race is drawn entirely in
            // the light half's company. A board coloured by sign keeps white for both signs: there
            // the colours *are* the meaning, and a rise and a fall of the same size written in two
            // different inks would read as two different kinds of label.
            Color insideInk = ColourBySign
                ? Color.FromArgb(0xFF, 0xFF, 0xFF, 0xFF)
                : Ink.OnTopOf(colour);

            Color valueColour = inside
                ? insideInk
                : _metric is RaceMetric.Return
                    ? (state.Values[k] >= 0 ? Palette.Emphasis : Rgb(0x4A, 0xDE, 0x80))
                    : colour;

            if (vx >= zx)
            {
                if (inside)
                {
                    Ink.RightMiddle(session, text, bx + w - context.Px(13), yc, valueFormat, valueColour, intro);
                }
                else
                {
                    Ink.LeftAt(session, text, bx + w + context.Px(12), yc, valueFormat, valueColour, intro);
                }
            }
            else
            {
                if (inside)
                {
                    Ink.LeftAt(session, text, bx + context.Px(13), yc, valueFormat, valueColour, intro);
                }
                else if (bx - context.Px(12) - textWidth < x0)
                {
                    // Outside, on the near side, there is no room: the bar points left and its left
                    // end is close to the plot's own left edge, so a label right-aligned at that end
                    // runs back over the name column and the row reads as one string —
                    // "恒生科技−40.55%". The axis's 22% headroom puts the *most* negative value at
                    // about 16% of the plot's width, which is 36 baseline pixels, and a label is
                    // wider than that; so this is not a rare frame but the one row that is furthest
                    // down in every frame of a board that has a fall on it. Put the label beyond
                    // the zero axis instead, where a short fall has the frame to itself.
                    Ink.LeftAt(session, text, zx + context.Px(12), yc, valueFormat, valueColour, intro);
                }
                else
                {
                    Ink.RightMiddle(session, text, bx - context.Px(12), yc, valueFormat, valueColour, intro);
                }
            }
        }
    }

    private CanvasTextFormat? _names;

    private double _namesFor = -1;

    /// <summary>
    /// The left gutter's format, sized down until the longest name fits the room it is given.
    ///
    /// The room used to be the gutter alone — 150 baseline pixels, less a 24-pixel inset. That is
    /// the right room for a board whose rows say 能源 and 材料, and it is not the right room for
    /// one whose rows say 中国石油化工股份: eight characters is about 261 baseline pixels at the
    /// size a fifteen-row board draws at, so the fit shrank the **whole column** to 19 — every row,
    /// including 腾讯 and 美团 — to keep one name inside a band that was drawn as a column but is
    /// not one.
    ///
    /// It is not a column, because the names are right-aligned against the plot: they end at the
    /// same x and reach left as far as each one needs. What they may use is therefore everything
    /// between the frame's edge and the plot — the gutter **and** the frame's left margin, which on
    /// a bar race holds nothing at all, there being no Y axis on this renderer. See NameRoom.
    ///
    /// **One size for the whole column**, not one per row: rows scaled individually read as a
    /// ransom note rather than as a list. And computed **once**, not per frame — a 2,700-frame
    /// export would otherwise measure every name 2,700 times for an answer that cannot change.
    /// </summary>
    private CanvasTextFormat NameFormat(CanvasDrawingSession session, FrameContext context, double wanted)
    {
        if (_names is not null && Math.Abs(_namesFor - wanted) < 0.01)
        {
            return _names;
        }

        var (x0, _) = PlotColumns(context);

        // Everything between the frame's edge and the plot, not only the gutter — see NameRoom.
        var room = x0 - context.Px(NameRightGap) - context.Px(NameEdgeInset);
        var size = wanted;

        foreach (var entry in _series.Entries)
        {
            if (entry.Name.Length > 0)
            {
                size = Math.Min(size, Ink.FitSize(session, entry.Name, context.Px(wanted), room, bold: true));
            }
        }

        _names?.Dispose();

        _namesFor = wanted;
        _names = Ink.Format(context.Px(Math.Max(wanted * 0.5, size)), bold: true);

        return _names;
    }

    /// <summary>How far a name's right edge stops short of the plot.</summary>
    private const double NameRightGap = 14;

    /// <summary>
    /// How far the longest name may reach towards the frame's left edge.
    ///
    /// Small, and deliberately not the frame's left margin: the margin is how far the *nearest
    /// content* sits from the edge, and on this renderer the title block is what sets it — a name
    /// that runs past it is not overlapping anything, it is using empty frame. What this constant
    /// guards against is a name touching the edge itself, which is the one place it cannot go.
    /// </summary>
    private const double NameEdgeInset = 16;

    private string ValueText(double value) =>
        (_metric is RaceMetric.Return && value > 0 ? "+" : string.Empty)
        + value.ToString("N" + Decimals.ToString(CultureInfo.InvariantCulture), CultureInfo.InvariantCulture)
        + Unit;

    private void DrawFooter(CanvasDrawingSession session, FrameContext context, double t)
    {
        var a = Easing.Ramp(t, FinaleStart - 1200, 900);
        if (a <= 0)
        {
            return;
        }

        using var format = Ink.Format(context.Px(20));

        Ink.Centred(session, Strings.Get("StudioCredit"), context.Width / 2, context.CreditLine,
            format, Palette.Credit, a * 0.8);
    }

    private void DrawHeader(
        CanvasDrawingSession session, FrameContext context, double t,
        (double[] Values, double[] Slots, int[] Finals, double AxisMin, double AxisMax, int DayIndex) state)
    {
        var a = Easing.Ramp(t, 0, 1000);
        var cx = context.Width / 2;

        var title = Title.Length > 0 ? Title : AutoTitle();

        if (ShowTitle)
        {
            var size = Ink.FitSize(session, title, context.Px(64), context.Width - context.Px(120), bold: true);

            using var format = Ink.Format(size, bold: true);

            Ink.Centred(session, title, cx, context.HeaderRow(0.155, ShowTitle), format, Palette.Title, a);
        }

        using (var plain = Ink.Format(context.Px(26)))
        using (var strong = Ink.Format(context.Px(26), bold: true))
        {
            var unit = _series.Racers == 0 ? string.Empty : UnitWord;

            Ink.Runs(
                session,
                [
                    (Iso(_series.Dates[0]) + " " + Strings.Get("StockRangeJoiner") + " " + Iso(_series.Dates[^1]) + " · ",
                        Palette.StockMuted, plain),
                    (_series.Days.ToString(CultureInfo.InvariantCulture), Palette.Emphasis, strong),
                    (" " + Span + " · " + _series.Racers.ToString(CultureInfo.InvariantCulture) + " " + unit,
                        Palette.StockMuted, plain),
                ],
                cx, context.HeaderRow(0.188, ShowTitle), a);
        }

        using (var format = Ink.Format(context.Px(40), bold: true))
        {
            Ink.Centred(session, Iso(_series.Dates[state.DayIndex]), cx,
                context.HeaderRow(0.222, ShowTitle), format, Palette.Moving, a);
        }
    }

    private static void DrawProgress(CanvasDrawingSession session, FrameContext context)
    {
        var height = (float)Math.Max(4, context.Height * 0.003);
        var y = (float)(context.Height - height);

        session.FillRectangle(0, y, (float)context.Width, height, Palette.ProgressTrack);

        Ink.FillHorizontal(
            session,
            new Rect(0, y, context.Width * Math.Clamp(context.Progress, 0, 1), height),
            Palette.RaceProgressFill,
            context.Width);
    }

    /// <summary>The plot's rows: the top anchored to the header block, the bottom to the credit.</summary>
    private (double Top, double Bottom) PlotArea(FrameContext context)
    {
        var top = context.HeaderRow(HeaderTopFraction, ShowTitle);
        var bottom = context.CreditLine - context.Px(CreditGap);

        return (top, bottom);
    }

    /// <summary>The plot's left and right, gutters inside the user's margins.</summary>
    private (double Left, double Right) PlotColumns(FrameContext context) =>
        (context.Margins.Left + context.Px(GutterLeft),
         context.Width - context.Margins.Right - context.Px(GutterRight));

    private double ZeroX(FrameContext context,
        (double[] Values, double[] Slots, int[] Finals, double AxisMin, double AxisMax, int DayIndex) state)
    {
        var (x0, x1) = PlotColumns(context);
        var span = (state.AxisMax - state.AxisMin) is var s && s == 0 ? 1 : s;

        return x0 + ((0 - state.AxisMin) / span) * (x1 - x0);
    }

    /// <summary>“{list} 涨幅竞速” / “{list} 成交额竞速” — the source's own auto-title shape.</summary>
    private string AutoTitle() => Strings.Format(
        _metric is RaceMetric.Return ? "SectorAutoTitleReturn" : "SectorAutoTitleAmount",
        ListLabel);

    /// <summary>The roster's name, supplied by the page — it knows which list was chosen.</summary>
    public string ListLabel { get; set; } = string.Empty;

    /// <summary>
    /// The word after the count of them — 个交易日 for a daily series, 个月 for a monthly one.
    ///
    /// Supplied by the page, and this one used to be read straight off the string table here.
    /// That was a claim about the data, made by a renderer that cannot see the data: when the
    /// market-cap board inherited this renderer and became monthly, every frame it drew announced
    /// "12 个交易日" for twelve months. The page knows what interval it asked the source for; the
    /// renderer only knows how many rows came back.
    ///
    /// Empty means a daily race, which is what this renderer was written for.
    /// </summary>
    public string SpanWord { get; set; } = string.Empty;

    private string Span => SpanWord.Length > 0 ? SpanWord : Strings.Get("StockTradingDaysUnit");

    /// <summary>
    /// The count word for the header line — 个板块, 只个股, 只候选. Supplied by the page because it
    /// belongs to the roster, not to the metric: a key keyed on the metric here is how
    /// `[SectorUnitPercent]` ended up rendered literally in a shipped frame.
    /// </summary>
    public string UnitWord { get; set; } = string.Empty;

    private static string Iso(DateOnly day) => day.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

    private static double Lerp(double a, double b, double t) => a + ((b - a) * t);

    private static double SmoothStep(double t) => (t * t) * (3 - (2 * t));

    private static Color Rgb(byte r, byte g, byte b) => Color.FromArgb(0xFF, r, g, b);
}

/// <summary>Every racer's chosen measure as a per-racer array over the shared days.</summary>
public static class SectorSeriesExtensions
{
    public static double[][] ReturnsOrAmounts(this SectorRaceSeries series, RaceMetric metric) =>
        metric is RaceMetric.Return ? [.. series.Returns] : [.. series.Amounts];
}
