<?php
// 设置数据文件路径
$dataFile = 'ip_records.txt';

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
    return strtotime($a['timestamp']) - strtotime($b['timestamp']);
});
$records = array_slice($records, -10); // 取最新的10条记录

// 返回 JSON 格式的记录
header('Content-Type: application/json');
echo json_encode($records);
?> 