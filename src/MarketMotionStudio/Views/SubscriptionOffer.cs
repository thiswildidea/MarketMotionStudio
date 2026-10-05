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

        var asked = await Dialogs.ShowAsync(Offer(root, subscription));

        return asked switch
        {
            ContentDialogResult.Primary => await subscription.SubscribeAsync(handle) is SubscribeOutcome.Subscribed,
            ContentDialogResult.Secondary => await RestoredAsync(handle, subscription),

            // Nothing else is a yes. A dismissal, a second dialog being dropped
            // by Dialogs.ShowAsync, and a purchase the Store refused all leave
            // the caller exactly where it was.
            _ => false,
        };
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
