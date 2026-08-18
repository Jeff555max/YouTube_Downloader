$exePath = "c:\projects\YouTube_Downloader\dist\VideoDownloader\VideoDownloader.exe"
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = "$desktop\Video Downloader.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $exePath
$shortcut.WorkingDirectory = "c:\projects\YouTube_Downloader\dist\VideoDownloader"
$shortcut.Description = "Video Downloader - YouTube, RuTube, VK"
$shortcut.Save()

Write-Host "Ярлык создан: $shortcutPath"
