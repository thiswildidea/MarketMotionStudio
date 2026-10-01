using MarketMotionStudio.Localization;
using Microsoft.UI.Xaml.Controls;

namespace MarketMotionStudio.Pages;

/// <summary>
/// Shared plumbing for the pages that turn an indicator into a video.
///
/// Both of them do the same three long things — fetch a series, render a preview,
/// encode a file — and each needs the same wrapper around them: something to
/// disable while it runs, a way to be stopped, somewhere to report a failure, and
/// a registration so the window can say what is happening. Putting that here means
/// neither page can start long work the rest of the app cannot see.
/// </summary>
public abstract partial class StudioPage : Page
{
    protected AppServices Services => AppServices.Current;

    /// <summary>Where this page reports what happened.</summary>
    protected abstract InfoBar StatusControl { get; }

    /// <summary>
    /// What this page's work is called, for anything reporting it from outside the
    /// page. The page titles already name these in every language, so they are
    /// reused rather than translated again.
    /// </summary>
    protected abstract string JobName { get; }

    /// <summary>
    /// A moment of the animation as the transport writes it: 75 seconds reads "1:15".
    ///
    /// A clock rather than a count of seconds, because a position is something people
    /// locate rather than measure. "0:45 / 1:15" is read off directly as two thirds of
    /// the way through; "45.0 / 75 秒" is the same fact with the division left to do.
    ///
    /// Minutes alone until the composition is an hour long, so the ordinary case does
    /// not carry a leading "0:" that means nothing. The seam at an hour is the one
    /// thing to get wrong here, and <see cref="TimeSpan.Minutes"/> is what gets it
    /// wrong: it is the minutes past the hour, so 3661 seconds would print "1:01" and
    /// lose the hour entirely.
    /// </summary>
    protected static string Clock(TimeSpan value) =>
        value.TotalHours >= 1
            ? $"{(int)value.TotalHours}:{value.Minutes:00}:{value.Seconds:00}"
            : $"{value.Minutes}:{value.Seconds:00}";

    protected void ShowStatus(InfoBarSeverity severity, string message)
    {
        StatusControl.Severity = severity;
        StatusControl.Message = message;
        StatusControl.IsOpen = true;
    }

    /// <summary>
    /// Reports a failure as what was being attempted, and then why.
    ///
    /// "The remote name could not be resolved" is a true sentence about nothing in
    /// particular: the reader is looking at a preview and cannot tell whether the
    /// fetch, the render or the export is what went wrong.
    ///
    /// The reason itself is passed through untranslated. It is either the server's
    /// own words or the framework's, and inventing a translation for someone else's
    /// message would mean guessing at what it said.
    /// </summary>
    protected void ShowFailure(string attemptKey, Exception ex) =>
        ShowStatus(InfoBarSeverity.Error, Strings.Format(attemptKey, Strings.Reason(ex)));

    /// <summary>
    /// Runs page work with the usual wrapper: disable the control that started it,
    /// surface failures as a message instead of an unhandled exception, and always
    /// put the control back.
    ///
    /// The work is also registered as running, so the window's title can say so
    /// while it is behind something else.
    /// </summary>
    protected async Task RunAsync(Control trigger, Func<CancellationToken, Task> work, TimeSpan timeout)
    {
        trigger.IsEnabled = false;

        using var job = Services.Work.Begin(JobName);
        using var cancellation = new CancellationTokenSource(timeout);

        _running = cancellation;
        _stoppedByUser = false;

        try
        {
            await work(cancellation.Token);
        }
        catch (OperationCanceledException)
        {
            job.Cancelled();

            // A timeout and a person pressing Cancel arrive as the same exception
            // and mean opposite things: one is work that failed to finish, the
            // other is work that did what it was told. Telling someone who just
            // stopped an export that it took too long reads as a fault.
            ShowStatus(
                InfoBarSeverity.Warning,
                Strings.Get(_stoppedByUser ? "PageCancelled" : "PageTimedOut"));
        }
        catch (Exception ex)
        {
            // Kept as well as shown: a page that fails sits on its progress line until
            // someone closes the message, and the log is the only place the reason
            // outlives the window.
            Diagnostics.CrashLog.Note($"[page] {JobName} failed: {ex}");

            job.Failed(Strings.Reason(ex));
            ShowStatus(InfoBarSeverity.Error, Strings.Format("PageWorkFailed", JobName, Strings.Reason(ex)));
        }
        finally
        {
            _running = null;
            trigger.IsEnabled = true;
        }
    }

    private CancellationTokenSource? _running;
    private bool _stoppedByUser;

    /// <summary>
    /// Stops the work this page has in progress. Does nothing when there is none,
    /// so a stale button press cannot throw.
    /// </summary>
    protected void CancelRunning()
    {
        if (_running is { } running)
        {
            // Set before cancelling rather than after. Cancel resumes the awaiting
            // continuation, which may read this flag before a line written after
            // the call has run.
            _stoppedByUser = true;
            running.Cancel();
        }
    }

    protected bool IsRunning => _running is not null;
}
