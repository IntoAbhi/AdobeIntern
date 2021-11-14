<#
Written on 25 June 2021, 00:44 IST
author : Abhigyan Shrivastava (abhigshr),product development intern 2021
Title : Cloud connector log-level switcher
Build : idk
#>

$host_list = "or1010051151039.corp.adobe.com", "no1010042224070.corp.adobe.com"

# Parameter 1 to switch to Verbose, any other integer to switch to Information
$param = $args[0]

# Verify argument existance
if($args.count -eq 0) {
    Write-Host "ERROR : NO ARGUMENT PASSED!"
    Write-Host "Please pass one of the following arguments:"
    Write-Host "1 : Turn ON Verbose"
    Write-Host "0 : Turn OFF Verbose and collect logs"
    Write-Host "restart : ONLY restart airwatch service in all servers"
    exit
}

# Create essential directories if not exist already
if(!(Test-Path C:\log_level_switcher\log_backup)) {
    mkdir C:\log_level_switcher\log_backup
}
if(!(Test-Path C:\log_level_switcher\downloads)) {
    mkdir C:\log_level_switcher\downloads
}

# Service restart only
$cred = Get-Credential abhigshr
if($param -eq "restart") {
    Write-Host "Restarting service locally"
    Restart-Service AirWatchCloudConnector
     For ($i=0; $i -lt $host_list.Count; $i++) {
        $session = New-PSSession -Credential $cred -ComputerName $host_list[$i]
        Write-Host "Restarting service for " + $host_list[$i]
        Invoke-Command -Session $session -ScriptBlock {
            Restart-Service AirWatchCloudConnector
        }
        Remove-PSSession $session
    }
    exit
}

$path_dir = ""
$datetime = Get-Date -f MM-dd-yy_hh-mm-ss

# Search both banks for config file
if(Test-Path C:\VMware\AirWatch\CloudConnector\Bank1\CloudConnector.exe.config -PathType Leaf) {
    $path_dir = "C:\VMware\AirWatch\CloudConnector\Bank1\CloudConnector.exe.config"
}
else {
    $path_dir = "C:\VMware\AirWatch\CloudConnector\Bank2\CloudConnector.exe.config"
}
Write-Host $path_dir

# Make backup before editing
Copy-Item $path_dir -Destination "C:\log_level_switcher\log_backup"
Rename-Item "C:\log_level_switcher\log_backup\CloudConnector.exe.config" -NewName ($datetime + "_CloudConnector.exe.config")

# Edit as per parameter supplied
if($param -eq 1) {

    if((Get-Content $path_dir) -imatch "Verbose") {
        Write-Host "Already VERBOSE, no changes performed"
    }
    else {
        Write-Host "Switching to VERBOSE"
        (Get-Content $path_dir).Replace('Information', 'Verbose') | Out-File $path_dir -Encoding ascii
    }
}
elseif ($param -eq 0) {

    if((Get-Content $path_dir) -imatch "Information") {
        Write-Host "Already INFORMATION, no changes performed"
    }
    else {
        Write-Host "Switching to INFORMATION"
        (Get-Content $path_dir).Replace('Verbose', 'Information') | Out-File $path_dir -Encoding ascii
    }
}
else {
    Write-Host "Unidentified argument passed, no changes performed in config file"
}

Write-Host "Restarting service now..."
Restart-Service AirWatchCloudConnector
Write-Host "Querying current log level: "

# Checking current log-level
if((Get-Content $path_dir) -imatch "Information") {
    Write-Host "INFORMATION"
}
elseif((Get-Content $path_dir) -imatch "Verbose") {
    Write-Host "VERBOSE"
}
else {
     Write-Host "Log file could be corrupted, please resolve manually"
}

Write-Host "Attempting remote execution now..."


# Download logs if switching verbose off
if($param -eq 0) {
    Copy-Item C:\VMware\AirWatch\Logs\CloudConnector\CloudConnector.log -Destination C:\log_level_switcher\downloads
    Rename-Item -Path C:\log_level_switcher\downloads\CloudConnector.log -NewName ($datetime + "_" + $env:COMPUTERNAME)
    For ($i=0; $i -lt $host_list.Count; $i++) {
        $session = New-PSSession -Credential $cred -ComputerName $host_list[$i]
        Write-Host "Downloading log file..."
        Copy-Item -FromSession $session C:\VMware\AirWatch\Logs\CloudConnector\CloudConnector.log -Destination C:\log_level_switcher\downloads
        Start-Sleep -Seconds 5
        $new_name = $host_list[$i] + ".log" 
        Rename-Item -Path C:\log_level_switcher\downloads\CloudConnector.log -NewName ($datetime + "_" + $new_name)
        Remove-PSSession $session
    }
}


# Execute scripts in all other servers
For ($i=0; $i -lt $host_list.Count; $i++) {
    $session = New-PSSession -Credential $cred -ComputerName $host_list[$i]
    Invoke-Command -Session $session -ScriptBlock {
        hostname
        if(!(Test-Path C:\log_level_switcher\log_backup)) {
            mkdir C:\log_level_switcher\log_backup
        }

        $path_dir = ""
        $datetime = Get-Date -f MM-dd-yy_hh-mm-ss
        if(Test-Path C:\VMware\AirWatch\CloudConnector\Bank1\CloudConnector.exe.config -PathType Leaf) {
            $path_dir = "C:\VMware\AirWatch\CloudConnector\Bank1\CloudConnector.exe.config"
        }
        else {
            $path_dir = "C:\VMware\AirWatch\CloudConnector\Bank2\CloudConnector.exe.config"
        }
        Write-Host $path_dir
        Copy-Item $path_dir -Destination "C:\log_level_switcher\log_backup"
        Rename-Item "C:\log_level_switcher\log_backup\CloudConnector.exe.config" -NewName ($datetime + "_CloudConnector.exe.config")
        if($Using:param -eq 1) {
            Write-Host "Switching to VERBOSE"
            (Get-Content $path_dir).Replace('Information', 'Verbose') | Out-File $path_dir -Encoding ascii
        }
        elseif($Using:param -eq 0) {
        Write-Host "Switching to INFORMATION"
            (Get-Content $path_dir).Replace('Verbose', 'Information') | Out-File $path_dir -Encoding ascii
        }
        else {
            Write-Host "No changes performed in config file"
        }
        Write-Host "Restarting service now..."
        Restart-Service AirWatchCloudConnector
        Write-Host "Querying current log level: "
        if((Get-Content $path_dir) -imatch "Information") {
            Write-Host "INFORMATION"
        }
        elseif((Get-Content $path_dir) -imatch "Verbose") {
            Write-Host "VERBOSE"
        }
        else {
             Write-Host "Log file could be corrupted, please resolve manually"
        }
    }
    Remove-PSSession $session
}

