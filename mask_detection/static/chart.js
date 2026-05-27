/**
 * chart.js — Mask Detection Dashboard
 * Module quản lý chart, stats, và live polling
 */

// ── Cấu hình ─────────────────────────────────────────────────────
const POLL_INTERVAL_MS = 2000;   // Tần suất refresh stats (ms)
const MAX_HISTORY      = 20;     // Số điểm dữ liệu lịch sử giữ lại
const STATS_API        = "/api/stats";

// ── Trạng thái nội bộ ────────────────────────────────────────────
let pieChart    = null;
let lineChart   = null;
let pollTimer   = null;
let maskHistory = [];   // [{time, mask, nomask}, ...]

// ── Khởi tạo toàn bộ dashboard ───────────────────────────────────
function initDashboard() {
    initPieChart();
    initLineChart();
    startPolling();
}

// ── Pie Chart — tỉ lệ Mask vs No Mask hiện tại ───────────────────
function initPieChart() {
    const canvas = document.getElementById("pieChart");
    if (!canvas) return;

    const initialMask   = parseInt(canvas.dataset.mask   || "0");
    const initialNomask = parseInt(canvas.dataset.nomask || "0");

    pieChart = new Chart(canvas.getContext("2d"), {
        type: "pie",
        data: {
            labels: ["✅ MASK", "❌ NO MASK"],
            datasets: [{
                data: [initialMask, initialNomask],
                backgroundColor: ["#22c55e", "#ef4444"],
                borderColor: ["#16a34a", "#b91c1c"],
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        color: "#94a3b8",
                        font: { size: 13 },
                        padding: 16,
                    }
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
                            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = total > 0
                                ? ((ctx.parsed / total) * 100).toFixed(1)
                                : 0;
                            return ` ${ctx.label}: ${ctx.parsed} (${pct}%)`;
                        }
                    }
                }
            }
        }
    });
}

// ── Line Chart — lịch sử số người qua thời gian ──────────────────
function initLineChart() {
    const canvas = document.getElementById("lineChart");
    if (!canvas) return;

    lineChart = new Chart(canvas.getContext("2d"), {
        type: "line",
        data: {
            labels: [],
            datasets: [
                {
                    label: "MASK",
                    data: [],
                    borderColor: "#22c55e",
                    backgroundColor: "rgba(34,197,94,0.1)",
                    borderWidth: 2,
                    pointRadius: 3,
                    tension: 0.4,
                    fill: true,
                },
                {
                    label: "NO MASK",
                    data: [],
                    borderColor: "#ef4444",
                    backgroundColor: "rgba(239,68,68,0.1)",
                    borderWidth: 2,
                    pointRadius: 3,
                    tension: 0.4,
                    fill: true,
                }
            ]
        },
        options: {
            responsive: true,
            animation: { duration: 300 },
            scales: {
                x: {
                    ticks: { color: "#94a3b8", maxTicksLimit: 8 },
                    grid:  { color: "rgba(148,163,184,0.1)" }
                },
                y: {
                    beginAtZero: true,
                    ticks: { color: "#94a3b8", stepSize: 1 },
                    grid:  { color: "rgba(148,163,184,0.1)" }
                }
            },
            plugins: {
                legend: {
                    labels: { color: "#94a3b8", font: { size: 12 } }
                }
            }
        }
    });
}

// ── Cập nhật chart với dữ liệu mới ───────────────────────────────
function updateCharts(mask, nomask) {
    // Pie chart
    if (pieChart) {
        pieChart.data.datasets[0].data = [mask, nomask];
        pieChart.update("none");   // "none" = không animate, nhanh hơn
    }

    // Line chart — thêm điểm mới vào lịch sử
    if (lineChart) {
        const now = new Date().toLocaleTimeString("vi-VN", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
        });

        const labels = lineChart.data.labels;
        const maskData   = lineChart.data.datasets[0].data;
        const nomaskData = lineChart.data.datasets[1].data;

        labels.push(now);
        maskData.push(mask);
        nomaskData.push(nomask);

        // Giữ tối đa MAX_HISTORY điểm
        if (labels.length > MAX_HISTORY) {
            labels.shift();
            maskData.shift();
            nomaskData.shift();
        }

        lineChart.update("none");
    }
}

// ── Cập nhật các thẻ số liệu trên dashboard ──────────────────────
function updateStatCards(data) {
    const setEl = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    };

    setEl("stat-mask",       data.mask       ?? 0);
    setEl("stat-nomask",     data.nomask     ?? 0);
    setEl("stat-violations", data.total_violations ?? 0);

    // Cập nhật màu badge trạng thái
    const badge = document.getElementById("status-badge");
    if (badge) {
        if (data.nomask > 0) {
            badge.textContent  = "⚠️ VI PHẠM";
            badge.style.background = "#b91c1c";
        } else {
            badge.textContent  = "✅ AN TOÀN";
            badge.style.background = "#16a34a";
        }
    }
}

// ── Cập nhật bảng log vi phạm ────────────────────────────────────
function updateLogTable(logs) {
    const tbody = document.getElementById("log-body");
    if (!tbody || !logs || logs.length === 0) return;

    tbody.innerHTML = logs
        .slice()
        .reverse()   // Mới nhất lên trên
        .map((log, i) => `
            <tr>
                <td>${logs.length - i}</td>
                <td>${escapeHtml(log.time)}</td>
                <td style="color:#f87171;font-weight:bold;">${escapeHtml(log.status)}</td>
                <td>
                    <a href="/static/violations/${escapeHtml(log.image)}"
                       target="_blank" rel="noopener">
                        🖼️ Xem ảnh
                    </a>
                </td>
            </tr>`)
        .join("");
}

// ── Polling API /api/stats ────────────────────────────────────────
async function fetchStats() {
    try {
        const res = await fetch(STATS_API, { credentials: "same-origin" });

        if (res.status === 401) {
            // Phiên đăng nhập hết hạn → chuyển về login
            stopPolling();
            window.location.href = "/login";
            return;
        }

        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();

        updateStatCards(data);
        updateCharts(data.mask ?? 0, data.nomask ?? 0);
        updateLogTable(data.logs);

    } catch (err) {
        console.warn("[MaskDetect] Không thể lấy stats:", err.message);
    }
}

function startPolling() {
    fetchStats();   // Lần đầu chạy ngay lập tức
    pollTimer = setInterval(fetchStats, POLL_INTERVAL_MS);
}

function stopPolling() {
    if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
    }
}

// ── Tiện ích ─────────────────────────────────────────────────────
function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g,  "&amp;")
        .replace(/</g,  "&lt;")
        .replace(/>/g,  "&gt;")
        .replace(/"/g,  "&quot;")
        .replace(/'/g,  "&#039;");
}

// ── Export API công khai ──────────────────────────────────────────
window.MaskDetect = {
    init:         initDashboard,
    startPolling,
    stopPolling,
    fetchStats,
    updateCharts,
};

// Tự động khởi động khi DOM sẵn sàng
document.addEventListener("DOMContentLoaded", initDashboard);