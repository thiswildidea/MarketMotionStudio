namespace MarketMotionStudio.Market;

/// <summary>
/// Where a series of daily closes comes from, for the two pages that need years of
/// them and nothing else.
///
/// The plan page and the holding page are arithmetic over one thing: what a coin or a
/// share closed at, day by day, across a span. Neither cares whether those closes were
/// walked backwards six hundred and forty at a time off a Chinese quote endpoint or
/// fetched in one request from a chart endpoint abroad — they care that the answer is a
/// day-keyed series covering the range, and that a day the instrument had no price for
/// is absent rather than zero.
///
/// So the source is an interface and not a class, and it is deliberately the narrowest
/// thing that lets the two pages do their work: one method, no notion of a bar, an
/// adjustment, a venue or a currency. Adding a second kind of instrument — the crypto
/// pages — then costs one small implementation rather than a second copy of two
/// loaders, and the copies are what would drift: a plan simulated over one source's
/// closes and another's would not answer the same question.
/// </summary>
public interface ICloseWalk
{
    /// <summary>
    /// The closes from <paramref name="start"/> to <paramref name="end"/>, or as many
    /// as the source has, keyed by day. Days the instrument did not trade are absent.
    /// </summary>
    /// <param name="code">The instrument, in the spelling its own source wants.</param>
    /// <param name="display">The name to report progress in, already localised.</param>
    Task<SortedList<DateOnly, double>> ClosesAsync(
        string code, string display, DateOnly start, DateOnly end,
        IProgress<string> progress, CancellationToken cancellation);
}

/// <summary>
/// Closes walked off the stock quote endpoint.
///
/// A pass-through, and the whole point of it: the paging, the adjustment question and
/// the stop condition are <see cref="HistoryWalk"/>'s, and they stay there. This class
/// exists so that the loaders can name the *shape* of what they need instead of naming
/// a venue.
/// </summary>
public sealed class TencentCloseWalk(TencentKline kline) : ICloseWalk
{
    public Task<SortedList<DateOnly, double>> ClosesAsync(
        string code, string display, DateOnly start, DateOnly end,
        IProgress<string> progress, CancellationToken cancellation) =>
        HistoryWalk.ClosesAsync(kline, code, display, start, end, progress, cancellation);
}

/// <summary>
/// Closes read off a cryptocurrency source.
///
/// The same shape as the walk above and none of its machinery: a coin's history comes
/// back in one reply and is not adjusted, because there is nothing to adjust for —
/// see the note on <see cref="CryptoQuotes"/>. What it shares with the walk is the
/// answer, which is all either loader ever reads.
/// </summary>
public sealed class CryptoCloseWalk(CryptoQuotes quotes) : ICloseWalk
{
    public Task<SortedList<DateOnly, double>> ClosesAsync(
        string code, string display, DateOnly start, DateOnly end,
        IProgress<string> progress, CancellationToken cancellation) =>
        quotes.ClosesAsync(code, display, start, end, progress, cancellation);
}
