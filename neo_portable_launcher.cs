// Neo AI Terminal - tiny Windows bootstrap launcher.
// Runtime payloads are downloaded from official Python.org / Node.js.org endpoints
// on first launch and kept in the sibling runtime folder.
using System;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Web.Script.Serialization;
using System.Windows.Forms;

internal static class NeoPortableLauncher
{
    private const string PythonVersion = "3.13.17";
    private const string PythonArchive = "python-3.13.17-embeddable-amd64.zip";
    private const string PythonUrl = "https://www.python.org/ftp/python/3.13.17/python-3.13.17-embeddable-amd64.zip";
    // SHA-256 from Python.org's official windows-3.13.17.json release manifest.
    private const string PythonSha256 = "0ba1ee4bfcbdc3a559d27e2e9ce76d04a7839947a23f46375872c755c0d463b8";
    private const string NodeIndexUrl = "https://nodejs.org/dist/index.json";
    private const string ServerUrl = "http://127.0.0.1:8765";

    [STAThread]
    private static void Main()
    {
        if (!Environment.Is64BitOperatingSystem)
        {
            MessageBox.Show("نسخهٔ Lightweight به ویندوز ۶۴ بیتی نیاز دارد.",
                "Neo AI Terminal", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }

        bool created;
        using (Mutex mutex = new Mutex(true, "Local\\NeoAITerminal.Lightweight.Launcher", out created))
        {
            if (!created)
            {
                TryOpenDashboard();
                return;
            }
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new BootstrapForm());
            GC.KeepAlive(mutex);
        }
    }

    internal static readonly string AppRoot = Path.GetDirectoryName(Process.GetCurrentProcess().MainModule.FileName);
    internal static readonly string RuntimeRoot = Path.Combine(AppRoot, "runtime");
    internal static readonly string PythonRoot = Path.Combine(RuntimeRoot, "python");
    internal static readonly string NodeRoot = Path.Combine(RuntimeRoot, "node");
    internal static readonly string PythonExe = Path.Combine(PythonRoot, "python.exe");
    internal static readonly string NodeExe = Path.Combine(NodeRoot, "node.exe");
    internal static readonly string LogRoot = Path.Combine(RuntimeRoot, "logs");
    private static readonly object LogLock = new object();

    internal static void SetupAndLaunch(Action<string, int> report)
    {
        ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12;
        ServicePointManager.Expect100Continue = false;
        Directory.CreateDirectory(RuntimeRoot);
        Directory.CreateDirectory(LogRoot);

        string[] required = {
            "neo_launcher.py", "web_app.py", "duck_cli.py", "duckai_catalog.py",
            "duck_i18n.py", "duck_voice.py", "api_providers.py", "secure_store.py",
            "jsa_jsdom.js", "requirements-portable.txt", "package.json"
        };
        foreach (string name in required)
        {
            if (!File.Exists(Path.Combine(AppRoot, name)))
                throw new InvalidOperationException("Application files are incomplete. Extract the entire Neo AI Terminal folder, not only the EXE. Missing: " + name);
        }
        if (!Directory.Exists(Path.Combine(AppRoot, "web")) || !File.Exists(Path.Combine(AppRoot, "web", "index.html")))
            throw new InvalidOperationException("The web interface files are missing. Extract the full Portable ZIP again.");

        EnsurePython(report);
        EnsureNode(report);
        EnsureNodePackages(report);
        report("در حال بررسی داشبورد محلی...", 90);

        if (!IsHealthy())
        {
            report("در حال اجرای Neo AI Terminal...", 95);
            StartServer();
            if (!WaitForHealth(45))
            {
                string tail = ReadServerLogsTail(3500);
                throw new InvalidOperationException("The local server did not become ready.\r\n\r\n" + tail);
            }
        }
        report("آماده شد؛ داشبورد در مرورگر باز می‌شود...", 100);
        TryOpenDashboard();
    }

    private static void EnsurePython(Action<string, int> report)
    {
        string requirements = Path.Combine(AppRoot, "requirements-portable.txt");
        string marker = Path.Combine(RuntimeRoot, "python-requirements.sha256");
        string requirementsHash = Sha256File(requirements);
        bool runtimePresent = File.Exists(PythonExe) && File.Exists(Path.Combine(PythonRoot, "python313.dll"));

        if (!runtimePresent)
        {
            report("در حال دریافت Python " + PythonVersion + "...", 8);
            string archive = Path.Combine(RuntimeRoot, PythonArchive);
            DownloadFile(PythonUrl, archive, PythonSha256, delegate(int p) {
                report("در حال دریافت Python " + PythonVersion + "... " + p + "%", 8 + (p * 12 / 100));
            });
            report("در حال آماده‌سازی Python قابل‌حمل...", 21);
            if (Directory.Exists(PythonRoot)) Directory.Delete(PythonRoot, true);
            Directory.CreateDirectory(PythonRoot);
            ZipFile.ExtractToDirectory(archive, PythonRoot);
            File.Delete(archive);
            ConfigureEmbeddedPython();
        }
        else
        {
            ConfigureEmbeddedPython();
        }

        bool packagesReady = File.Exists(marker) && File.ReadAllText(marker).Trim().Equals(requirementsHash, StringComparison.OrdinalIgnoreCase)
            && PythonCheck();
        if (!packagesReady)
        {
            report("در حال آماده‌سازی نصب‌کنندهٔ بسته‌های Python...", 23);
            string getPip = Path.Combine(RuntimeRoot, "get-pip.py");
            DownloadFile("https://bootstrap.pypa.io/pip/3.13/get-pip.py", getPip, null, delegate(int p) {
                report("در حال دریافت نصب‌کنندهٔ بسته‌های Python...", 23);
            });
            RunProcess(PythonExe, Quote(getPip) + " --disable-pip-version-check --no-warn-script-location", PythonRoot, null, "Installing pip");
            TryDeleteFile(getPip);

            report("در حال نصب وابستگی‌های Python (فقط اجرای اول)...", 28);
            string args = "-m pip install --disable-pip-version-check --no-warn-script-location --no-cache-dir --only-binary=:all: -r " + Quote(requirements);
            RunProcess(PythonExe, args, AppRoot, null, "Installing Python dependencies");
            if (!PythonCheck())
                throw new InvalidOperationException("Python packages were installed, but the Neo AI Terminal modules could not be imported. Check runtime\\logs\\setup.log.");
            File.WriteAllText(marker, requirementsHash, Encoding.ASCII);
        }
    }

    private static void ConfigureEmbeddedPython()
    {
        string pth = Path.Combine(PythonRoot, "python313._pth");
        if (!File.Exists(pth))
            throw new InvalidOperationException("The downloaded Python runtime is incomplete (python313._pth not found).");
        Directory.CreateDirectory(Path.Combine(PythonRoot, "Lib", "site-packages"));
        string[] lines = File.ReadAllLines(pth);
        bool hasSitePackages = false;
        var updated = new System.Collections.Generic.List<string>();
        foreach (string line in lines)
        {
            string clean = line.Trim();
            if (clean.Equals("import site", StringComparison.OrdinalIgnoreCase)
                || clean.Equals("#import site", StringComparison.OrdinalIgnoreCase)) continue;
            if (clean.Equals("Lib\\site-packages", StringComparison.OrdinalIgnoreCase))
            {
                hasSitePackages = true;
                continue;
            }
            updated.Add(line);
        }
        // Add site-packages before importing site, as required by the embeddable
        // Python path configuration format.
        if (!hasSitePackages) updated.Add("Lib\\site-packages");
        updated.Add("import site");
        File.WriteAllLines(pth, updated.ToArray(), new UTF8Encoding(false));
    }

    private static bool PythonCheck()
    {
        if (!File.Exists(PythonExe)) return false;
        string check = "import requests, PIL, fastapi, uvicorn, multipart; import web_app";
        try { return RunProcess(PythonExe, "-c " + Quote(check), AppRoot, null, "Checking Python") == 0; }
        catch { return false; }
    }

    private static void EnsureNode(Action<string, int> report)
    {
        string npmCli = Path.Combine(NodeRoot, "node_modules", "npm", "bin", "npm-cli.js");
        if (File.Exists(NodeExe) && File.Exists(npmCli)) return;

        report("در حال بررسی آخرین نسخهٔ پایدار Node.js...", 44);
        string index = DownloadText(NodeIndexUrl);
        var serializer = new JavaScriptSerializer();
        object[] versions = serializer.DeserializeObject(index) as object[];
        string version = null;
        if (versions != null)
        {
            foreach (object item in versions)
            {
                var record = item as System.Collections.Generic.Dictionary<string, object>;
                if (record == null || !record.ContainsKey("lts")) continue;
                // Non-LTS entries use boolean false; LTS entries carry a codename string.
                if (!(record["lts"] is string) || String.IsNullOrWhiteSpace(Convert.ToString(record["lts"]))) continue;
                if (record.ContainsKey("version")) { version = Convert.ToString(record["version"]); break; }
            }
        }
        if (String.IsNullOrWhiteSpace(version) || !Regex.IsMatch(version, @"^v\d+\.\d+\.\d+$"))
            throw new InvalidOperationException("Could not identify the current stable Node.js LTS release from nodejs.org.");

        string fileName = "node-" + version + "-win-x64.zip";
        string baseUrl = "https://nodejs.org/dist/" + version + "/";
        string sums = DownloadText(baseUrl + "SHASUMS256.txt");
        Match hashMatch = Regex.Match(sums, @"(?im)^([0-9a-f]{64})\s+\*?" + Regex.Escape(fileName) + @"\s*$");
        if (!hashMatch.Success)
            throw new InvalidOperationException("Node.js checksum entry was not found on the official release server.");

        report("در حال دریافت Node.js " + version + " LTS...", 46);
        string archive = Path.Combine(RuntimeRoot, fileName);
        string expectedHash = hashMatch.Groups[1].Value;
        DownloadFile(baseUrl + fileName, archive, expectedHash, delegate(int p) {
            report("در حال دریافت Node.js " + version + " LTS... " + p + "%", 46 + (p * 18 / 100));
        });

        report("در حال آماده‌سازی Node.js...", 65);
        string temp = Path.Combine(RuntimeRoot, "node-extract");
        if (Directory.Exists(temp)) Directory.Delete(temp, true);
        if (Directory.Exists(NodeRoot)) Directory.Delete(NodeRoot, true);
        Directory.CreateDirectory(temp);
        ZipFile.ExtractToDirectory(archive, temp);
        string extracted = Path.Combine(temp, "node-" + version + "-win-x64");
        if (!Directory.Exists(extracted))
            throw new InvalidOperationException("The downloaded Node.js archive has an unexpected folder layout.");
        Directory.Move(extracted, NodeRoot);
        Directory.Delete(temp, true);
        File.Delete(archive);
        if (!File.Exists(NodeExe) || !File.Exists(npmCli))
            throw new InvalidOperationException("Node.js was extracted, but its node.exe or npm files are missing.");
    }

    private static void EnsureNodePackages(Action<string, int> report)
    {
        string modules = Path.Combine(AppRoot, "node_modules");
        string marker = Path.Combine(RuntimeRoot, "node-packages.sha256");
        string packageHash = Sha256File(Path.Combine(AppRoot, "package.json"));
        string jsdom = Path.Combine(modules, "jsdom", "package.json");
        string fontCss = Path.Combine(modules, "vazir-font", "dist", "font-face.css");
        bool ready = File.Exists(marker) && File.ReadAllText(marker).Trim().Equals(packageHash, StringComparison.OrdinalIgnoreCase)
            && File.Exists(jsdom) && File.Exists(fontCss);
        if (ready) return;

        report("در حال نصب موتور JavaScript داک‌ای‌آی و فونت فارسی...", 68);
        Directory.CreateDirectory(modules);
        string npmScript = Path.Combine(NodeRoot, "node_modules", "npm", "bin", "npm-cli.js");
        var env = new System.Collections.Generic.Dictionary<string, string>();
        env["npm_config_cache"] = Path.Combine(RuntimeRoot, "npm-cache");
        env["npm_config_audit"] = "false";
        env["npm_config_fund"] = "false";
        env["npm_config_update_notifier"] = "false";
        env["PATH"] = NodeRoot + Path.PathSeparator + Environment.GetEnvironmentVariable("PATH");
        RunProcess(NodeExe, Quote(npmScript) + " install --omit=dev --no-audit --no-fund --no-progress", AppRoot, env,
            "Installing JavaScript dependencies");
        if (!File.Exists(jsdom) || !File.Exists(fontCss))
            throw new InvalidOperationException("npm completed, but jsdom or Vazirmatn font files are missing. Check runtime\\logs\\setup.log.");
        File.WriteAllText(marker, packageHash, Encoding.ASCII);
        TryDeleteDirectory(Path.Combine(RuntimeRoot, "npm-cache"));
    }

    private static void StartServer()
    {
        // Detach the server from this short-lived GUI bootstrapper. Start-Process
        // keeps the Python process alive after the launcher closes and writes its
        // streams directly to files instead of leaving broken redirected pipes.
        string powershell = Path.Combine(Environment.SystemDirectory,
            "WindowsPowerShell\\v1.0\\powershell.exe");
        if (!File.Exists(powershell))
            throw new InvalidOperationException("Windows PowerShell was not found; it is required to start the background local server.");

        string stdout = Path.Combine(LogRoot, "server.stdout.log");
        string stderr = Path.Combine(LogRoot, "server.stderr.log");
        string script = "$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; " +
            "$env:PYTHONUNBUFFERED='1'; $env:NEO_SKIP_AUTO_OPEN='1'; " +
            "$env:NODE_PATH=" + PowerShellQuote(Path.Combine(AppRoot, "node_modules")) + "; " +
            "$env:PATH=" + PowerShellQuote(NodeRoot) + " + ';' + $env:PATH; " +
            "$p = Start-Process -FilePath " + PowerShellQuote(PythonExe) +
            " -ArgumentList " + PowerShellQuote(Quote(Path.Combine(AppRoot, "neo_launcher.py"))) +
            " -WorkingDirectory " + PowerShellQuote(AppRoot) +
            " -WindowStyle Hidden -RedirectStandardOutput " + PowerShellQuote(stdout) +
            " -RedirectStandardError " + PowerShellQuote(stderr) + " -PassThru; " +
            "if ($null -eq $p) { throw 'Python server process was not created.' }";

        RunProcess(powershell, "-NoProfile -NonInteractive -ExecutionPolicy Bypass -Command " + Quote(script),
            AppRoot, null, "Starting local server");
    }

    private static string PowerShellQuote(string value)
    {
        return "'" + (value ?? "").Replace("'", "''") + "'";
    }

    private static string ReadServerLogsTail(int maxChars)
    {
        string setup = ReadLogTail(Path.Combine(LogRoot, "setup.log"), maxChars / 3);
        string stdout = ReadLogTail(Path.Combine(LogRoot, "server.stdout.log"), maxChars / 3);
        string stderr = ReadLogTail(Path.Combine(LogRoot, "server.stderr.log"), maxChars / 3);
        return "--- setup.log ---\r\n" + setup + "\r\n--- server.stdout.log ---\r\n" + stdout +
            "\r\n--- server.stderr.log ---\r\n" + stderr;
    }

    private static bool WaitForHealth(int seconds)
    {
        DateTime until = DateTime.UtcNow.AddSeconds(seconds);
        while (DateTime.UtcNow < until)
        {
            if (IsHealthy()) return true;
            Thread.Sleep(500);
        }
        return IsHealthy();
    }

    private static bool IsHealthy()
    {
        try
        {
            var req = (HttpWebRequest)WebRequest.Create(ServerUrl + "/api/health");
            req.Timeout = 1200;
            req.ReadWriteTimeout = 1200;
            req.Proxy = null;
            using (var response = (HttpWebResponse)req.GetResponse()) return (int)response.StatusCode == 200;
        }
        catch { return false; }
    }

    private static void TryOpenDashboard()
    {
        try { Process.Start(new ProcessStartInfo(ServerUrl) { UseShellExecute = true }); }
        catch { }
    }

    private static string DownloadText(string url)
    {
        var req = (HttpWebRequest)WebRequest.Create(url);
        req.UserAgent = "Neo-AI-Terminal-Lightweight/1.0";
        req.Timeout = 60000;
        req.ReadWriteTimeout = 60000;
        using (var response = (HttpWebResponse)req.GetResponse())
        using (var stream = response.GetResponseStream())
        using (var reader = new StreamReader(stream, Encoding.UTF8)) return reader.ReadToEnd();
    }

    private static void DownloadFile(string url, string destination, string expectedSha256, Action<int> progress)
    {
        string partial = destination + ".part";
        TryDeleteFile(partial);
        try
        {
            var req = (HttpWebRequest)WebRequest.Create(url);
            req.UserAgent = "Neo-AI-Terminal-Lightweight/1.0";
            req.Timeout = 300000;
            req.ReadWriteTimeout = 300000;
            using (var response = (HttpWebResponse)req.GetResponse())
            using (var input = response.GetResponseStream())
            using (var output = new FileStream(partial, FileMode.Create, FileAccess.Write, FileShare.None))
            {
                long total = response.ContentLength;
                long received = 0;
                byte[] buffer = new byte[65536];
                int read;
                int last = -1;
                while ((read = input.Read(buffer, 0, buffer.Length)) > 0)
                {
                    output.Write(buffer, 0, read);
                    received += read;
                    if (total > 0 && progress != null)
                    {
                        int current = (int)Math.Min(100, (received * 100L) / total);
                        if (current != last) { last = current; progress(current); }
                    }
                }
            }
            if (!String.IsNullOrEmpty(expectedSha256))
            {
                string actual = Sha256File(partial);
                if (!actual.Equals(expectedSha256, StringComparison.OrdinalIgnoreCase))
                    throw new InvalidOperationException("Security check failed: SHA-256 does not match for " + Path.GetFileName(destination));
            }
            if (File.Exists(destination)) File.Delete(destination);
            File.Move(partial, destination);
        }
        catch
        {
            TryDeleteFile(partial);
            throw;
        }
    }

    private static int RunProcess(string executable, string arguments, string workingDirectory,
        System.Collections.Generic.Dictionary<string, string> environment, string label)
    {
        var info = new ProcessStartInfo();
        info.FileName = executable;
        info.Arguments = arguments;
        info.WorkingDirectory = workingDirectory;
        info.UseShellExecute = false;
        info.CreateNoWindow = true;
        info.WindowStyle = ProcessWindowStyle.Hidden;
        info.RedirectStandardOutput = true;
        info.RedirectStandardError = true;
        if (environment != null)
            foreach (var pair in environment) info.EnvironmentVariables[pair.Key] = pair.Value;
        using (Process process = new Process())
        {
            process.StartInfo = info;
            var output = new StringBuilder();
            var error = new StringBuilder();
            process.OutputDataReceived += delegate(object sender, DataReceivedEventArgs args) { if (args.Data != null) lock (output) { output.AppendLine(args.Data); } };
            process.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs args) { if (args.Data != null) lock (error) { error.AppendLine(args.Data); } };
            try
            {
                process.Start();
                process.BeginOutputReadLine();
                process.BeginErrorReadLine();
                process.WaitForExit();
                process.WaitForExit();
            }
            catch (Exception ex)
            {
                AppendLog(label + " failed to start: " + ex);
                throw new InvalidOperationException(label + " could not start. " + ex.Message);
            }
            string outText, errText;
            lock (output) outText = output.ToString();
            lock (error) errText = error.ToString();
            if (outText.Length > 0) AppendLog("[" + label + "] " + outText);
            if (errText.Length > 0) AppendLog("[" + label + " STDERR] " + errText);
            if (process.ExitCode != 0)
            {
                string combined = (errText + "\r\n" + outText).Trim();
                if (combined.Length > 2600) combined = combined.Substring(combined.Length - 2600);
                throw new InvalidOperationException(label + " failed (exit code " + process.ExitCode + ").\r\n" + combined + "\r\n\r\nSee runtime\\logs\\setup.log for details.");
            }
            return process.ExitCode;
        }
    }

    private static string Sha256File(string path)
    {
        using (var sha = SHA256.Create())
        using (var stream = File.OpenRead(path))
        {
            byte[] hash = sha.ComputeHash(stream);
            var result = new StringBuilder(hash.Length * 2);
            foreach (byte b in hash) result.Append(b.ToString("x2"));
            return result.ToString();
        }
    }

    private static string Quote(string value)
    {
        // Windows CRT command-line quoting: only backslashes before quotes or the
        // closing quote are doubled. Ordinary path separators remain untouched.
        value = value ?? "";
        var result = new StringBuilder();
        result.Append('"');
        int slashes = 0;
        foreach (char ch in value)
        {
            if (ch == '\\') { slashes++; continue; }
            if (ch == '"')
            {
                result.Append('\\', slashes * 2 + 1);
                result.Append('"');
                slashes = 0;
                continue;
            }
            if (slashes > 0) result.Append('\\', slashes);
            result.Append(ch);
            slashes = 0;
        }
        if (slashes > 0) result.Append('\\', slashes * 2);
        result.Append('"');
        return result.ToString();
    }

    private static void AppendLog(string message)
    {
        try
        {
            lock (LogLock)
                File.AppendAllText(Path.Combine(LogRoot, "setup.log"), DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + " " + message + Environment.NewLine, Encoding.UTF8);
        }
        catch { }
    }

    private static string ReadLogTail(string path, int maxChars)
    {
        try
        {
            if (!File.Exists(path)) return "No server log is available yet.";
            string value = File.ReadAllText(path, Encoding.UTF8);
            return value.Length <= maxChars ? value : value.Substring(value.Length - maxChars);
        }
        catch { return "Could not read the server log."; }
    }

    private static void TryDeleteFile(string path) { try { if (File.Exists(path)) File.Delete(path); } catch { } }
    private static void TryDeleteDirectory(string path) { try { if (Directory.Exists(path)) Directory.Delete(path, true); } catch { } }
}

internal sealed class BootstrapForm : Form
{
    private readonly Label heading;
    private readonly Label status;
    private readonly ProgressBar progress;
    private readonly TextBox details;
    private readonly Button retry;
    private readonly Button close;
    private bool working;

    internal BootstrapForm()
    {
        Text = "راه‌اندازی Neo AI Terminal · نسخهٔ پرتابل";
        Width = 560;
        Height = 245;
        MinimumSize = new System.Drawing.Size(560, 245);
        StartPosition = FormStartPosition.CenterScreen;
        RightToLeft = RightToLeft.Yes;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        MinimizeBox = true;

        heading = new Label();
        heading.Text = "NEO AI TERMINAL";
        heading.Font = new System.Drawing.Font("Segoe UI", 15F, System.Drawing.FontStyle.Bold);
        heading.TextAlign = System.Drawing.ContentAlignment.MiddleRight;
        heading.SetBounds(22, 16, 500, 32);
        Controls.Add(heading);

        status = new Label();
        status.Text = "آماده‌سازی اجرای اولیه...";
        status.RightToLeft = RightToLeft.Yes;
        status.TextAlign = System.Drawing.ContentAlignment.MiddleRight;
        status.SetBounds(24, 58, 500, 24);
        Controls.Add(status);

        progress = new ProgressBar();
        progress.SetBounds(24, 88, 500, 18);
        progress.Style = ProgressBarStyle.Marquee;
        progress.MarqueeAnimationSpeed = 24;
        Controls.Add(progress);

        details = new TextBox();
        details.Multiline = true;
        details.RightToLeft = RightToLeft.Yes;
        details.ReadOnly = true;
        details.ScrollBars = ScrollBars.Vertical;
        details.Visible = false;
        details.SetBounds(24, 116, 500, 55);
        Controls.Add(details);

        retry = new Button();
        retry.Text = "تلاش دوباره";
        retry.SetBounds(340, 178, 85, 28);
        retry.Visible = false;
        retry.Click += delegate { details.Visible = false; retry.Visible = false; close.Visible = false; StartWork(); };
        Controls.Add(retry);

        close = new Button();
        close.Text = "بستن";
        close.SetBounds(439, 178, 85, 28);
        close.Visible = false;
        close.Click += delegate { Close(); };
        Controls.Add(close);

        Shown += delegate { StartWork(); };
    }

    private void StartWork()
    {
        if (working) return;
        working = true;
        retry.Enabled = false;
        progress.Style = ProgressBarStyle.Marquee;
        status.Text = "در حال شروع...";
        var worker = new BackgroundWorker();
        worker.DoWork += delegate
        {
            NeoPortableLauncher.SetupAndLaunch(delegate(string message, int value)
            {
                if (IsDisposed) return;
                try
                {
                    BeginInvoke(new Action(delegate
                    {
                        status.Text = message;
                        if (value >= 0 && value <= 100)
                        {
                            progress.Style = ProgressBarStyle.Continuous;
                            progress.Value = value;
                        }
                    }));
                }
                catch { }
            });
        };
        worker.RunWorkerCompleted += delegate(object sender, RunWorkerCompletedEventArgs args)
        {
            working = false;
            if (args.Error == null)
            {
                Close();
                return;
            }
            progress.Style = ProgressBarStyle.Continuous;
            progress.Value = 0;
            status.Text = "اجرای Neo AI Terminal با خطا مواجه شد.";
            details.Text = args.Error.GetBaseException().Message;
            details.Visible = true;
            retry.Visible = true;
            retry.Enabled = true;
            close.Visible = true;
            Height = 300;
        };
        worker.RunWorkerAsync();
    }
}
