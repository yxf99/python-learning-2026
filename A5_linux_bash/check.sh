#!/bin/bash

LOG="${1:-sample.log}"

if [ ! -f "$LOG" ]; then
    echo "错误: 找不到文件 $LOG"
    exit 1
fi

echo "=== 日志分析: $LOG ==="
echo "总行数: $(wc -l < "$LOG")"
echo "错误数: $(grep -c ERROR "$LOG")"

echo ""
echo "各级别统计:"
grep -o "ERROR\|WARN\|INFO" "$LOG" | sort | uniq -c

echo ""
echo "最近 3 条错误:"
grep ERROR "$LOG" | tail -n 3

ERRORS=$(grep -c ERROR "$LOG")
if [ "$ERRORS" -gt 3 ]; then
    echo ""
    echo "⚠️  错误数超过阈值 (3)"
    exit 1
fi