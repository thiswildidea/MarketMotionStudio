using System;
using System.Linq;
using System.Threading.Tasks;
using MarketMotionStudio.Diagnostics;
using Windows.Services.Store;
using Windows.System;

namespace MarketMotionStudio;

/// <summary>How an attempt to subscribe ended, as far as this process saw.</summary>
public enum SubscribeOutcome
{
    /// <summary>The Store took the subscription and the licence now says so.</summary>
    Subscribed,

    /// <summary>The Store's own dialog was dismissed.</summary>
    Cancelled,

    /// <summary>Nothing could be offered: no network, no Store, or no add-on published yet.</summary>
    Unavailable,

    Failed,
}

/// <summary>
/// Whether this machine has paid for the monthly subscription, and getting it.
///
/// **Two things ride on the answer: writing a video file, and taking the
/// watermark off it.** Everything else — fetching data, drawing the preview,
/// saving a cover image — stays open. The answer is asked for in one place
/// (<see cref="Views.SubscriptionOffer"/>) on behalf of every page, and it is the
/// licence that answers, not a record this app keeps of having been paid.
///
/// Nothing is cached beyond the process. The Store keeps the licence on the
/// machine and answers from it offline, and a copy of "someone paid" that this
/// app had to keep fresh would be a licence that could be argued with: it would
/// either expire on its own schedule or be believed forever, and both are worse
/// than asking again.
///
/// Every failure to ask is treated as "not subscribed". A build sideloaded from
/// Visual Studio, a machine with the Store disabled by policy, an add-on not yet
/// published and no network all land here — and treating any of those as paid
/// would give the thing away, while treating them as unpaid costs whoever it
/// hits exactly one dialog. Held for the app's lifetime rather than by the
/// window, for the same reason <see cref="StoreUpdates"/> is.
/// </summary>
public sealed class StoreSubscription
{
    /// <summary>
    /// The add-on's own identifier, as it is written in Partner Center.
    ///
    /// Not its <c>StoreId</c>: that one is issued by the Store per product per
    /// account and differs between a test flight and the published listing, so
    /// it cannot be written down here. The token is the one thing that survives
    /// both, and the offer is looked up by it every time.
    /// </summary>
    private const string OfferToken = "MarketMotionStudio";

    /// <summary>
    /// The kinds of add-on the query asks for. Every kind an add-on can be,
    /// on purpose: a subscription add-on *is* a durable one as far as this
    /// filter is concerned — the Store reports its `ProductKind` as `Durable`
    /// and carries the billing period on the SKU instead, so "Durable" alone
    /// would find ours in a correctly published world. It was also the one
    /// thing here that could make the list come back empty for a reason of
    /// our own: had the add-on been created as some other kind in Partner
    /// Center, asking only for "Durable" would return nothing and the log
    /// would blame the Store. Asking for all of them costs nothing — the
    /// offer is picked by token, never by kind — and what the query returns
    /// is written out with its kind, so a wrong kind shows up as a fact
    /// instead of an absence.
    /// </summary>
    private static readonly string[] Kinds = ["Durable", "Consumable", "UnmanagedConsumable"];

    /// <summary>Where the Store sends someone to end a subscription it is billing.</summary>
    private static readonly Uri AccountServices = new("https://account.microsoft.com/services/");

    private StoreContext? _context;
    private StoreProduct? _offer;

    public bool Subscribed { get; private set; }

    /// <summary>
    /// Whether the Store answered at all, either way.
    ///
    /// False on a machine where there was nothing to buy — sideloaded build,
    /// Store switched off, add-on not published — and the settings card is
    /// hidden rather than shown empty, for the same reason the update button is:
    /// offering something requires having something to offer.
    /// </summary>
    public bool Known { get; private set; }

    /// <summary>
    /// What it costs, as the Store prices it in this market — currency included,
    /// because naming a currency this app cannot know is not a thing it should
    /// be doing.
    /// </summary>
    public string? Price { get; private set; }

    /// <summary>When the month runs out. Null when nobody is subscribed.</summary>
    public DateTimeOffset? RenewsOn { get; private set; }

    public bool Busy { get; private set; }

    /// <summary>Raised when the answer changes, so open previews and settings controls catch up.</summary>
    public event EventHandler? Changed;

    /// <summary>
    /// The Store's context, associated with the window.
    ///
    /// A desktop app has no CoreWindow for the Store to parent its prompts to,
    /// so without this the purchase dialog fails instead of appearing. Done
    /// once: a context can be initialised with a window only once, and there is
    /// only one window.
    /// </summary>
    private StoreContext Context(nint window)
    {
        if (_context is null)
        {
            _context = StoreContext.GetDefault();
            WinRT.Interop.InitializeWithWindow.Initialize(_context, window);
        }

        return _context;
    }

    /// <summary>Asks the Store again what this machine is entitled to.</summary>
    public async Task RefreshAsync(nint window)
    {
        await ResolveAsync(window);

        ReadSimulation();

        Changed?.Invoke(this, EventArgs.Empty);
    }

    /// <summary>
    /// Puts the offer in front of the user and takes them through the Store's
    /// own purchase dialog.
    ///
    /// The result is not believed on its own word: success only means the Store
    /// says the purchase went through, and it is the licence afterwards that
    /// decides whether anything is unlocked. Both are read, because a purchase
    /// that succeeded without granting the licence is exactly the report nobody
    /// thinks to file.
    /// </summary>
    public async Task<SubscribeOutcome> SubscribeAsync(nint window)
    {
        if (Busy)
        {
            return SubscribeOutcome.Failed;
        }

        Busy = true;
        Changed?.Invoke(this, EventArgs.Empty);

        try
        {
            var offer = _offer ?? await LookupAsync(window);

            if (offer is null)
            {
                return SubscribeOutcome.Unavailable;
            }

            var result = await Context(window).RequestPurchaseAsync(offer.StoreId);

            CrashLog.Note($"subscribe: purchase ended, status={result.Status}");

            if (result.Status is StorePurchaseStatus.NetworkError or StorePurchaseStatus.ServerError)
            {
                return SubscribeOutcome.Unavailable;
            }

            // Read again rather than reusing what the purchase dialog said.
            await ResolveAsync(window);

            return Subscribed
                ? SubscribeOutcome.Subscribed
                : result.Status == StorePurchaseStatus.Succeeded
                    ? SubscribeOutcome.Failed
                    : SubscribeOutcome.Cancelled;
        }
        catch (Exception ex)
        {
            CrashLog.Note($"subscribe: purchase failed, {ex.GetType().Name} 0x{ex.HResult:X8}");
            return SubscribeOutcome.Failed;
        }
        finally
        {
            Busy = false;
            Changed?.Invoke(this, EventArgs.Empty);
        }
    }

    /// <summary>
    /// Re-reads the licence without showing a purchase dialog.
    ///
    /// There is nothing to restore as such — the Store's answer already sits on
    /// the machine and re-reading it is the whole of what this does — but there
    /// has to be a button that does it, because for someone who has paid and
    /// finds the app locked, the obvious alternative is to reinstall it.
    /// </summary>
    public async Task RestoreAsync(nint window) => await RefreshAsync(window);

    /// <summary>Opens the page where a Store subscription is cancelled.</summary>
    public static Task ManageAsync() => Launcher.LaunchUriAsync(AccountServices).AsTask();

    /// <summary>
    /// Asks for the offer and then for the licence, and sets everything else from
    /// what they say.
    /// </summary>
    private async Task ResolveAsync(nint window)
    {
        RenewsOn = null;
        Subscribed = false;

        var offer = await LookupAsync(window);

        if (offer is null)
        {
            Known = false;
            return;
        }

        try
        {
            var license = await Context(window).GetAppLicenseAsync();

            Subscribed = Holds(license, offer);

            if (Subscribed)
            {
                RenewsOn = license.AddOnLicenses[offer.StoreId].ExpirationDate;
            }

            Known = true;
        }
        catch (Exception ex)
        {
            // A failure to read the licence is not a licence. Left locked, and
            // `Known` stays false so nothing claims to have an answer.
            CrashLog.Note($"subscribe: licence read failed, {ex.GetType().Name} 0x{ex.HResult:X8}");
            Known = false;
        }
    }

    /// <summary>
    /// Whether the licence grants the add-on <paramref name="offer"/> names, and
    /// still does today.
    ///
    /// The expiry is checked as well as the active flag. A subscription is billed
    /// month by month and its licence carries the date it runs to; whether the
    /// Store answers no past that point is its business, but the cost of looking
    /// is nothing and the cost of being wrong about something paid for is the
    /// whole arrangement.
    ///
    /// Matching on the token as well as the identifier: the Store keys these by
    /// the same <c>StoreId</c> it issues, and matching only on that key would
    /// leave nothing to fall back on if it ever hands back a different one for
    /// the same product.
    /// </summary>
    private static bool Holds(StoreAppLicense license, StoreProduct offer)
    {
        if (license.AddOnLicenses.TryGetValue(offer.StoreId, out var granted))
        {
            return Live(granted);
        }

        return license.AddOnLicenses.Values.Any(
            addOn => addOn.InAppOfferToken == offer.InAppOfferToken && Live(addOn));

        // Licences that never run out carry the default date rather than one far
        // in the future, so "no expiry" has to be read as "still going".
        static bool Live(StoreLicense addOn) =>
            addOn.IsActive && (addOn.ExpirationDate == default || addOn.ExpirationDate > DateTimeOffset.Now);
    }

    /// <summary>
    /// The add-on this token names, or null when the Store has nothing by that
    /// name — the ordinary state on a machine whose app was sideloaded, whose
    /// Store is switched off, or whose publisher has not published it yet.
    /// </summary>
    private async Task<StoreProduct?> LookupAsync(nint window)
    {
        try
        {
            var result = await Context(window).GetAssociatedStoreProductsAsync(Kinds);

            // An empty list and a failed query look exactly alike from the
            // outside, and the difference is the whole diagnosis: no add-on
            // published is a thing to fix in Partner Center, while a query that
            // failed is this machine or this package — 0x803F6107, the one
            // everybody hits, is the Store declining to answer a build it does
            // not consider Store-installed. Without this line the log says
            // "among 0" and the publisher goes looking in the wrong place.
            if (result.ExtendedError is { } failure)
            {
                CrashLog.Note($"subscribe: add-on query failed, 0x{failure.HResult:X8}");
            }

            var offer = result.Products.Values.FirstOrDefault(
                product => string.Equals(product.InAppOfferToken, OfferToken, StringComparison.OrdinalIgnoreCase));

            _offer = offer;

            if (offer is null)
            {
                // "Nothing at all" and "things, but none by this name" are two
                // entirely different diagnoses, and one sentence is all the
                // publisher gets to tell them apart:
                //
                //   among 0            — the Store has no add-on for this app.
                //                        Either none is published, or the query
                //                        failed (see the line above).
                //   X named instead    — add-ons are published and reachable, so
                //                        the one being asked for is named
                //                        differently in Partner Center. The exact
                //                        product IDs come back here, which turns
                //                        a hunt through the dashboard into one
                //                        comparison.
                CrashLog.Note(
                    result.Products.Count == 0
                        ? $"subscribe: no add-on named {OfferToken}; the Store returned none for this app"
                        : $"subscribe: no add-on named {OfferToken}; it returned "
                          + string.Join(", ", result.Products.Values.Select(
                              product => $"{product.InAppOfferToken}/{product.StoreId} ({product.ProductKind})")));

                return null;
            }

            Price = offer.Price?.FormattedPrice;

            // Whether it really renews every month is written off the SKU below,
            // for the log rather than for a decision: the words on screen come
            // from resources that have to agree with Partner Center whether or
            // not anything is read back here. Noted either way, so the two
            // disagreeing is something a log can show instead of a claim the
            // interface would have to retract afterwards.
            CrashLog.Note($"subscribe: {offer.InAppOfferToken} {Period(offer)}");

            return offer;
        }
        catch (Exception ex)
        {
            CrashLog.Note($"subscribe: lookup failed, {ex.GetType().Name} 0x{ex.HResult:X8}");
            _offer = null;
            return null;
        }
    }

    /// <summary>
    /// How often the offer renews, as its SKU describes it, for a log line.
    ///
    /// The period lives on the SKU, not on the product — there is no billing
    /// period on <see cref="StoreProduct"/> itself — and whether the Store sends
    /// a SKU at all for an add-on it is not selling yet is its business. None of
    /// this decides anything: the sentences shown to the reader about months and
    /// renewal are written once and have to match Partner Center regardless.
    /// </summary>
    private static string Period(StoreProduct offer) =>
        offer.Skus.Count == 0
            ? "sku=none"
            : offer.Skus[0].SubscriptionInfo is { } info
                ? $"subscription every {info.BillingPeriod} {info.BillingPeriodUnit}, trial={info.HasTrialPeriod}"
                : $"sku={offer.Skus[0].StoreId}, not marked as a subscription";

    // ---- Debug-only simulation -------------------------------------------
    //
    // A subscription cannot be bought on a development machine: the Store only
    // completes one for a Store-installed package, and this build is registered
    // from bin. Both halves of the feature — locked and unlocked — would
    // otherwise only be seen after a real release, which is another way of
    // saying never done deliberately. A file named below in LocalState makes a
    // Debug build answer "subscribed"; its absence answers the usual "no", and
    // its contents, if any, are shown as the price so the card reads whole.
    // Compiled out of Release entirely.

    private void ReadSimulation()
    {
#if DEBUG
        try
        {
            if (File.Exists(SimulationFile))
            {
                Subscribed = true;
                Known = true;
                RenewsOn = DateTimeOffset.Now.AddMonths(1);
                Price = File.ReadAllText(SimulationFile).Trim() is { Length: > 0 } shown ? shown : Price ?? "—";

                CrashLog.Note("subscribe: simulated as subscribed (Debug)");
            }
        }
        catch (IOException)
        {
        }
#endif
    }

#if DEBUG
    private static string SimulationFile => Path.Combine(
        Windows.Storage.ApplicationData.Current.LocalFolder.Path, "simulate-subscription.txt");
#endif
}
