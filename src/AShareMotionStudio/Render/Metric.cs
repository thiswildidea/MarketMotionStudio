using System.Globalization;
using AShareMotionStudio.Localization;
using AShareMotionStudio.Market;
using Windows.UI;

namespace AShareMotionStudio.Render;

/// <summary>
/// Which of a series' two measures a frame is drawing, and everything that follows from that
/// choice: the values, their colours, how a figure reads, what the closing cards say, and which
/// two days get boxed.
///
/// This exists so the shared chrome in <see cref="TurnoverRenderer"/> stays metric-agnostic. The
/// source tool branches on `isRetView()` inside its shared `drawHeader` and `drawStats`, which is
/// fine in one file of one language; here the same knowledge would be spread across a base class
/// and two subclasses, and a third metric later would mean finding every branch. One object per
/// metric means adding one.
///
/// Named `Metric` rather than `Measure` because `Measure` is an inherited method on every
/// `UIElement`, so a page referring to `Measure.Turnover` resolves the method and fails to compile
/// with an error that names layout rather than this type.
/// </summary>
public abstract class Metric
{
    public static Metric Turnover { get; } = new TurnoverMetric();

    public static Metric Return { get; } = new ReturnMetric();

    /// <summary>The values being drawn, in the series' own order.</summary>
    public abstract IReadOnlyList<double> Values(TurnoverSeries series);

    /// <summary>The colour for one day.</summary>
    public abstract Color Colour(TurnoverSeries series, int index);

    /// <summary>The headline used when the user has typed no title.</summary>
    public abstract string DefaultTitle();

    /// <summary>The line under the title saying what is being measured and in what unit.</summary>
    public abstract string Subtitle(TurnoverSeries series);

    /// <summary>The unit, on its own line under the running figure.</summary>
    public abstract string Unit();

    /// <summary>How the running figure reads.</summary>
    public abstract string Readout(double value);

    /// <summary>The four closing cards.</summary>
    public abstract (string Label, string Value)[] Cards(TurnoverSeries series);

    /// <summary>
    /// The two days worth boxing at the end, with what to call them.
    ///
    /// The high is annotated first and the low a little later, so they arrive as two beats rather
    /// than one — which is why the delay belongs to the renderer and the identity to the measure.
    /// </summary>
    public abstract (int Index, string Label)[] Extremes(TurnoverSeries series);

    private sealed class TurnoverMetric : Metric
    {
        public override IReadOnlyList<double> Values(TurnoverSeries series) => series.Totals;

        public override Color Colour(TurnoverSeries series, int index)
        {
            var spread = series.Peak - series.Low;

            return Palette.Volume(spread <= 0 ? 1 : (series.Totals[index] - series.Low) / spread);
        }

        public override string DefaultTitle() => Strings.Get("MarketTurnoverStageTitle");

        public override string Subtitle(TurnoverSeries series) =>
            Strings.Format("TurnoverSubtitle", string.Join(" + ", series.Markets), Strings.Get("TurnoverUnit"));

        public override string Unit() => Strings.Get("TurnoverUnit");

        public override string Readout(double value) => TurnoverRenderer.Round(value);

        public override (string Label, string Value)[] Cards(TurnoverSeries series) =>
        [
            (Strings.Get("TurnoverStatAverage"), TurnoverRenderer.Round(series.Average)),
            (Strings.Get("TurnoverStatPeak"), TurnoverRenderer.Round(series.Peak)),
            (Strings.Get("TurnoverStatLow"), TurnoverRenderer.Round(series.Low)),
            (Strings.Get("TurnoverStatRatio"), Ratio(series)),
        ];

        public override (int Index, string Label)[] Extremes(TurnoverSeries series) =>
        [
            (series.PeakIndex, Strings.Get("TurnoverStatPeak")),
            (series.LowIndex, Strings.Get("TurnoverStatLow")),
        ];

        private static string Ratio(TurnoverSeries series) =>
            series.Low <= 0
                ? "—"
                : (series.Peak / series.Low).ToString("0.00", CultureInfo.InvariantCulture) + "x";
    }

    private sealed class ReturnMetric : Metric
    {
        public override IReadOnlyList<double> Values(TurnoverSeries series) => series.Returns;

        public override Color Colour(TurnoverSeries series, int index) =>
            Palette.Return(series.Returns[index], series.ReturnAbsMax);

        public override string DefaultTitle() => Strings.Get("ReturnStageTitle");

        /// <summary>
        /// Names whatever the returns were computed from — one venue's composite index on the
        /// whole-market page, the chosen instrument on the gain-loss calendar page. Empty falls
        /// back to the composite, which is where the whole-market page's returns come from.
        /// </summary>
        public override string Subtitle(TurnoverSeries series) =>
            Strings.Format(
                "ReturnSubtitle",
                series.ReturnSource.Length > 0 ? series.ReturnSource : Strings.Get("IndexSSE"));

        public override string Unit() => "%";

        /// <summary>
        /// Two decimals and an explicit plus sign on a rise. The sign is what the frame is about,
        /// so leaving a gain unmarked would make the reader work it out from the colour.
        /// </summary>
        public override string Readout(double value) =>
            (value > 0 ? "+" : string.Empty) + value.ToString("0.00", CultureInfo.InvariantCulture);

        public override (string Label, string Value)[] Cards(TurnoverSeries series) =>
        [
            (Strings.Get("ReturnStatUp"), Strings.Format("ReturnDayCount", series.UpDays)),
            (Strings.Get("ReturnStatDown"), Strings.Format("ReturnDayCount", series.DownDays)),
            (Strings.Get("ReturnStatBest"), Percent(series.ReturnMax)),
            (Strings.Get("ReturnStatWorst"), Percent(series.ReturnMin)),
        ];

        public override (int Index, string Label)[] Extremes(TurnoverSeries series) =>
        [
            (series.ReturnMaxIndex, Strings.Get("ReturnStatBest")),
            (series.ReturnMinIndex, Strings.Get("ReturnStatWorst")),
        ];

        private static string Percent(double value) =>
            (value > 0 ? "+" : string.Empty) + value.ToString("0.00", CultureInfo.InvariantCulture) + "%";
    }
}
