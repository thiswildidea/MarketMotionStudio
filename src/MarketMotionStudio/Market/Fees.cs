namespace MarketMotionStudio.Market;

/// <summary>
/// What a fill costs to make, in the mainland's own four parts.
///
/// <para>
/// **Why it is a setting and not a constant.** The diluted cost a broker shows is the cost of the
/// shares *plus* what it cost to trade them, so a book that ignores fees cannot reproduce the
/// number on the screen it was copied from: 中望软件's 300 remaining shares read 14.444 in the
/// broker app and 14.379 when the fees are left out, and the 19.60 yuan between the two is the
/// commission and stamp duty on the two sales. The rates themselves are not fixed either — a
/// broker's commission is negotiated, and the stamp duty has been changed more than once.
/// </para>
///
/// <para>
/// **Rates are in ‱ (per ten thousand).** A commission of 万2.5 is 2.5, stamp duty of 千0.5 is 5,
/// and the transfer fee of 万0.1 is 0.1 — which is how the reader's own statement puts them, and
/// the only unit in which all three fit on one line without a decimal point in front of every
/// figure.
/// </para>
///
/// <para>
/// **One schedule covers every fill**, including the Hong Kong ones. Hong Kong's own charges are
/// nothing like these, and a reader who trades it can set the numbers to match — but a second
/// schedule for a market whose lots are quoted in another currency is two settings where one
/// question was asked.
/// </para>
/// </summary>
/// <param name="Commission">Commission rate in ‱, charged on both sides.</param>
/// <param name="Minimum">The least a commission can be, in yuan, however small the fill.</param>
/// <param name="Stamp">Stamp duty in ‱, charged on the sale only.</param>
/// <param name="Transfer">Transfer fee in ‱, charged on both sides.</param>
public sealed record FeeSchedule(double Commission, double Minimum, double Stamp, double Transfer)
{
    /// <summary>
    /// The mainland's own figures, which is what the page opens with: 万2.5 commission with a
    /// five-yuan floor, 千0.5 stamp duty on the sale, 万0.1 transfer fee both ways.
    ///
    /// Filled in rather than left at zero, because a reader who does not know these numbers still
    /// wants the cost the app on their phone shows — and because an empty field that silently
    /// means "ignore fees" is a setting the reader cannot see is on.
    /// </summary>
    public static FeeSchedule Mainland { get; } = new(2.5, 5, 5, 0.1);

    /// <summary>Nothing is charged: every rate and the floor are zero.</summary>
    public static FeeSchedule None { get; } = new(0, 0, 0, 0);

    /// <summary>
    /// What it costs to buy <paramref name="amount"/> worth: commission and transfer fee.
    /// </summary>
    public double OnBuy(double amount) => CommissionFee(amount) + Rate(Transfer, amount);

    /// <summary>
    /// What it costs to sell <paramref name="amount"/> worth: commission, stamp duty and transfer
    /// fee — the stamp duty being the reason a sale costs more than a purchase of the same size.
    /// </summary>
    public double OnSell(double amount) =>
        CommissionFee(amount) + Rate(Stamp, amount) + Rate(Transfer, amount);

    /// <summary>
    /// The commission, which is the greater of the rate and the floor.
    ///
    /// Most brokers will not take less than five yuan for a fill, and a rate alone would charge
    /// 2.84 on a 9,480-yuan sale — which is how the arithmetic came out 0.014 short of the
    /// broker's own figure for 中望软件, and how it lands on it once the floor is there.
    /// </summary>
    private double CommissionFee(double amount) => Math.Max(Minimum, Rate(Commission, amount));

    private static double Rate(double permyriad, double amount) => (amount * permyriad) / 10_000;
}
