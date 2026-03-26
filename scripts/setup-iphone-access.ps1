# AI社員ダッシュボード - iPhone アクセス設定
# PowerShell (管理者権限) で実行してください
# 実行方法: PowerShell を右クリック → 「管理者として実行」
#           Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
#           .\setup-iphone-access.ps1

$WSL_PORT = 3333
$WIN_PORT = 3333

# WSL2 の IP を自動取得
$WSL_IP = (wsl hostname -I).Trim().Split(" ")[0]
Write-Host "WSL2 IP: $WSL_IP"

# 既存のポートフォワーディングを削除（重複防止）
netsh interface portproxy delete v4tov4 listenport=$WIN_PORT listenaddress=0.0.0.0 2>$null

# ポートフォワーディング追加
netsh interface portproxy add v4tov4 `
    listenport=$WIN_PORT `
    listenaddress=0.0.0.0 `
    connectport=$WSL_PORT `
    connectaddress=$WSL_IP

# Firewall ルール（既存があれば上書き）
netsh advfirewall firewall delete rule name="AI社員ダッシュボード" 2>$null
netsh advfirewall firewall add rule `
    name="AI社員ダッシュボード" `
    protocol=TCP `
    dir=in `
    localport=$WIN_PORT `
    action=allow

# 確認
Write-Host ""
Write-Host "=== 設定完了 ===" -ForegroundColor Green
Write-Host ""

# Windows の LAN IP を取得
$WIN_IP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
    $_.InterfaceAlias -notlike "*Loopback*" -and
    $_.InterfaceAlias -notlike "*WSL*" -and
    $_.IPAddress -notlike "169.*"
} | Select-Object -First 1).IPAddress

Write-Host "iPhone から以下の URL にアクセスしてください:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  http://${WIN_IP}:${WIN_PORT}/mobile" -ForegroundColor Yellow
Write-Host ""
Write-Host "（iPhone と PC が同じ Wi-Fi に接続されている必要があります）"
Write-Host ""
Write-Host "ホーム画面に追加するには:"
Write-Host "  Safari で開く → 共有ボタン → 「ホーム画面に追加」"
