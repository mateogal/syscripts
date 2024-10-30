$hookUrl = ''
$logPath = ''
[System.Collections.ArrayList]$embedArray = @()
[System.Collections.ArrayList]$connectionList = @()

function Send-Webhook {
    param (
        $content
    )

    # Server start
    $rx = "Valheim version:(\d+\.\d+\.\d+)"
    $match = $content -match $rx
    if ($match) {
        $player_name = $Matches[1]
        $color = '5763719'
        $title = 'Servidor Iniciado'
        $description = "Servidor Valheim iniciado!"

        $embedObject = [PSCustomObject]@{
            color       = $color
            title       = $title
            description = $description
        }
    
        $embedArray.Add($embedObject)
        $payload = [PSCustomObject]@{
            embeds = $embedArray
        }

        Invoke-RestMethod -Uri $hookUrl -Method Post -Body ($payload | ConvertTo-Json) -ContentType 'Application/Json' &
        return
    }

    # Monitor for initiation of new connection
    $rx = "Got handshake from client (\d+)"
    $match = $content -match $rx
    if ($match) {
        $connectionList.Add(
            [PSCustomObject]@{
                SteamID    = $Matches[1]
                PlayerName = ""
            }
        )
        return
    }

    # Player Connection and player death
    $rx = "Got character ZDOID from (.+) : (-?\d+:-?\d+)"
    $match = $content -match $rx
    if ($match) {
        if ($Matches[2] -eq "0:0") {
            $player_name = $Matches[1]
            $color = '15105570'
            $title = 'Muerte de Jugador'
            foreach ($player in $connectionList) {
                if ($player.PlayerName -eq $player_name) {
                    $description = "El jugador $player_name ha muerto dentro de Valheim Server!"
                    break
                }
            }
            
        }
        else {
            $player_name = $Matches[1]
            $connectionList[-1].PlayerName = $player_name
            $color = '4289797'
            $title = 'Conexion de Jugador'
            $description = "El jugador $player_name se ha conectado a Valheim Server!"
        }

        $embedObject = [PSCustomObject]@{
            color       = $color
            title       = $title
            description = $description
        }
        
        $embedArray.Add($embedObject)
        $payload = [PSCustomObject]@{
            embeds = $embedArray
        }

        Invoke-RestMethod -Uri $hookUrl -Method Post -Body ($payload | ConvertTo-Json) -ContentType 'Application/Json' &
        return
    }

    # Player disconnection
    $rx = "Closing socket (\d{2,})"
    $match = $content -match $rx
    if ($match) {
        $steam_id = $Matches[1]
        $color = '16776960'
        $title = 'Desconexion de Jugador'
        foreach ($player in $connectionList) {
            if ($steam_id -eq $player.SteamID) {
                $description = "El jugador $player_name se ha desconectado a Valheim Server!"
            }
            $connectionList.Remove($player)
        }        
    
        $embedObject = [PSCustomObject]@{
            color       = $color
            title       = $title
            description = $description
        }
            
        $embedArray.Add($embedObject)
        $payload = [PSCustomObject]@{
            embeds = $embedArray
        }
    
        Invoke-RestMethod -Uri $hookUrl -Method Post -Body ($payload | ConvertTo-Json) -ContentType 'Application/Json' &
        return
    }
}

$current_line = ""

while (1) {
    $new_line = Get-Content $logPath -Tail 1
    if ($new_line -ne $current_line) {
        $current_line = $new_line
        Send-Webhook -Content $new_line
    }
}