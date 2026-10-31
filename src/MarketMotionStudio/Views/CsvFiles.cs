using System.Text;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using Microsoft.UI.Xaml;
using Windows.Storage;
using Windows.Storage.Pickers;

namespace MarketMotionStudio.Views;

/// <summary>
/// The two file gestures every CSV in this app is moved with: pick one to read, pick one to
/// write.
///
/// <para>
/// **Extracted because three dialogs now ask for the same thing.** 管理持仓 exports and imports a
/// snapshot and a holdings sheet; 导入成交记录 exports and imports the archive. Each of those is
/// four lines of picker boilerplate plus an owner-window call that is easy to get subtly wrong —
/// and getting it wrong is silent: a picker with no owner HWND does not throw, it simply never
/// appears, which reads to the reader as a dead button.
/// </para>
///
/// <para>
/// **The owner window is the whole point of the ceremony.** These are desktop Win32 windows
/// hosting XAML islands: `PickSingleFileAsync` has no way to know which window it belongs to
/// unless it is told, and the result of not telling it is the invisible dialog above.
/// </para>
/// </summary>
public static class CsvFiles
{
    /// <summary>
    /// Asks for a `.csv` (or `.txt`, for a list pasted into one) and hands back its text, or null
    /// when the reader cancelled.
    /// </summary>
    /// <param name="encodingKey">
    /// The message to show when the bytes are not decodable — every caller has its own wording for
    /// "that file is not text this app can read".
    /// </param>
    public static async Task<string?> ReadAsync(string encodingKey)
    {
        if (App.Window is not { } window)
        {
            return null;
        }

        var picker = new FileOpenPicker
        {
            SuggestedStartLocation = PickerLocationId.DocumentsLibrary,
            ViewMode = PickerViewMode.List,
        };

        picker.FileTypeFilter.Add(".csv");
        picker.FileTypeFilter.Add(".txt");

        WinRT.Interop.InitializeWithWindow.Initialize(
            picker, WinRT.Interop.WindowNative.GetWindowHandle(window));

        if (await picker.PickSingleFileAsync() is not { } file)
        {
            return null;
        }

        using var stream = await file.OpenStreamForReadAsync();
        using var memory = new MemoryStream();

        await stream.CopyToAsync(memory);

        // Bytes to text is not `Encoding.UTF8.GetString`: a CSV off a Chinese broker's site is
        // GBK as often as not, and a reader who exports from this app and re-imports it gets a BOM
        // they never asked for. `HoldingsSheet` already knows both.
        return HoldingsSheet.TryDecode(memory.ToArray(), out var text)
            ? text
            : throw new InvalidOperationException(Strings.Get(encodingKey));
    }

    /// <summary>
    /// Writes <paramref name="csv"/> to a file the reader names. False when they cancelled.
    /// </summary>
    public static async Task<bool> WriteAsync(string suggested, string csv)
    {
        if (App.Window is not { } window)
        {
            return false;
        }

        var picker = new FileSavePicker
        {
            SuggestedStartLocation = PickerLocationId.DocumentsLibrary,
            SuggestedFileName = suggested,
        };

        picker.FileTypeChoices.Add("CSV", [".csv"]);

        WinRT.Interop.InitializeWithWindow.Initialize(
            picker, WinRT.Interop.WindowNative.GetWindowHandle(window));

        if (await picker.PickSaveFileAsync() is not { } file)
        {
            return false;
        }

        // **Bytes, not text.** `WriteTextAsync` normalises line endings, and this file's rows are
        // CRLF by construction (see `TradesToCsv`): every exporter in this app writes CRLF and
        // every reader accepts either, so a save that quietly rewrote them would make the round
        // trip depend on which path wrote the file. The BOM is prepended here for the reason in
        // the comment above.
        var bytes = Encoding.UTF8.GetPreamble()
            .Concat(Encoding.UTF8.GetBytes(csv))
            .ToArray();

        await FileIO.WriteBytesAsync(file, bytes);

        return true;
    }
}
