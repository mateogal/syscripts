#Requisito previo, ejecutar en PS en todos los equipos a conectar: Enable-PSRemoting

$host_remoto_name = "Srv-Host" #Nombre del equipo DNS
$host_remoto = "192.168.1.14" #Interfaz Principal a chequear
$host_remoto_bkp = "192.168.1.18" #Interfaz secundaria a usar para conexion en caso de fallo
$interfaz_name = "Ethernet" #Nombre del adaptador a reinciar
$host_remoto_username = "Srv-Host\Administrador" #Credenciales del equipo a conectarse
$host_remoto_password = ConvertTo-SecureString "PASSWORD" -AsPlainText -Force #Credenciales del equipo a conectarse
$credenciales = New-Object System.Management.Automation.PSCredential($host_remoto_username, $host_remoto_password)

if ($host_remoto -NotLike "*$($host_remoto)*") {
    Set-Item WSMan:\localhost\Client\TrustedHosts -Concatenate -Value $host_remoto -Force #Agregamos a TrustedHosts el equipo a conectarse principal
}

if ($host_remoto -NotLike "*$($host_remoto_bkp)*") {
    Set-Item WSMan:\localhost\Client\TrustedHosts -Concatenate -Value $host_remoto_bkp -Force #Agregamos a TrustedHosts el equipo a conectarse secundaria
}

$test_connection_host = Test-NetConnection -ComputerName $host_remoto -InformationLevel Detailed #PING principal
$test_connection_host_bkp = Test-NetConnection -ComputerName $host_remoto_bkp -InformationLevel Detailed #PING secundaria

Write-Output "Comenzado chequeo de $($host_remoto) / $($host_remoto_bkp) / Interfaz: $($interfaz_name) `n" > "C:\scripts\check_red.log"
Write-Output "PING interfaz principal $($host_remoto):" >> "C:\scripts\check_red.log"
Write-Output $($test_connection_host | Format-List) >> "C:\scripts\check_red.log"

if (!$test_connection_host.PingSucceeded) {
    Write-Output "El Host destino NO respondio en interfaz principal $($host_remoto) `n" >> "C:\scripts\check_red.log"
    Write-Output "PING interfaz secundaria $($host_remoto_bkp):" >> "C:\scripts\check_red.log"
    Write-Output $($test_connection_host_bkp | Format-List) >> "C:\scripts\check_red.log"

    if ($test_connection_host_bkp.PingSucceeded) {
        $session = New-PSSession $host_remoto_bkp -Credential $credenciales

        Write-Output "Conectado al host remoto por interfaz secundaria $($host_remoto_bkp). Comenzando con los comandos. `n" >> "C:\scripts\check_red.log"

        $adapter = Invoke-Command -Session $session -ScriptBlock { Get-NetAdapter -Name $Using:interfaz_name }

        $disable_adapter = Invoke-Command -Session $session -ScriptBlock { Disable-NetAdapter -Name $Using:adapter.Name -Confirm:$false }
        Write-Output "Comando Disable-NetAdapter: $($disable_adapter). `n" >> "C:\scripts\check_red.log"

        $enable_adapter = Invoke-Command -Session $session -ScriptBlock { Enable-NetAdapter -Name $Using:adapter.Name -Confirm:$false }
        Write-Output "Comando Enable-NetAdapter: $($enable_adapter). `n" >> "C:\scripts\check_red.log"

        Remove-PSSession $session

        Start-Sleep -Seconds 5

        $test_connection_host = Test-NetConnection -ComputerName $host_remoto -InformationLevel Detailed
        Write-Output "PING luego de intento solucionar:" >> "C:\scripts\check_red.log"
        Write-Output $($test_connection_host | Format-List) >> "C:\scripts\check_red.log"

        if ($test_connection_host.PingSucceeded) {
            $resultado = "SOLUCIONADO"
            Write-Output "Fue solucionado el problema." >> "C:\scripts\check_red.log"
        }
        else {
            $resultado = "ADVERTENCIA CONECTADO PERO NO SOLUCIONADO"
            Write-Output "NO se pudo solucionar el problema." >> "C:\scripts\check_red.log"
        }        
    }
    else {
        Write-Output "El Host destino NO respondio en interfaz secundaria $($host_remoto_bkp) `n" >> "C:\scripts\check_red.log"
        Write-Output "NINGUNA interfaz del host remoto respondio." >> "C:\scripts\check_red.log"

        $resultado = "EMERGENCIA TODAS INTERFACES CAIDAS"
    }

    #ENVIANDO MAIL CON ADJUNTO
    $fecha = Get-Date
    $from = "EMAIL"
    $to = "EMAIL"
    $subject = "$($resultado) / Chequeo de Red - XXXXXX / $($host_remoto_name)"
    $smtpserver = "SMTP"
    $user = "EMAIL"
    $passwd = ConvertTo-SecureString "PASSWORD" -AsPlainText -Force
    $credenciales = New-Object System.Management.Automation.PSCredential ($user, $passwd)
    $port = 587
    Send-MailMessage -smtpServer $smtpserver -from $from -to $to -subject $subject -body "$fecha" -credential $credenciales -Attachments "C:\scripts\check_red.log" -UseSsl -Port $port

}
else {
    Write-Output "El Host esta activo sin problemas." >> "C:\scripts\check_red.log"
}