using AShareMotionStudio.Localization;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.Windows.AppLifecycle;
using Windows.Storage;

namespace AShareMotionStudio.Pages;

public sealed partial class SettingsPage : Page
{
    /// <summary>
    /// The languages shipped with the app. The empty tag means "whatever Windows is
    /// set to", which is the default and what most users want.
    /// </summary>
    private static readonly (string Tag, string Label)[] Languages =
    [
        (string.Empty, "SettingsLanguageSystem.Content"),
        ("en-US", "English"),
        ("de", "Deutsch"),
        ("es", "Español"),
        ("fr", "Français"),
        ("it", "Italiano"),
        ("pl", "Polski"),
        ("pt-BR", "Português (Brasil)"),
        ("cs", "Čeština"),
        ("tr", "Türkçe"),
        ("ru", "Русский"),
        ("ja", "日本語"),
        ("ko", "한국어"),
        ("zh-Hans", "简体中文"),
        ("zh-Hant", "繁體中文"),
    ];

    /// <summary>
    /// Follow Windows first, because it is the default and what most people want;
    /// the other two are for overriding it.
    /// </summary>
    private static readonly (ElementTheme Theme, string Label)[] Themes =
    [
        (ElementTheme.Default, "SettingsThemeSystem"),
        (ElementTheme.Light, "SettingsThemeLight"),
        (ElementTheme.Dark, "SettingsThemeDark"),
    ];

    private bool _loading = true;

    /// <summary>
    /// Where to write when something is wrong. The same address the help document
    /// ends with; the two are reached in different moods, and someone whose export
    /// just failed is not reading a manual.
    /// </summary>
    private const string ContactAddress = "gaqo@outlook.com";

    public SettingsPage()
    {
        InitializeComponent();

        ContactLink.Content = ContactAddress;
        VersionText.Text = Strings.Format("SettingsVersion", AppVersion);

        foreach (var (tag, label) in Languages)
        {
            LanguageCombo.Items.Add(new ComboBoxItem
            {
                // The system option is translated; the language names are not,
                // because a language should be listed in its own language.
                Content = tag.Length == 0 ? Strings.Get(label) : label,
                Tag = tag,
            });
        }

        LanguageCombo.SelectedIndex = Math.Max(0, Array.FindIndex(Languages, l => l.Tag == LanguageSettings.Current));

        foreach (var (theme, label) in Themes)
        {
            ThemeCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(label), Tag = theme });
        }

        ThemeCombo.SelectedIndex = Math.Max(0, Array.FindIndex(Themes, t => t.Theme == ThemeSettings.Current));

        StoragePathText.Text = ApplicationData.Current.LocalFolder.Path;

        _loading = false;

        RefreshOutputFolder();
    }

    /// <summary>
    /// Says where exports go, or that nothing has been chosen and the first one will
    /// ask.
    ///
    /// The path is read from what was recorded alongside the grant rather than by
    /// resolving the grant, because this is a label and resolving it is a file-system
    /// round trip that can fail — and a Settings page that reports a folder as
    /// missing because a drive is asleep is answering a question nobody asked.
    /// </summary>
    private void RefreshOutputFolder()
    {
        var path = OutputFolder.RememberedPath;
        var chosen = path is { Length: > 0 };

        OutputPathText.Text = chosen ? path! : Strings.Get("SettingsOutputNotSet");
        ForgetOutputButton.IsEnabled = chosen;
    }

    private async void OnChooseOutput(object sender, RoutedEventArgs e)
    {
        if (App.Window is not { } window)
        {
            return;
        }

        try
        {
            if (await OutputFolder.ChooseAsync(window) is not null)
            {
                RefreshOutputFolder();
            }
        }
        catch (Exception ex)
        {
            Status.Severity = InfoBarSeverity.Error;
            Status.Message = Strings.Format("SettingsOutputFailed", Strings.Reason(ex));
            RestartButton.Visibility = Visibility.Collapsed;
            Status.IsOpen = true;
        }
    }

    private void OnForgetOutput(object sender, RoutedEventArgs e)
    {
        OutputFolder.Forget();
        RefreshOutputFolder();
    }

    private void OnThemeChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_loading || ThemeCombo.SelectedItem is not ComboBoxItem { Tag: ElementTheme theme })
        {
            return;
        }

        ThemeSettings.Current = theme;

        // Applied on the spot. A theme is re-read by elements already on screen, so
        // unlike the language there is nothing to restart for.
        App.Window?.ApplyTheme();
    }

    private void OnLanguageChanged(object sender, SelectionChangedEventArgs e)
    {
        // Setting the override while the combo is being populated would rewrite the
        // stored preference with whatever happened to be selected first.
        if (_loading || LanguageCombo.SelectedItem is not ComboBoxItem { Tag: string tag })
        {
            return;
        }

        LanguageSettings.Choose(tag);

        // Stored but not applied: see LanguageSettings.Choose. Nothing on screen
        // changes yet, so the restart that changes all of it is offered rather than
        // only described.
        Status.Severity = InfoBarSeverity.Informational;
        Status.Message = Strings.Get("SettingsLanguageRestart.Text");
        RestartButton.Visibility = Visibility.Visible;
        Status.IsOpen = true;
    }

    /// <summary>
    /// The package's version, which is the one a support reply would ask for. Read
    /// from the package rather than from an assembly attribute: the package version
    /// is what the Store shows and what an update changes.
    /// </summary>
    private static string AppVersion
    {
        get
        {
            var v = Windows.ApplicationModel.Package.Current.Id.Version;
            return $"{v.Major}.{v.Minor}.{v.Build}.{v.Revision}";
        }
    }

    /// <summary>
    /// Opens a mail draft already carrying the app and its version. Nothing else is
    /// filled in — a body pre-written by the app would be text the sender has to read
    /// and delete before writing theirs.
    /// </summary>
    private async void OnContact(object sender, RoutedEventArgs e)
    {
        var subject = Strings.Format("SettingsContactSubject", AppVersion);
        var uri = new Uri($"mailto:{ContactAddress}?subject={Uri.EscapeDataString(subject)}");

        try
        {
            await Windows.System.Launcher.LaunchUriAsync(uri);
        }
        catch (Exception ex)
        {
            // A machine with no mail client is a real machine. Saying so beats a
            // click that appears to do nothing.
            Status.Severity = InfoBarSeverity.Warning;
            Status.Message = Strings.Format("SettingsContactFailed", ContactAddress, Strings.Reason(ex));
            RestartButton.Visibility = Visibility.Collapsed;
            Status.IsOpen = true;
        }
    }

    private void OnRestartNow(object sender, RoutedEventArgs e)
    {
        // The stored choice is applied during startup, before any window exists to
        // be left behind in the previous language.
        var failure = AppInstance.Restart(string.Empty);

        // Restart only returns when it did not happen.
        Status.Severity = InfoBarSeverity.Error;
        Status.Message = Strings.Format("SettingsRestartFailed", failure);
        RestartButton.Visibility = Visibility.Collapsed;
    }
}
