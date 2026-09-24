using System.Text;

namespace AShareMotionStudio.Diagnostics;

/// <summary>
/// Records unhandled exceptions to a file.
///
/// A XAML-thread failure surfaces in the Windows event log only as a fault in
/// Microsoft.UI.Xaml.dll with exception code 0xc000027b, naming neither the type
/// nor the stack. Without this, diagnosing a startup or navigation crash means
/// guessing. With it, the first line of the file says what happened.
/// </summary>
public static class CrashLog
{
    private static readonly Lock Gate = new();

    public static string Path { get; } = System.IO.Path.Combine(
        Windows.Storage.ApplicationData.Current.LocalFolder.Path,
        "crash.log");

    public static void Install(Microsoft.UI.Xaml.Application app)
    {
        app.UnhandledException += (_, e) =>
        {
            Write("XAML", e.Exception);

            // Left unhandled on purpose. Swallowing it would leave the app in
            // whatever broken state caused the exception, which is worse than
            // stopping, and the record is already written.
        };

        AppDomain.CurrentDomain.UnhandledException += (_, e) =>
            Write("AppDomain", e.ExceptionObject as Exception);

        TaskScheduler.UnobservedTaskException += (_, e) =>
        {
            Write("Task", e.Exception);
            e.SetObserved();
        };
    }

    /// <summary>
    /// Appends a one-line note to the same file.
    ///
    /// For following a path that fails without throwing. The export is the case this was added for:
    /// it stopped somewhere between the button and the encoder, reported nothing, and could not be
    /// located by inspecting the interface — a closed status bar looks identical whether the code
    /// never reached the line that opens it or never ran at all. A trace distinguishes those; nothing
    /// observable from outside does.
    ///
    /// Diagnostics, not logging: these calls are meant to be removed once the path they trace is
    /// working, and NOTES records that debt.
    /// </summary>
    public static void Note(string message)
    {
        try
        {
            lock (Gate)
            {
                Directory.CreateDirectory(System.IO.Path.GetDirectoryName(Path)!);
                File.AppendAllText(Path, $"{DateTimeOffset.Now:HH:mm:ss.fff}  {message}{Environment.NewLine}");
            }
        }
        catch (IOException)
        {
            // Diagnostics must never be the reason an app fails.
        }
    }

    public static void Write(string source, Exception? exception)
    {
        var entry = new StringBuilder()
            .AppendLine(new string('-', 72))
            .AppendLine($"{DateTimeOffset.Now:u}  [{source}]");

        for (var current = exception; current is not null; current = current.InnerException)
        {
            entry.AppendLine($"{current.GetType().FullName}: {current.Message}");

            if (current.StackTrace is { Length: > 0 } stack)
            {
                entry.AppendLine(stack);
            }

            if (current.InnerException is not null)
            {
                entry.AppendLine("--- caused by ---");
            }
        }

        try
        {
            lock (Gate)
            {
                Directory.CreateDirectory(System.IO.Path.GetDirectoryName(Path)!);
                File.AppendAllText(Path, entry.ToString());
            }
        }
        catch (IOException)
        {
            // Diagnostics must never be the reason an app fails.
        }
    }
}
