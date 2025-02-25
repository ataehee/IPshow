<?php
// 设置数据文件路径
$dataFile = 'ip_records.txt';

// 处理 POST 请求
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // 读取 JSON 数据
    $input = json_decode(file_get_contents('php://input'), true);
    $ip = $input['ip'] ?? '';
    $timestamp = $input['timestamp'] ?? '';

    if ($ip && $timestamp) {
        // 将记录写入文件
        file_put_contents($dataFile, "$ip,$timestamp\n", FILE_APPEND);
    }
}

// 读取记录并过滤过期数据
$records = [];
if (file_exists($dataFile)) {
    $lines = file($dataFile, FILE_IGNORE_NEW_LINES);
    $now = time();
    foreach ($lines as $line) {
        list($ip, $timestamp) = explode(',', $line);
        if ($now - strtotime($timestamp) <= 864000) { // 10天 = 864000秒
            $records[] = ['ip' => $ip, 'timestamp' => $timestamp];
        }
    }
}

// 按时间戳排序并取最新的10条记录
usort($records, function($a, $b) {
    return strtotime($b['timestamp']) - strtotime($a['timestamp']); // 最新的排在前面
});
$records = array_slice($records, 0, 10); // 取最新的10条记录
?>

<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IP 记录</title>
    <link rel="stylesheet" href="style.css">
    <script>
        function fetchLatestIPs() {
            fetch('get_latest_ip.php')
                .then(response => response.json())
                .then(data => {
                    const tbody = document.querySelector('tbody');
                    tbody.innerHTML = ''; // 清空现有内容
                    data.forEach((record, index) => {
                        const row = document.createElement('tr');
                        const indexCell = document.createElement('td');
                        const ipCell = document.createElement('td');
                        const timestampCell = document.createElement('td');
                        indexCell.textContent = index + 1; // 添加序号
                        ipCell.textContent = record.ip;
                        timestampCell.textContent = record.timestamp;
                        row.appendChild(indexCell);
                        row.appendChild(ipCell);
                        row.appendChild(timestampCell);
                        tbody.appendChild(row);
                    });
                })
                .catch(error => console.error('获取最新IP失败:', error));
        }

        // 每5秒请求一次最新的IP记录
        setInterval(fetchLatestIPs, 5000);
    </script>
</head>
<body>
    <div class="container">
        <h1>IP 记录</h1>
        <table>
            <thead>
                <tr>
                    <th>序号</th>
                    <th>IP 地址</th>
                    <th>时间戳</th>
                </tr>
            </thead>
            <tbody>
                <?php foreach ($records as $index => $record): ?>
                    <tr>
                        <td><?php echo $index + 1; ?></td>
                        <td><?php echo htmlspecialchars($record['ip']); ?></td>
                        <td><?php echo htmlspecialchars($record['timestamp']); ?></td>
                    </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    </div>
</body>
</html> 