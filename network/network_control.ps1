# This script is part of (https://github.com/mateogal/Syscripts)
#Pre-requisites in all machines: Enable-PSRemoting

$remote_hostname = "Srv-Host" # Hostname
$remote_host = "192.168.1.14" # Main network interface to check
$remote_host_bkp = "192.168.1.18" # Secondary network interface to check in case of failure
$interfaz_name = "Ethernet" # Adapter name to restart
$remote_host_username = "Srv-Host\Administrador" # Remote machine username
$remote_host_password = ConvertTo-SecureString "PASSWORD" -AsPlainText -Force # Remote machine password
$credentials = New-Object System.Management.Automation.PSCredential($remote_host_username, $remote_host_password)

if ($remote_host -NotLike "*$($remote_host)*") {
    Set-Item WSMan:\localhost\Client\TrustedHosts -Concatenate -Value $remote_host -Force # Add TrustedHosts
}

if ($remote_host -NotLike "*$($remote_host_bkp)*") {
    Set-Item WSMan:\localhost\Client\TrustedHosts -Concatenate -Value $remote_host_bkp -Force # Add TrustedHosts
}

$test_connection_host = Test-NetConnection -ComputerName $remote_host -InformationLevel Detailed # PING to main
$test_connection_host_bkp = Test-NetConnection -ComputerName $remote_host_bkp -InformationLevel Detailed # PING to secondary

Write-Output "Starting test: $($remote_host) / $($remote_host_bkp) / Interfaz: $($interfaz_name) `n" > "C:\scripts\check_network.log"
Write-Output "PING main interface: $($remote_host):" >> "C:\scripts\check_network.log"
Write-Output $($test_connection_host | Format-List) >> "C:\scripts\check_network.log"

if (!$test_connection_host.PingSucceeded) {
    Write-Output "Destination host ping fail: $($remote_host) `n" >> "C:\scripts\check_network.log"
    Write-Output "PING secondary interface: $($remote_host_bkp):" >> "C:\scripts\check_network.log"
    Write-Output $($test_connection_host_bkp | Format-List) >> "C:\scripts\check_network.log"

    if ($test_connection_host_bkp.PingSucceeded) {
        $session = New-PSSession $remote_host_bkp -Credential $credentials

        Write-Output "Connected to remote host through secondary interface: $($remote_host_bkp). Fix starting. `n" >> "C:\scripts\check_network.log"

        $adapter = Invoke-Command -Session $session -ScriptBlock { Get-NetAdapter -Name $Using:interfaz_name }

        $disable_adapter = Invoke-Command -Session $session -ScriptBlock { Disable-NetAdapter -Name $Using:adapter.Name -Confirm:$false }
        Write-Output "Command Disable-NetAdapter: $($disable_adapter). `n" >> "C:\scripts\check_network.log"

        $enable_adapter = Invoke-Command -Session $session -ScriptBlock { Enable-NetAdapter -Name $Using:adapter.Name -Confirm:$false }
        Write-Output "Command Enable-NetAdapter: $($enable_adapter). `n" >> "C:\scripts\check_network.log"

        Remove-PSSession $session

        Start-Sleep -Seconds 5

        $test_connection_host = Test-NetConnection -ComputerName $remote_host -InformationLevel Detailed
        Write-Output "PING after fix attempt:" >> "C:\scripts\check_network.log"
        Write-Output $($test_connection_host | Format-List) >> "C:\scripts\check_network.log"

        if ($test_connection_host.PingSucceeded) {
            $result = "FIXED"
            Write-Output "Problem fixed." >> "C:\scripts\check_network.log"
        }
        else {
            $result = "WARNING: CONNECTED BUT NOT FIXED"
            Write-Output "Problem wasn't fixed." >> "C:\scripts\check_network.log"
        }        
    }
    else {
        Write-Output "Remote host didn't respond on secondary interface $($remote_host_bkp) `n" >> "C:\scripts\check_network.log"
        Write-Output "None of the interfaces from remote host responded" >> "C:\scripts\check_network.log"

        $result = "EMERGENCY ALL REMOTE INTERFACES ARE DOWN"
    }

    # Send email
    $fecha = Get-Date
    $from = "EMAIL"
    $to = "EMAIL"
    $subject = "$($result) / Network check - XXXXXX / $($remote_hostname)"
    $smtpserver = "SMTP"
    $user = "EMAIL"
    $passwd = ConvertTo-SecureString "PASSWORD" -AsPlainText -Force
    $credentials = New-Object System.Management.Automation.PSCredential ($user, $passwd)
    $port = 587
    Send-MailMessage -smtpServer $smtpserver -from $from -to $to -subject $subject -body "$fecha" -credential $credentials -Attachments "C:\scripts\check_network.log" -UseSsl -Port $port

}
else {
    Write-Output "Remote host is running without problems." >> "C:\scripts\check_network.log"
}