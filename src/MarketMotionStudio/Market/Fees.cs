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

/// <summary>
/// What a Stock Connect fill costs, in Hong Kong dollars.
///
/// <para>
/// **港股通 and not Hong Kong direct.** The two are close but not the same bill: through the
/// Connect every levy below is charged, and the stamp duty is charged **on both sides** — a sale
/// costs more than a purchase here as well, but for the opposite reason to the mainland, where the
/// stamp duty is the sale's own tax. These are the Shanghai exchange's published figures as of
/// 2026, each rounded the way the exchange rounds it (stamp up to the whole dollar, the rest to
/// the cent).
/// </para>
///
/// <para>
/// **The commission is the broker's, and only the commission.** Every other line is a statutory
/// charge with a published rate, so they are constants; what a broker actually takes differs by
/// account and is the one thing worth asking the reader for — rate and floor, in ‱ and in dollars.
/// </para>
///
/// <para>
/// **The system fee is per fill, not per share.** HK$0.50 on each side of each ticket: on a small
/// order it is the largest line of the bill, and leaving it out makes a 200-share buy look free.
/// </para>
/// </summary>
/// <param name="Commission">The broker's rate, in ‱ of the consideration.</param>
/// <param name="Minimum">The least that commission can be, in Hong Kong dollars.</param>
public sealed record HongKongFees(double Commission, double Minimum)
{
    /// <summary>
    /// The mainland brokers' usual Connect terms: 万2.5 with a **hundred**-dollar floor.
    ///
    /// <para>
    /// **The floor is a hundred, not five.** Five is the mainland's own floor and copying it here
    /// was a quiet mistake: a Connect account is a separate contract with a minimum ticket of
    /// HK$100 at the brokers that offer it, and at the sizes this page deals in — a few hundred
    /// shares — the rate never clears the floor, so the whole bill turned on the one number that
    /// was wrong. 快手's 1,400 shares read 30.312 with the five-dollar floor and 30.448 with the
    /// hundred; the app on the reader's phone reads 30.453.
    /// </para>
    ///
    /// <para>
    /// Still a starting point rather than a fact — the reader's own contract is the answer, which
    /// is why the rate and the floor are two boxes on the settings page.
    /// </para>
    /// </summary>
    public static HongKongFees Connect { get; } = new(2.5, 100);

    /// <summary>Stamp duty: 0.1% on both sides, rounded up to the whole dollar.</summary>
    public const double Stamp = 10;

    /// <summary>Exchange trading fee: 0.00565%, both sides.</summary>
    public const double Trading = 0.565;

    /// <summary>SFC transaction levy: 0.0027%, both sides.</summary>
    public const double Levy = 0.27;

    /// <summary>AFRC transaction levy: 0.00015%, both sides.</summary>
    public const double Afrc = 0.015;

    /// <summary>CCASS settlement fee: 0.002%, both sides, between 2 and 100 dollars.</summary>
    public const double Settlement = 0.2;
    public const double SettlementLeast = 2;
    public const double SettlementMost = 100;

    /// <summary>The exchange's own system fee: half a dollar on each side of each ticket.</summary>
    public const double System = 0.5;

    /// <summary>What it costs to buy, in Hong Kong dollars.</summary>
    public double OnBuy(double amount) => Charged(amount);

    /// <summary>What it costs to sell — the same bill as a buy, stamp duty included.</summary>
    public double OnSell(double amount) => Charged(amount);

    private double Charged(double amount)
    {
        // Each line rounded as the exchange rounds it, and separately: rounding the sum instead
        // would put the total a cent or a dollar off the statement in either direction.
        var stamp = Math.Ceiling(Rate(Stamp, amount));
        var trading = Math.Round(Rate(Trading, amount), 2, MidpointRounding.AwayFromZero);
        var levy = Math.Round(Rate(Levy, amount), 2, MidpointRounding.AwayFromZero);
        var afrc = Math.Round(Rate(Afrc, amount), 2, MidpointRounding.AwayFromZero);

        var settlement = Math.Round(
            Math.Clamp(Rate(Settlement, amount), SettlementLeast, SettlementMost),
            2,
            MidpointRounding.AwayFromZero);

        var commission = Math.Max(Minimum, Rate(Commission, amount));

        return commission + stamp + trading + levy + afrc + settlement + System;
    }

    private static double Rate(double permyriad, double amount) => (amount * permyriad) / 10_000;
}

/// <summary>
/// The two bills, and which one a code is charged on.
///
/// <para>
/// **A fill is charged by the market it traded in, not by a setting.** One schedule for both was
/// the earlier design and it was wrong in a quiet way: a Hong Kong purchase was charged 万2.5 with
/// a five-yuan floor and no stamp duty, when the Connect charges 0.1% stamp on the way in as well
/// as out, plus four levies. The cost price on the page inherited that optimism.
/// </para>
/// </summary>
public sealed record FeeTable(FeeSchedule Mainland, HongKongFees Kong)
{
    /// <summary>The mainland's figures and the Connect's usual terms.</summary>
    public static FeeTable Default { get; } = new(FeeSchedule.Mainland, HongKongFees.Connect);

    /// <summary>Whether this is a Hong Kong listing, which is the only routing question here.</summary>
    public static bool IsKong(string code) => code.StartsWith("hk", StringComparison.OrdinalIgnoreCase);

    /// <summary>What it costs to buy <paramref name="amount"/> worth of <paramref name="code"/>.</summary>
    public double OnBuy(string code, double amount) =>
        IsKong(code) ? Kong.OnBuy(amount) : Mainland.OnBuy(amount);

    /// <summary>What it costs to sell <paramref name="amount"/> worth of <paramref name="code"/>.</summary>
    public double OnSell(string code, double amount) =>
        IsKong(code) ? Kong.OnSell(amount) : Mainland.OnSell(amount);
}
