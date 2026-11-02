using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Reflection;

internal static class Setup
{
    private const string PayloadResource = "ZelixMinecraftLoader.payload.zip";

    private static int Main(string[] arguments)
    {
        try
        {
            Dictionary<string, string> options = ParseArguments(arguments);
            string gameDirectory = GetOption(options, "--game-dir");
            string version = GetOption(options, "--version");
            string installDirectory = GetOption(options, "--install-dir");

            if (String.IsNullOrWhiteSpace(gameDirectory))
            {
                string defaultGameDirectory = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                    ".minecraft");
                Console.Write("Minecraft game directory [{0}]: ", defaultGameDirectory);
                string entered = Console.ReadLine();
                gameDirectory = String.IsNullOrWhiteSpace(entered)
                    ? defaultGameDirectory
                    : entered.Trim().Trim('"');
            }

            if (String.IsNullOrWhiteSpace(version))
            {
                Console.Write("Minecraft Java version to configure (1.8.8 or 1.12.2): ");
                version = Console.ReadLine();
            }
            if (version != "1.8.8" && version != "1.12.2")
            {
                throw new InvalidOperationException(
                    "Choose a supported Minecraft Java version: 1.8.8 or 1.12.2.");
            }

            gameDirectory = Path.GetFullPath(gameDirectory);
            string versionDirectory = Path.Combine(
                gameDirectory, "versions", version);
            if (!Directory.Exists(versionDirectory))
            {
                throw new DirectoryNotFoundException(
                    "Minecraft " + version + " is not installed under " + gameDirectory
                    + ". Install and launch that profile once, then rerun setup.");
            }

            if (String.IsNullOrWhiteSpace(installDirectory))
            {
                installDirectory = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                    "Zelix", "MinecraftLoader");
            }
            installDirectory = Path.GetFullPath(installDirectory);
            string gameMods = Path.Combine(gameDirectory, "mods");
            string sampleMod = Path.Combine(gameMods, "zelix-hello-world");
            string temporaryPayload = Path.Combine(
                Path.GetTempPath(), "zelix-minecraft-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(temporaryPayload);

            try
            {
                ExtractPayload(temporaryPayload);
                Directory.CreateDirectory(installDirectory);
                Directory.CreateDirectory(gameMods);
                CopyDirectory(
                    Path.Combine(temporaryPayload, "python"),
                    Path.Combine(installDirectory, "python"));
                CopyDirectory(
                    Path.Combine(temporaryPayload, "runtime"),
                    Path.Combine(installDirectory, "runtime"));
                CopyFile(
                    Path.Combine(temporaryPayload, "zelix-minecraft-loader-0.1.0.jar"),
                    Path.Combine(gameMods, "zelix-minecraft-loader-0.1.0.jar"));
                CopyFile(
                    Path.Combine(temporaryPayload, "loader-README.md"),
                    Path.Combine(installDirectory, "loader-README.md"));

                if (Directory.Exists(sampleMod))
                {
                    Console.WriteLine("Keeping existing sample mod directory: " + sampleMod);
                }
                else
                {
                    CopyDirectory(
                        Path.Combine(temporaryPayload, "mods", "hello-world"),
                        sampleMod);
                }

                string argumentsFile = Path.Combine(
                    installDirectory, "launch-arguments-" + version + ".txt");
                string python = Path.Combine(installDirectory, "python", "python.exe");
                string zelixCli = Path.Combine(installDirectory, "runtime", "zelix.py");
                File.WriteAllLines(argumentsFile, new[]
                {
                    "--tweakClass dev.zelix.minecraft.ZelixTweaker",
                    "--zelixVersion " + version,
                    "--zelixMods \"" + gameMods + "\"",
                    "--zelixPython \"" + python + "\"",
                    "--zelixCli \"" + zelixCli + "\""
                });

                Console.WriteLine();
                Console.WriteLine("Zelix loader files installed.");
                Console.WriteLine("Game folder: " + gameDirectory);
                Console.WriteLine("Loader JAR:  " + Path.Combine(
                    gameMods, "zelix-minecraft-loader-0.1.0.jar"));
                Console.WriteLine("Sample mod:  " + sampleMod);
                Console.WriteLine("Arguments:   " + argumentsFile);
                Console.WriteLine();
                Console.WriteLine(
                    "The installer does not change your launcher profile. Add the arguments above to an existing LaunchWrapper-based profile and put the loader JAR on that profile's Java classpath.");
                Console.WriteLine(
                    "Minecraft, the official launcher, accounts, and game assets are not included.");
                Console.WriteLine("Only install Zelix mod scripts you trust.");
            }
            finally
            {
                if (Directory.Exists(temporaryPayload))
                {
                    Directory.Delete(temporaryPayload, true);
                }
            }
            return 0;
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine("Setup failed: " + exception.Message);
            return 1;
        }
    }

    private static Dictionary<string, string> ParseArguments(string[] arguments)
    {
        Dictionary<string, string> options = new Dictionary<string, string>(
            StringComparer.OrdinalIgnoreCase);
        for (int index = 0; index < arguments.Length; index++)
        {
            string argument = arguments[index];
            if (argument == "--help" || argument == "-h")
            {
                Console.WriteLine(
                    "Usage: Zelix-Minecraft-Loader-Setup.exe "
                    + "[--game-dir PATH] [--version 1.8.8|1.12.2] "
                    + "[--install-dir PATH]");
                Environment.Exit(0);
            }
            if (!argument.StartsWith("--", StringComparison.Ordinal))
            {
                throw new ArgumentException("Unexpected argument: " + argument);
            }
            string value;
            int equals = argument.IndexOf('=');
            if (equals >= 0)
            {
                value = argument.Substring(equals + 1).Trim('"');
                argument = argument.Substring(0, equals);
            }
            else
            {
                if (index + 1 >= arguments.Length)
                {
                    throw new ArgumentException("Missing value for " + argument);
                }
                value = arguments[++index].Trim('"');
            }
            options[argument] = value;
        }
        return options;
    }

    private static string GetOption(
        Dictionary<string, string> options, string name)
    {
        string value;
        return options.TryGetValue(name, out value) ? value : null;
    }

    private static void ExtractPayload(string destination)
    {
        Assembly assembly = Assembly.GetExecutingAssembly();
        using (Stream stream = assembly.GetManifestResourceStream(PayloadResource))
        {
            if (stream == null)
            {
                throw new InvalidOperationException("The setup payload is missing.");
            }
            using (ZipArchive archive = new ZipArchive(stream, ZipArchiveMode.Read))
            {
                string root = Path.GetFullPath(destination)
                    .TrimEnd(Path.DirectorySeparatorChar)
                    + Path.DirectorySeparatorChar;
                foreach (ZipArchiveEntry entry in archive.Entries)
                {
                    string target = Path.GetFullPath(Path.Combine(
                        destination,
                        entry.FullName.Replace(
                            '/', Path.DirectorySeparatorChar)));
                    if (!target.StartsWith(
                        root, StringComparison.OrdinalIgnoreCase))
                    {
                        throw new InvalidDataException(
                            "Invalid path in installer payload.");
                    }
                    if (entry.FullName.EndsWith("/", StringComparison.Ordinal))
                    {
                        Directory.CreateDirectory(target);
                        continue;
                    }
                    Directory.CreateDirectory(Path.GetDirectoryName(target));
                    using (Stream input = entry.Open())
                    using (FileStream output = File.Create(target))
                    {
                        input.CopyTo(output);
                    }
                }
            }
        }
    }

    private static void CopyDirectory(string source, string destination)
    {
        if (!Directory.Exists(source))
        {
            throw new DirectoryNotFoundException("Payload directory missing: " + source);
        }
        Directory.CreateDirectory(destination);
        foreach (string file in Directory.GetFiles(source))
        {
            CopyFile(file, Path.Combine(destination, Path.GetFileName(file)));
        }
        foreach (string directory in Directory.GetDirectories(source))
        {
            CopyDirectory(
                directory,
                Path.Combine(destination, Path.GetFileName(directory)));
        }
    }

    private static void CopyFile(string source, string destination)
    {
        if (!File.Exists(source))
        {
            throw new FileNotFoundException("Payload file missing.", source);
        }
        string parent = Path.GetDirectoryName(destination);
        if (!String.IsNullOrEmpty(parent))
        {
            Directory.CreateDirectory(parent);
        }
        File.Copy(source, destination, true);
    }
}
