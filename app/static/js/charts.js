/**
 * KZ-InsurePro Charts Module
 * Interactive dashboards with 8 types of Chart.js visualizations
 * For Insurance Company (Insurer) role
 */

// Chart instances storage
const chartInstances = {};

// Color schemes
const colors = {
    primary: '#1e3a5f',
    secondary: '#3d5a80',
    success: '#06d6a0',
    warning: '#ffd60a',
    danger: '#ef476f',
    info: '#118ab2',
    light: '#f8f9fa',
    dark: '#212529',

    // Extended palette
    blue: '#0d6efd',
    indigo: '#6610f2',
    purple: '#6f42c1',
    pink: '#d63384',
    red: '#dc3545',
    orange: '#fd7e14',
    yellow: '#ffc107',
    green: '#198754',
    teal: '#20c997',
    cyan: '#0dcaf0',

    // Insurance specific
    life: '#4a90e2',
    nonLife: '#f39c12',
    health: '#27ae60',
    annuity: '#9b59b6'
};

// Chart default config
Chart.defaults.font.family = "'Inter', 'Segoe UI', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = '#495057';

/**
 * 1. LINE CHART: Solvency Ratio (12 months trend)
 */
function createSolvencyRatioChart(canvasId, data = null) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.error(`Canvas ${canvasId} not found`);
        return null;
    }

    // Default data if not provided
    if (!data) {
        data = {
            labels: ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'],
            solvencyRatio: [142, 145, 148, 151, 149, 152, 155, 157, 159, 157, 155, 157],
            minRequirement: Array(12).fill(100), // 100% minimum
            targetLevel: Array(12).fill(120)      // 120% target
        };
    }

    // Destroy existing chart
    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    chartInstances[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Коэффициент платежеспособности (%)',
                    data: data.solvencyRatio,
                    borderColor: colors.success,
                    backgroundColor: 'rgba(6, 214, 160, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 7
                },
                {
                    label: 'Минимальное требование (100%)',
                    data: data.minRequirement,
                    borderColor: colors.danger,
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                },
                {
                    label: 'Целевой уровень (120%)',
                    data: data.targetLevel,
                    borderColor: colors.warning,
                    borderWidth: 2,
                    borderDash: [10, 5],
                    fill: false,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Solvency II Ratio - Динамика за 12 месяцев',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    display: true,
                    position: 'bottom'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    min: 80,
                    max: 180,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    title: {
                        display: true,
                        text: 'Коэффициент (%)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Месяц'
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });

    return chartInstances[canvasId];
}

/**
 * 2. PIE CHART: Portfolio Composition (by Currency)
 */
function createPortfolioCompositionChart(canvasId, data = null) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    if (!data) {
        data = {
            labels: ['KZT', 'USD', 'EUR', 'RUB'],
            values: [650000000, 120000000, 45000000, 35000000] // in KZT equivalent
        };
    }

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    chartInstances[canvasId] = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: [
                    colors.primary,
                    colors.success,
                    colors.info,
                    colors.warning
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Состав портфеля по валютам',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    display: true,
                    position: 'right'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return context.label + ': ' + formatCurrency(value) + ' (' + percentage + '%)';
                        }
                    }
                }
            }
        }
    });

    return chartInstances[canvasId];
}

/**
 * 3. BAR CHART: ECL by Stage with Forecast
 */
function createECLByStageChart(canvasId, data = null) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    if (!data) {
        data = {
            labels: ['Q1 2025', 'Q2 2025', 'Q3 2025', 'Q4 2025', 'Q1 2026 (П)'],
            stage1: [12500000, 13200000, 13800000, 14100000, 14500000],
            stage2: [8900000, 9100000, 9500000, 9800000, 10200000],
            stage3: [4200000, 4500000, 4800000, 5100000, 5400000]
        };
    }

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    chartInstances[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Stage 1 (12-месячный ECL)',
                    data: data.stage1,
                    backgroundColor: colors.success,
                    borderColor: colors.success,
                    borderWidth: 1
                },
                {
                    label: 'Stage 2 (Lifetime ECL)',
                    data: data.stage2,
                    backgroundColor: colors.warning,
                    borderColor: colors.warning,
                    borderWidth: 1
                },
                {
                    label: 'Stage 3 (Обесценение)',
                    data: data.stage3,
                    backgroundColor: colors.danger,
                    borderColor: colors.danger,
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'ECL по стадиям (МСФО 9) с прогнозом',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    display: true,
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + formatCurrency(context.parsed.y);
                        },
                        footer: function(tooltipItems) {
                            const total = tooltipItems.reduce((sum, item) => sum + item.parsed.y, 0);
                            return 'Всего: ' + formatCurrency(total);
                        }
                    }
                }
            },
            scales: {
                x: {
                    stacked: true,
                    title: {
                        display: true,
                        text: 'Период'
                    }
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value, true);
                        }
                    },
                    title: {
                        display: true,
                        text: 'ECL (млн ₸)'
                    }
                }
            }
        }
    });

    return chartInstances[canvasId];
}

/**
 * 4. WATERFALL CHART: CSM Changes (IFRS 17)
 * Using bar chart with custom colors to simulate waterfall
 */
function createCSMWaterfallChart(canvasId, data = null) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    if (!data) {
        data = {
            labels: ['Нач. баланс', 'Новые договоры', 'Ожид. изменения', 'Опыт. корректировки', 'Амортизация', 'Кон. баланс'],
            values: [450000000, 85000000, -15000000, 12000000, -62000000, 470000000],
            colors: [colors.primary, colors.success, colors.danger, colors.success, colors.danger, colors.primary]
        };
    }

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    chartInstances[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'CSM изменения',
                data: data.values,
                backgroundColor: data.colors,
                borderColor: data.colors.map(c => c),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'CSM Roll-Forward (Contractual Service Margin)',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return formatCurrency(context.parsed.y);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value, true);
                        }
                    },
                    title: {
                        display: true,
                        text: 'CSM (млн ₸)'
                    }
                }
            }
        }
    });

    return chartInstances[canvasId];
}

/**
 * 5. AREA CHART: Premiums vs Claims Trend
 */
function createPremiumsVsClaimsChart(canvasId, data = null) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    if (!data) {
        data = {
            labels: ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'],
            premiums: [125000000, 132000000, 128000000, 135000000, 142000000, 138000000, 145000000, 151000000, 148000000, 155000000, 152000000, 160000000],
            claims: [78000000, 82000000, 79000000, 85000000, 88000000, 86000000, 91000000, 95000000, 93000000, 97000000, 94000000, 99000000]
        };
    }

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    chartInstances[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Премии',
                    data: data.premiums,
                    borderColor: colors.success,
                    backgroundColor: 'rgba(6, 214, 160, 0.3)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Убытки',
                    data: data.claims,
                    borderColor: colors.danger,
                    backgroundColor: 'rgba(239, 71, 111, 0.3)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Динамика премий и убытков',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    display: true,
                    position: 'bottom'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + formatCurrency(context.parsed.y);
                        },
                        footer: function(tooltipItems) {
                            if (tooltipItems.length >= 2) {
                                const premium = tooltipItems[0].parsed.y;
                                const claim = tooltipItems[1].parsed.y;
                                const lossRatio = ((claim / premium) * 100).toFixed(1);
                                return 'Loss Ratio: ' + lossRatio + '%';
                            }
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value, true);
                        }
                    },
                    title: {
                        display: true,
                        text: 'Сумма (млн ₸)'
                    }
                }
            },
            interaction: {
                mode: 'index',
                intersect: false
            }
        }
    });

    return chartInstances[canvasId];
}

/**
 * 6. DOUGHNUT CHART: Products Mix
 */
function createProductsMixChart(canvasId, data = null) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    if (!data) {
        data = {
            labels: ['Жизнь', 'Не-жизнь', 'Здоровье', 'Аннуитеты'],
            values: [420000000, 285000000, 95000000, 50000000]
        };
    }

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    chartInstances[canvasId] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: [
                    colors.life,
                    colors.nonLife,
                    colors.health,
                    colors.annuity
                ],
                borderWidth: 3,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Структура продуктов по типу страхования',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    display: true,
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return context.label + ': ' + formatCurrency(value) + ' (' + percentage + '%)';
                        }
                    }
                }
            },
            cutout: '60%'
        }
    });

    return chartInstances[canvasId];
}

/**
 * 7. GAUGE CHART: Key Metrics (Solvency, Loss Ratio)
 * Using doughnut chart with custom display
 */
function createGaugeChart(canvasId, metric, value, min = 0, max = 200, threshold = 100) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    // Calculate percentage
    const percentage = ((value - min) / (max - min)) * 100;
    const remaining = 100 - percentage;

    // Determine color based on threshold
    let gaugeColor;
    if (value >= threshold * 1.2) {
        gaugeColor = colors.success;
    } else if (value >= threshold) {
        gaugeColor = colors.warning;
    } else {
        gaugeColor = colors.danger;
    }

    chartInstances[canvasId] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [percentage, remaining],
                backgroundColor: [gaugeColor, '#e9ecef'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            rotation: -90,
            circumference: 180,
            cutout: '75%',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                },
                title: {
                    display: true,
                    text: metric,
                    font: { size: 14, weight: 'bold' },
                    padding: { bottom: 10 }
                }
            }
        },
        plugins: [{
            id: 'gaugeText',
            afterDatasetDraw: function(chart) {
                const ctx = chart.ctx;
                const centerX = chart.chartArea.left + (chart.chartArea.right - chart.chartArea.left) / 2;
                const centerY = chart.chartArea.top + (chart.chartArea.bottom - chart.chartArea.top) / 2 + 20;

                ctx.save();
                ctx.font = 'bold 24px Inter';
                ctx.fillStyle = gaugeColor;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(value.toFixed(1) + '%', centerX, centerY);

                ctx.font = '12px Inter';
                ctx.fillStyle = '#6c757d';
                ctx.fillText('Min: ' + min + '% | Max: ' + max + '%', centerX, centerY + 25);
                ctx.restore();
            }
        }]
    });

    return chartInstances[canvasId];
}

/**
 * 8. RADAR CHART: Risk Matrix / Concentration
 */
function createRiskMatrixChart(canvasId, data = null) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    if (!data) {
        data = {
            labels: ['Market Risk', 'Credit Risk', 'Operational Risk', 'Underwriting Risk', 'Liquidity Risk', 'Concentration Risk'],
            current: [65, 45, 55, 70, 35, 60],
            target: [50, 40, 45, 60, 30, 50]
        };
    }

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    chartInstances[canvasId] = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Текущий уровень',
                    data: data.current,
                    borderColor: colors.danger,
                    backgroundColor: 'rgba(239, 71, 111, 0.2)',
                    borderWidth: 2,
                    pointRadius: 4,
                    pointBackgroundColor: colors.danger
                },
                {
                    label: 'Целевой уровень',
                    data: data.target,
                    borderColor: colors.success,
                    backgroundColor: 'rgba(6, 214, 160, 0.2)',
                    borderWidth: 2,
                    pointRadius: 4,
                    pointBackgroundColor: colors.success
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Матрица рисков - профиль концентрации',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    display: true,
                    position: 'bottom'
                }
            },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20
                    }
                }
            }
        }
    });

    return chartInstances[canvasId];
}

/**
 * UTILITY FUNCTIONS
 */

function formatCurrency(value, short = false) {
    if (short) {
        // Convert to millions
        value = value / 1000000;
        return value.toFixed(1) + 'M';
    }
    return new Intl.NumberFormat('ru-KZ', {
        style: 'currency',
        currency: 'KZT',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

/**
 * Update chart with new data
 */
function updateChart(chartId, newData) {
    const chart = chartInstances[chartId];
    if (!chart) {
        console.error(`Chart ${chartId} not found`);
        return;
    }

    chart.data = newData;
    chart.update('active');
}

/**
 * Destroy chart
 */
function destroyChart(chartId) {
    if (chartInstances[chartId]) {
        chartInstances[chartId].destroy();
        delete chartInstances[chartId];
    }
}

/**
 * Initialize all dashboard charts
 */
function initializeDashboardCharts() {
    // Check if we're on the dashboard page (check for any chart canvas)
    const hasCharts = document.getElementById('solvencyRatioChart') ||
                      document.getElementById('portfolioCompositionChart') ||
                      document.getElementById('eclByStageChart') ||
                      document.getElementById('csmWaterfallChart');

    if (!hasCharts) return;

    console.log('Initializing dashboard charts...');

    // Initialize charts based on what canvases exist
    if (document.getElementById('solvencyRatioChart')) {
        createSolvencyRatioChart('solvencyRatioChart');
    }
    if (document.getElementById('portfolioCompositionChart')) {
        createPortfolioCompositionChart('portfolioCompositionChart');
    }
    if (document.getElementById('eclByStageChart')) {
        createECLByStageChart('eclByStageChart');
    }
    if (document.getElementById('csmWaterfallChart')) {
        createCSMWaterfallChart('csmWaterfallChart');
    }
    if (document.getElementById('premiumsVsClaimsChart')) {
        createPremiumsVsClaimsChart('premiumsVsClaimsChart');
    }
    if (document.getElementById('productsMixChart')) {
        createProductsMixChart('productsMixChart');
    }
    if (document.getElementById('solvencyGauge')) {
        createGaugeChart('solvencyGauge', 'Solvency Ratio', 157, 0, 200, 100);
    }
    if (document.getElementById('riskMatrixChart')) {
        createRiskMatrixChart('riskMatrixChart');
    }

    console.log('Dashboard charts initialized successfully!');
}

/**
 * Fetch real data from API and update charts
 */
async function fetchAndUpdateCharts() {
    try {
        // Fetch dashboard data from API
        const response = await fetch('/api/dashboard/metrics');
        const data = await response.json();

        if (data.status === 'success') {
            // Update charts with real data
            if (data.solvency_ratio) {
                updateChart('solvencyRatioChart', data.solvency_ratio);
            }
            if (data.portfolio_composition) {
                updateChart('portfolioCompositionChart', data.portfolio_composition);
            }
            // ... update other charts
        }
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
    }
}

// Export functions for global access
window.ChartManager = {
    createSolvencyRatioChart,
    createPortfolioCompositionChart,
    createECLByStageChart,
    createCSMWaterfallChart,
    createPremiumsVsClaimsChart,
    createProductsMixChart,
    createGaugeChart,
    createRiskMatrixChart,
    updateChart,
    destroyChart,
    initializeDashboardCharts,
    fetchAndUpdateCharts
};

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDashboardCharts);
} else {
    initializeDashboardCharts();
}
