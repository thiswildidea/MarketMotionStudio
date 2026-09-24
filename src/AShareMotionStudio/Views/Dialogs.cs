using Microsoft.UI.Xaml.Controls;

namespace AShareMotionStudio.Views;

/// <summary>
/// One dialog at a time.
///
/// <see cref="ContentDialog.ShowAsync()"/> throws when another dialog is already
/// showing, and this app deliberately does not swallow unhandled exceptions —
/// <see cref="Diagnostics.CrashLog"/> writes the fault and lets the process stop,
/// on the grounds that carrying on from an unknown state is worse. Every dialog
/// opens from an <c>async void</c> handler, so a double-click fast enough that
/// the first dialog has not finished becoming modal would close the app. A second
/// click is not an unknown state.
///
/// The extra request is dropped rather than queued. Someone who clicks twice
/// meant to open one dialog, and a second copy appearing after they dismiss the
/// first is a worse answer than nothing.
/// </summary>
public static class Dialogs
{
    /// <summary>
    /// Not synchronised, because dialogs only ever open from the UI thread and a
    /// lock here would be a claim about this type that is not true elsewhere.
    /// </summary>
    private static bool _showing;

    /// <summary>
    /// Shows <paramref name="dialog"/>, or returns
    /// <see cref="ContentDialogResult.None"/> if one is already up.
    ///
    /// None is what dismissing a dialog returns, so callers that test for a
    /// specific button treat a dropped request as a cancellation without needing
    /// to know this exists.
    /// </summary>
    public static async Task<ContentDialogResult> ShowAsync(ContentDialog dialog)
    {
        if (_showing)
        {
            return ContentDialogResult.None;
        }

        _showing = true;

        try
        {
            return await dialog.ShowAsync();
        }
        finally
        {
            _showing = false;
        }
    }
}
