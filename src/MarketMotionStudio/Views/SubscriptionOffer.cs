using System.Threading.Tasks;
using MarketMotionStudio.Localization;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace MarketMotionStudio.Views;

/// <summary>
/// The one place that decides whether a paid-for thing may be done.
///
/// **Seventeen pages have an Export button and seventeen have their own handler,
/// each written out in full — that duplication already exists and is not this
/// file's to fix. What must not be duplicated is the answer to "may this be
/// done": two answers written twice is one page that gives the video away. So
/// every handler asks here, and nothing else decides it.**
///
/// The gate is the whole of the sales argument, which is why it is a dialog
/// rather than a disabled button. A greyed-out button states that something is
/// unavailable and stops there, and somebody who has already decided they want
/// the file has no way to act on that. This answers the two questions a locked
/// button leaves open — *what do I get* and *what does it cost* — in the same
/// breath as the offer.
///
/// It is also why what is metered here is *writing a file* rather than *opening
/// the app*: seventeen pages of live market animation are what somebody came
/// for, and only the two ends that leave home — the video, and the mark that
/// travels with it — are behind this gate.
/// </summary>
public static class SubscriptionOffer
{
    /// <summary>
    /// True when the caller may go ahead.
    ///
    /// <para>
    /// A purchase that succeeds returns true, so the click that was refused —
    /// and which asked the Store for the subscription — finishes the job it was
    /// pressed for. Anything else returns false and the caller stops, having
    /// written nothing to disk.
    /// </para>
    ///
    /// <para>
    /// **The licence is read once more before the person is asked anything**,
    /// which is the other half of that same promise. A subscription can be
    /// bought in the Store's own window — a different window — while this app is
    /// open, and this process is not told about it; without that look the first
    /// press of Export after paying is refused, and being refused straight after
    /// buying reads as "my purchase did not work". It reads the licence and not
    /// the catalogue, so no network round trip stands between the click and the
    /// dialog it has earned.
    /// </para>
    /// </summary>
    /// <param name="root">The page's XAML root, which a dialog in a desktop app has to be given.</param>
    /// <param name="window">The window, whose handle the Store's own dialog is parented to.</param>
    public static async Task<bool> PermitAsync(XamlRoot root, Microsoft.UI.Xaml.Window window)
    {
        var subscription = AppServices.Current.Subscription;

        if (subscription.Subscribed)
        {
            return true;
        }

        if (root is null)
        {
            return false;
        }

        var handle = WinRT.Interop.WindowNative.GetWindowHandle(window);

        if (await subscription.RecheckAsync(handle))
        {
            return true;
        }

        var asked = await Dialogs.ShowAsync(Offer(root, subscription));

        // Each of the three answers is spoken to, rather than only the one that
        // worked. A purchase that cannot be offered leaves the Store's own
        // dialog unopened — nothing appears, nothing is said, and the button
        // looks broken, which is the report this arrived with. The one answer
        // that stays quiet is the person closing the Store's window themselves;
        // that is what closing it means, and there is nothing to explain.
        switch (asked)
        {
            case ContentDialogResult.Primary:
                var outcome = await subscription.SubscribeAsync(handle);

                return outcome switch
                {
                    SubscribeOutcome.Subscribed => true,
                    _ => await TellAsync(root, Explanation(outcome)),
                };

            case ContentDialogResult.Secondary:
                // Restore finding nothing is worth saying too: the person
                // pressing it believes they have already paid, and a button
                // that changes nothing tells them their purchase never
                // happened, which is not the same as nothing having changed.
                return await RestoredAsync(handle, subscription)
                    || await TellAsync(root, "SettingsSubscriptionRestoreMissing");

            // Nothing else is a yes. A dismissal, and a second dialog being
            // dropped by Dialogs.ShowAsync, both leave the caller where it was.
            default:
                return false;
        }
    }

    /// <summary>
    /// The sentence that says how an attempt ended, or null when there is
    /// nothing to say.
    ///
    /// **Shared with the settings card, which is the other place a failed
    /// purchase is reported.** Two places reading the same answer and naming
    /// their own sentence is how the same outcome ends up described two ways —
    /// each true, each uncontradicted by the other, and neither detectable
    /// alone. Which key answers which outcome belongs to one caller of
    /// <c>SubscribeAsync</c>, not two.
    ///
    /// Success and cancellation are both silent here: one is self-evident from
    /// the card changing underneath, and one is what pressing Cancel means.
    /// </summary>
    public static string? Explanation(SubscribeOutcome outcome) =>
        outcome switch
        {
            SubscribeOutcome.Unavailable => "SettingsSubscriptionUnavailable",
            SubscribeOutcome.Failed => "SettingsSubscriptionFailed",
            _ => null,
        };

    /// <summary>
    /// Says <paramref name="key"/> in its own dialog, and returns false, so that
    /// every caller's "was this permitted" reads the same whichever way it went.
    ///
    /// A dialog rather than a note on the page that asked: the caller is a chart
    /// page whose own strip is about the chart, and a purchase that failed is
    /// answered here or not at all.
    /// </summary>
    private static async Task<bool> TellAsync(XamlRoot root, string? key)
    {
        if (root is null || key is null)
        {
            return false;
        }

        await Dialogs.ShowAsync(new ContentDialog
        {
            XamlRoot = root,
            Title = Strings.Get("SubscriptionFailedTitle"),
            Content = new TextBlock
            {
                Text = Strings.Get(key),
                TextWrapping = TextWrapping.Wrap,
            },
            CloseButtonText = Strings.Get("StudioCancel.Content"),
        });

        return false;
    }

    /// <summary>
    /// Whether re-reading the licence found something this session did not know
    /// about yet.
    ///
    /// The most ordinary case is a subscription bought and then left running:
    /// the app has been open since before it started, or the Store granted it
    /// while its own window was in front and this process heard nothing.
    /// </summary>
    private static async Task<bool> RestoredAsync(nint handle, StoreSubscription subscription)
    {
        await subscription.RestoreAsync(handle);

        return subscription.Subscribed;
    }

    /// <summary>
    /// The dialog itself.
    ///
    /// The price is included when there is one to give and left out when there
    /// is not, rather than replaced with a number standing in for one: a build
    /// that cannot reach the Store cannot quote anything, and "—" would read as
    /// a price rather than as its absence.
    ///
    /// Restore is a button on the offer rather than something only Settings
    /// offers, because the person reading this dialog is precisely the person who
    /// believes they have already paid.
    /// </summary>
    private static ContentDialog Offer(XamlRoot root, StoreSubscription subscription)
    {
        var body = Strings.Get("SubscriptionOfferBody");

        if (subscription.Price is { Length: > 0 } price)
        {
            body += "\n\n" + Strings.Format("SubscriptionPerMonth", price);
        }

        return new ContentDialog
        {
            XamlRoot = root,
            Title = Strings.Get("SubscriptionOfferTitle"),
            Content = new TextBlock
            {
                TextWrapping = TextWrapping.Wrap,
                Text = body,
            },
            PrimaryButtonText = Strings.Get("SubscriptionSubscribe.Content"),
            SecondaryButtonText = Strings.Get("SubscriptionRestore.Content"),
            CloseButtonText = Strings.Get("StudioCancel.Content"),
            DefaultButton = ContentDialogButton.Primary,
        };
    }
}
