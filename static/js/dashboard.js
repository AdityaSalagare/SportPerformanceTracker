/**
 * Dashboard functionality for the Sports Performance Tracker
 */

document.addEventListener('DOMContentLoaded', function() {
    const teamSelect   = document.getElementById('chartTeamSelect');
    const metricSelect = document.getElementById('chartMetricSelect');
    let performanceChart = null;
  
    // Fetch + draw chart for chosen team & metric
    function createChart(teamId, metric) {
      if (!teamId || !metric) return;
  
      fetch(`/coach/api/performance_data/${teamId}/${metric}`)
        .then(r => r.json())
        .then(data => {
          if (!data.length) {
            document.getElementById('performanceChart').style.display = 'none';
            return;
          }
          document.getElementById('performanceChart').style.display = 'block';
  
          // build dates & datasets
          const athletes = [...new Set(data.map(d => d.athlete))];
          const dates    = [...new Set(data.map(d => d.date))].sort();
  
          const datasets = athletes.map(name => {
            const color = () => Math.floor(Math.random()*200)+30;
            const d = data.filter(d=>d.athlete===name);
            return {
              label: name,
              data: dates.map(date => {
                const match = d.find(x=>x.date===date);
                return match ? match.value : null;
              }),
              borderColor: `rgb(${color()},${color()},${color()})`,
              backgroundColor: `rgba(0,0,0,0)`,
              tension: 0.4
            };
          });
  
          const ctx = document.getElementById('performanceChart').getContext('2d');
          if (performanceChart) performanceChart.destroy();
          performanceChart = new Chart(ctx, {
            type: 'line',
            data: { labels: dates, datasets },
            options: {
              responsive: true,
              scales: {
                y: { beginAtZero: true },
                x: { title: { display: true, text: 'Date' } }
              }
            }
          });
        })
        .catch(console.error);
    }
  
    // when either select changes, redraw
    function onSelectionChange() {
      createChart(teamSelect.value, metricSelect.value);
    }
  
    // when team changes, reload its metrics list
    teamSelect.addEventListener('change', function() {
      fetch(`/coach/api/team/${this.value}/metrics`)
        .then(r => r.json())
        .then(metrics => {
          metricSelect.innerHTML = metrics
            .map(m => `<option value="${m.name}">${m.name.replace('_',' ')}</option>`)
            .join('');
          onSelectionChange();
        });
    });
  
    metricSelect.addEventListener('change', onSelectionChange);
  
    // initial draw
    onSelectionChange();
  });

/**
 * Updates the chart date range based on selection
 * @param {string} range - The selected date range
 */
function updateChartDateRange(range) {
    // This would typically filter the data and update the chart
    // For demonstration purposes, we'll just log the selection
    console.log('Selected date range:', range);
    
    // In a real implementation, we would fetch new data from the server
    // or filter existing data based on the selected date range
    // then update the chart with the new data
}

/**
 * Fetches the current notification count
 */
function fetchNotificationCount() {
    const countElement = document.querySelector('.notification-count');
    if (!countElement) return;
    
    const role = document.body.dataset.role;
    let endpoint = '';
    
    if (role === 'coach') {
        endpoint = '/coach/api/notification_count';
    } else if (role === 'athlete') {
        endpoint = '/athlete/api/notification_count';
    } else {
        return;
    }
    
    // Fetch notification count from server
    fetch(endpoint)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.count > 0) {
                countElement.textContent = data.count;
                countElement.style.display = 'inline';
            } else {
                countElement.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error fetching notification count:', error);
        });
}

/**
 * Creates a simple progress chart for metrics
 * @param {string} elementId - The canvas element ID
 * @param {Array} data - The chart data
 * @param {string} label - The chart label
 */
function createProgressChart(elementId, data, label) {
    const ctx = document.getElementById(elementId).getContext('2d');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.date),
            datasets: [{
                label: label,
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
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });
}

/**
 * Quick access to frequently used charts
 */
const dashboardCharts = {
    /**
     * Creates a team comparison radar chart
     * @param {string} elementId - The canvas element ID
     * @param {Array} athletes - The athletes data
     * @param {Array} metrics - The metrics data
     */
    createTeamRadarChart: function(elementId, athletes, metrics) {
        const ctx = document.getElementById(elementId);
        if (!ctx) return;
        
        const labels = metrics.map(m => m.name);
        const datasets = athletes.map((athlete, index) => {
            const hue = (index * 137) % 360;
            return {
                label: athlete.name,
                data: metrics.map(metric => {
                    const perf = athlete.performances.find(p => p.metric === metric.name);
                    return perf ? perf.value : 0;
                }),
                backgroundColor: `hsla(${hue}, 70%, 60%, 0.3)`,
                borderColor: `hsl(${hue}, 70%, 60%)`,
                borderWidth: 2
            };
        });
        
        new Chart(ctx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                elements: {
                    line: {
                        tension: 0.4
                    }
                }
            }
        });
    },
    
    /**
     * Creates a metric progression line chart
     * @param {string} elementId - The canvas element ID
     * @param {Array} performances - The performance data
     * @param {string} metricName - The metric name
     */
    createMetricProgressChart: function(elementId, performances, metricName) {
        const ctx = document.getElementById(elementId);
        if (!ctx) return;
        
        // Sort performances by date
        performances.sort((a, b) => new Date(a.date) - new Date(b.date));
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: performances.map(p => p.date),
                datasets: [{
                    label: metricName,
                    data: performances.map(p => p.value),
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
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
    }
};
