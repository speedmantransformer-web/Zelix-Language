param(
    [string]$OutputPath = (Join-Path $PSScriptRoot '..\..\build\Zelix-Minecraft-Loader-Setup.exe'),
    [string]$JdkHome = $env:JAVA_HOME
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path $PSScriptRoot).Path
$repositoryRoot = (Resolve-Path (Join-Path $projectRoot '..\..')).Path
$output = [System.IO.Path]::GetFullPath($OutputPath)
if ([string]::IsNullOrWhiteSpace($JdkHome)) {
    $JdkHome = Get-ChildItem 'C:\Program Files\Java' -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            (Test-Path -LiteralPath (Join-Path $_.FullName 'bin\javac.exe')) -and
            (Test-Path -LiteralPath (Join-Path $_.FullName 'bin\jar.exe'))
        } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1 -ExpandProperty FullName
}
if ([string]::IsNullOrWhiteSpace($JdkHome)) {
    throw 'Install a JDK 11+ or pass its location with -JdkHome.'
}
$jdk = [System.IO.Path]::GetFullPath($JdkHome)
$csharpCompiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$tools = @('javac.exe', 'jar.exe')
foreach ($tool in $tools) {
    if (-not (Test-Path -LiteralPath (Join-Path $jdk "bin\$tool"))) {
        throw "JDK tool not found: $(Join-Path $jdk "bin\$tool"). Set -JdkHome to a full JDK installation."
    }
}
if (-not (Test-Path -LiteralPath $csharpCompiler)) {
    throw ".NET Framework C# compiler was not found at $csharpCompiler."
}

$work = Join-Path $env:TEMP ('zelix-minecraft-package-' + [guid]::NewGuid().ToString('N'))
$staging = Join-Path $work 'staging'
$payload = Join-Path $work 'payload'
$dependencies = Join-Path $work 'dependencies'
$classes = Join-Path $work 'classes'
New-Item -ItemType Directory -Path $staging, $payload, $dependencies, $classes -Force | Out-Null

try {
    $downloads = @(
        @('launchwrapper-1.12.jar', 'https://libraries.minecraft.net/net/minecraft/launchwrapper/1.12/launchwrapper-1.12.jar'),
        @('asm-all-5.0.3.jar', 'https://repo.maven.apache.org/maven2/org/ow2/asm/asm-all/5.0.3/asm-all-5.0.3.jar'),
        @('python-3.13.2-embed-amd64.zip', 'https://www.python.org/ftp/python/3.13.2/python-3.13.2-embed-amd64.zip')
    )
    foreach ($download in $downloads) {
        $destination = Join-Path $dependencies $download[0]
        & curl.exe -fsSL $download[1] -o $destination
        if ($LASTEXITCODE -ne 0) {
            throw "Could not download packaging dependency $($download[0])."
        }
    }

    $pythonDirectory = Join-Path $payload 'python'
    $runtimeDirectory = Join-Path $payload 'runtime'
    $modsDirectory = Join-Path $payload 'mods'
    New-Item -ItemType Directory -Path $pythonDirectory, $runtimeDirectory, $modsDirectory -Force | Out-Null
    Expand-Archive -LiteralPath (Join-Path $dependencies 'python-3.13.2-embed-amd64.zip') `
        -DestinationPath $pythonDirectory

    $pythonPathFile = Join-Path $pythonDirectory 'python313._pth'
    if (-not (Test-Path -LiteralPath $pythonPathFile)) {
        throw "The Python embeddable distribution is missing $pythonPathFile."
    }
    $pythonPaths = [System.IO.File]::ReadAllText($pythonPathFile)
    if ($pythonPaths -notmatch '(?m)^\.\.\s*\\runtime\s*$') {
        [System.IO.File]::AppendAllText(
            $pythonPathFile,
            "`r`n..\runtime`r`n",
            [System.Text.Encoding]::ASCII)
    }

    $runtimeModules = @(
        'zelix.py', 'compiler.py', 'game_backend.py', 'project.py',
        'syntax.py', 'typesys.py', 'debug_server.py'
    )
    foreach ($module in $runtimeModules) {
        Copy-Item -LiteralPath (Join-Path $repositoryRoot $module) `
            -Destination $runtimeDirectory
    }
    & (Join-Path $pythonDirectory 'python.exe') `
        (Join-Path $runtimeDirectory 'zelix.py') --version
    if ($LASTEXITCODE -ne 0) {
        throw 'The bundled Python runtime could not start Zelix.'
    }
    foreach ($sampleMod in @('hello-world', 'content-demo')) {
        $sampleModDirectory = Join-Path $modsDirectory $sampleMod
        New-Item -ItemType Directory -Path $sampleModDirectory -Force | Out-Null
        $sampleSource = if ($sampleMod -eq 'content-demo') {
            Join-Path $projectRoot 'samples\content-demo'
        } else {
            Join-Path $projectRoot 'mods\hello-world'
        }
        Get-ChildItem -LiteralPath $sampleSource -Force |
            Copy-Item -Destination $sampleModDirectory -Recurse
    }

    $launchWrapper = Join-Path $dependencies 'launchwrapper-1.12.jar'
    $asm = Join-Path $dependencies 'asm-all-5.0.3.jar'
    $sourceFiles = Get-ChildItem (Join-Path $projectRoot 'src\main\java') `
        -Filter '*.java' -Recurse | ForEach-Object { $_.FullName }
    if ($sourceFiles.Count -eq 0) {
        throw 'No Java loader source files were found.'
    }
    $classpath = "$launchWrapper;$asm"
    & (Join-Path $jdk 'bin\javac.exe') --release 8 -encoding UTF-8 `
        -cp $classpath -d $classes $sourceFiles
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not compile the Java LaunchWrapper adapter.'
    }

    $manifestPath = Join-Path $work 'MANIFEST.MF'
    [System.IO.File]::WriteAllText(
        $manifestPath,
        "Manifest-Version: 1.0`r`nImplementation-Title: Zelix Minecraft Script Loader`r`nImplementation-Version: 0.1.0`r`nTweakClass: dev.zelix.minecraft.ZelixTweaker`r`n`r`n",
        [System.Text.Encoding]::ASCII)
    $loaderJar = Join-Path $payload 'zelix-minecraft-loader-0.1.0.jar'
    & (Join-Path $jdk 'bin\jar.exe') cfm $loaderJar $manifestPath -C $classes .
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not package the Java LaunchWrapper adapter.'
    }

    Copy-Item -LiteralPath (Join-Path $projectRoot 'README.md') `
        -Destination (Join-Path $payload 'loader-README.md')
    $payloadArchive = Join-Path $work 'payload.zip'
    Compress-Archive -Path (Join-Path $payload '*') -DestinationPath $payloadArchive -CompressionLevel Optimal
    New-Item -ItemType Directory -Path (Split-Path -Parent $output) -Force | Out-Null
    & $csharpCompiler /nologo /target:exe /platform:anycpu `
        "/out:$output" `
        "/reference:System.IO.Compression.dll" `
        "/reference:System.IO.Compression.FileSystem.dll" `
        "/resource:$payloadArchive,ZelixMinecraftLoader.payload.zip" `
        (Join-Path $PSScriptRoot 'setup.cs')
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $output)) {
        throw "Could not compile the setup executable at $output."
    }
    Write-Output "Created $output"
} finally {
    if (Test-Path -LiteralPath $work) {
        Remove-Item -LiteralPath $work -Recurse -Force
    }
}
