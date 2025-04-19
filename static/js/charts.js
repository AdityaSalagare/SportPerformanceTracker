/**
 * Charts functionality for the Sports Performance Tracker
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips for chart elements
    const chartTooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (chartTooltips.length > 0) {
        chartTooltips.forEach(tooltip => {
            new bootstrap.Tooltip(tooltip);
        });
    }
});

/**
 * Chart utility functions
 */
const chartUtils = {
    /**
     * Generates a random color
     * @param {number} index - The index to use for color generation
     * @returns {Object} - RGB and RGBA color strings
     */
    getColor: function(index) {
        const hue = (index * 137) % 360;
        return {
            rgb: `hsl(${hue}, 70%, 60%)`,
            rgba: `hsla(${hue}, 70%, 60%, 0.7)`
        };
    },
    
    /**
     * Formats date for chart display
     * @param {string|Date} date - The date to format
     * @returns {string} - Formatted date string
     */
    formatDate: function(date) {
        const d = new Date(date);
        return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    },
    
    /**
     * Calculates percentage change between two values
     * @param {number} oldValue - The old value
     * @param {number} newValue - The new value
     * @returns {number} - Percentage change
     */
    calculatePercentChange: function(oldValue, newValue) {
        if (oldValue === 0) return 0;
        return ((newValue - oldValue) / Math.abs(oldValue)) * 100;
    }
};

/**
 * Performance chart types
 */
const performanceCharts = {
    /**
     * Creates a line chart showing performance over time
     * @param {string} canvasId - The canvas element ID
     * @param {Array} data - The performance data
     * @param {string} metricName - The metric name
     * @param {string} unit - The metric unit
     */
    lineChart: function(canvasId, data, metricName, unit) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        
        // Sort data by date
        data.sort((a, b) => new Date(a.date) - new Date(b.date));
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => d.date),
                datasets: [{
                    label: `${metricName} (${unit})`,
                    data: data.map(d => d.value),
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: function(context) {
                                const index = context.dataIndex;
                                if (index > 0) {
                                    const currentValue = data[index].value;
                                    const prevValue = data[index - 1].value;
                                    const change = chartUtils.calculatePercentChange(prevValue, currentValue);
                                    return `Change: ${change > 0 ? '+' : ''}${change.toFixed(1)}%`;
                                }
                                return '';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        title: {
                            display: true,
                            text: metricName
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                }
            }
        });
    },
    
    /**
     * Creates a bar chart comparing metrics across athletes
     * @param {string} canvasId - The canvas element ID
     * @param {Array} athletes - The athletes data
     * @param {string} metricName - The metric name
     * @param {string} unit - The metric unit
     */
    comparisonBarChart: function(canvasId, athletes, metricName, unit) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        
        const labels = athletes.map(a => a.name);
        const values = athletes.map(a => a.value);
        const colors = athletes.map((a, i) => {
            const color = chartUtils.getColor(i);
            return a.isCurrentUser ? 'rgba(75, 192, 192, 0.7)' : color.rgba;
        });
        const borders = athletes.map((a, i) => {
            const color = chartUtils.getColor(i);
            return a.isCurrentUser ? 'rgba(75, 192, 192, 1)' : color.rgb;
        });
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: `${metricName} (${unit})`,
                    data: values,
                    backgroundColor: colors,
                    borderColor: borders,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            title: function(tooltipItems) {
                                return tooltipItems[0].label;
                            },
                            label: function(context) {
                                const value = context.raw;
                                return `${metricName}: ${value} ${unit}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        title: {
                            display: true,
                            text: `${metricName} (${unit})`
                        }
                    }
                }
            }
        });
    },
    
    /**
     * Creates a radar chart comparing multiple metrics for one or more athletes
     * @param {string} canvasId - The canvas element ID
     * @param {Array} data - The performance data by athlete and metric
     * @param {Array} metrics - The metrics data
     */
    radarChart: function(canvasId, data, metrics) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        
        const labels = metrics.map(m => m.name);
        const datasets = data.map((athlete, index) => {
            const color = chartUtils.getColor(index);
            return {
                label: athlete.name,
                data: metrics.map(metric => {
                    const metricData = athlete.metrics.find(m => m.name === metric.name);
                    return metricData ? metricData.value : 0;
                }),
                backgroundColor: `${color.rgba.replace('0.7', '0.2')}`,
                borderColor: color.rgb,
                borderWidth: athlete.isCurrentUser ? 3 : 2,
                pointRadius: athlete.isCurrentUser ? 5 : 3
            };
        });
        
        new Chart(ctx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                scales: {
                    r: {
                        angleLines: {
                            display: true,
                            color: 'rgba(255, 255, 255, 0.2)'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.2)'
                        },
                        pointLabels: {
                            font: {
                                size: 12
                            }
                        }
                    }
                }
            }
        });
    },
    
    /**
     * Creates a horizontal bar chart for team comparison
     * @param {string} canvasId - The canvas element ID
     * @param {Array} teams - The teams data
     * @param {string} metricName - The metric name
     */
    teamComparisonChart: function(canvasId, teams, metricName) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        
        const labels = teams.map(t => t.name);
        const datasets = [];
        
        // Get all unique athletes across teams
        const allAthletes = new Set();
        teams.forEach(team => {
            team.athletes.forEach(athlete => {
                allAthletes.add(athlete.name);
            });
        });
        
        // Create dataset for each athlete
        Array.from(allAthletes).forEach((athlete, index) => {
            const color = chartUtils.getColor(index);
            
            datasets.push({
                label: athlete,
                data: teams.map(team => {
                    const athleteData = team.athletes.find(a => a.name === athlete);
                    if (!athleteData) return null;
                    
                    const metricData = athleteData.metrics.find(m => m.name === metricName);
                    return metricData ? metricData.value : null;
                }),
                backgroundColor: color.rgba,
                borderColor: color.rgb,
                borderWidth: 1
            });
        });
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right',
                    },
                    title: {
                        display: true,
                        text: `${metricName} Comparison Across Teams`
                    }
                }
            }
        });
    }
};

/**
 * Creates a donut chart showing metric distribution
 * @param {string} canvasId - The canvas element ID
 * @param {Array} data - The metrics data
 */
function createMetricDistributionChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    
    const labels = data.map(d => d.name);
    const values = data.map(d => d.count);
    const colors = data.map((_, i) => {
        const hue = (i * 137) % 360;
        return `hsl(${hue}, 70%, 60%)`;
    });
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderColor: 'rgba(30, 30, 30, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right',
                },
                title: {
                    display: true,
                    text: 'Performance Distribution'
                }
            }
        }
    });
}

/**
 * Creates a bubble chart showing performance clusters
 * @param {string} canvasId - The canvas element ID
 * @param {Array} data - The performance data
 * @param {string} xMetric - The x-axis metric name
 * @param {string} yMetric - The y-axis metric name
 */
function createPerformanceClusterChart(canvasId, data, xMetric, yMetric) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    
    // Group data by athlete
    const athletes = {};
    data.forEach(item => {
        const athlete = item.athlete;
        if (!athletes[athlete]) {
            athletes[athlete] = {
                x: 0,
                y: 0,
                r: 10
            };
        }
        
        if (item.metric === xMetric) {
            athletes[athlete].x = item.value;
        }
        
        if (item.metric === yMetric) {
            athletes[athlete].y = item.value;
        }
    });
    
    const bubbleData = Object.keys(athletes).map(name => {
        return {
            label: name,
            data: [athletes[name]]
        };
    });
    
    new Chart(ctx, {
        type: 'bubble',
        data: {
            datasets: bubbleData.map((d, i) => {
                const color = chartUtils.getColor(i);
                return {
                    label: d.label,
                    data: d.data,
                    backgroundColor: color.rgba,
                    borderColor: color.rgb
                };
            })
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: `${xMetric} vs ${yMetric}`
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: xMetric
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: yMetric
                    }
                }
            }
        }
    });
}
