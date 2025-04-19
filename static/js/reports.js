/**
 * Reports functionality for the Sports Performance Tracker
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize form event listeners
    initReportFormHandlers();
    
    // Initialize date pickers with sensible defaults
    initDatePickers();
    
    // PDF generation
    initPdfGeneration();
});

/**
 * Initializes report form event handlers
 */
function initReportFormHandlers() {
    // Report type change handler
    const reportTypeSelect = document.getElementById('report_type');
    if (reportTypeSelect) {
        reportTypeSelect.addEventListener('change', function() {
            updateReportFormFields(this.value);
        });
        
        // Trigger change to initialize form
        if (reportTypeSelect.value) {
            updateReportFormFields(reportTypeSelect.value);
        }
    }
    
    // Team change handler
    const teamSelect = document.getElementById('team_id');
    if (teamSelect) {
        teamSelect.addEventListener('change', function() {
            updateMetricOptions(this.value);
        });
    }
}

/**
 * Updates form fields based on selected report type
 * @param {string} reportType - The selected report type
 */
function updateReportFormFields(reportType) {
    // Fields that are shown/hidden based on report type
    const metricField = document.getElementById('metric_field');
    const athleteField = document.getElementById('athlete_field');
    
    if (!metricField && !athleteField) return;
    
    switch (reportType) {
        case 'team_performance':
            if (metricField) metricField.style.display = 'block';
            if (athleteField) athleteField.style.display = 'none';
            break;
            
        case 'athlete_comparison':
            if (metricField) metricField.style.display = 'block';
            if (athleteField) athleteField.style.display = 'block';
            break;
            
        default:
            // Default behavior for other report types
            if (metricField) metricField.style.display = 'block';
            if (athleteField) athleteField.style.display = 'none';
    }
    
    // Update report preview
    updateReportPreview(reportType);
}

/**
 * Updates available metrics based on selected team
 * @param {string} teamId - The selected team ID
 */
function updateMetricOptions(teamId) {
    if (!teamId) return;
    
    const metricSelect = document.getElementById('metric_name');
    if (!metricSelect) return;
    
    // Fetch metrics for selected team
    fetch(`/api/teams/${teamId}/metrics`)
        .then(response => response.json())
        .then(data => {
            // Clear existing options
            metricSelect.innerHTML = '';
            
            // Add new options
            data.forEach(metric => {
                const option = document.createElement('option');
                option.value = metric.name;
                option.textContent = metric.name;
                metricSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error fetching metrics:', error);
        });
        
    // Update athlete options if athlete field exists
    const athleteSelect = document.getElementById('athlete_id');
    if (athleteSelect) {
        fetch(`/api/teams/${teamId}/athletes`)
            .then(response => response.json())
            .then(data => {
                // Clear existing options
                athleteSelect.innerHTML = '';
                
                // Add "All Athletes" option
                const allOption = document.createElement('option');
                allOption.value = '';
                allOption.textContent = 'All Athletes';
                athleteSelect.appendChild(allOption);
                
                // Add athlete options
                data.forEach(athlete => {
                    const option = document.createElement('option');
                    option.value = athlete.id;
                    option.textContent = athlete.name;
                    athleteSelect.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Error fetching athletes:', error);
            });
    }
}

/**
 * Updates the report preview based on selected options
 * @param {string} reportType - The selected report type
 */
function updateReportPreview(reportType) {
    const preview = document.getElementById('reportPreview');
    if (!preview) return;
    
    // Update preview content based on report type
    let previewContent = '';
    switch (reportType) {
        case 'team_performance':
            previewContent = `
                <div class="mb-3">
                    <i class="fas fa-users fa-4x text-primary"></i>
                </div>
                <h5>Team Performance Report</h5>
                <p class="text-muted">This report shows comprehensive performance data for all athletes in the selected team.</p>
                <p class="text-muted">Includes performance trends, averages, and individual metrics.</p>
            `;
            break;
            
        case 'athlete_comparison':
            previewContent = `
                <div class="mb-3">
                    <i class="fas fa-chart-bar fa-4x text-primary"></i>
                </div>
                <h5>Athlete Comparison Report</h5>
                <p class="text-muted">This report compares performance metrics across athletes in the selected team.</p>
                <p class="text-muted">Helpful for identifying strengths and areas for improvement among teammates.</p>
            `;
            break;
            
        default:
            previewContent = `
                <div class="mb-3">
                    <i class="fas fa-file-alt fa-4x text-muted"></i>
                </div>
                <h5>Select options and generate a report</h5>
                <p class="text-muted">Your report will appear here after generation</p>
            `;
    }
    
    preview.innerHTML = previewContent;
}

/**
 * Initializes date pickers with sensible defaults
 */
function initDatePickers() {
    const dateFromInput = document.getElementById('date_from');
    const dateToInput = document.getElementById('date_to');
    
    if (dateFromInput && !dateFromInput.value) {
        // Set default date from (30 days ago)
        const dateFrom = new Date();
        dateFrom.setDate(dateFrom.getDate() - 30);
        dateFromInput.value = dateFrom.toISOString().split('T')[0];
    }
    
    if (dateToInput && !dateToInput.value) {
        // Set default date to (today)
        const dateTo = new Date();
        dateToInput.value = dateTo.toISOString().split('T')[0];
    }
}

/**
 * Initializes PDF generation functionality
 */
function initPdfGeneration() {
    const downloadReportBtn = document.getElementById('downloadReportBtn');
    if (!downloadReportBtn) return;
    
    downloadReportBtn.addEventListener('click', function() {
        generatePdfReport();
    });
}

/**
 * Generates a PDF report from the report data
 */
function generatePdfReport() {
    // Check if jsPDF is available
    if (typeof jsPDF === 'undefined') {
        console.error('jsPDF is not available');
        alert('PDF generation library is not available');
        return;
    }
    
    // Basic report info
    const reportTitle = document.querySelector('h1').textContent;
    const subtitle = document.querySelector('p.lead').textContent;
    const date = new Date().toLocaleDateString();
    
    // Create PDF
    const doc = new jsPDF();
    
    // Add report header
    doc.setFontSize(22);
    doc.text(reportTitle, 20, 20);
    
    doc.setFontSize(14);
    doc.text(subtitle, 20, 30);
    
    doc.setFontSize(12);
    doc.text(`Generated on: ${date}`, 20, 40);
    
    // Add report parameters
    doc.setFontSize(14);
    doc.text('Report Parameters', 20, 55);
    
    // Extract parameters from the page
    const params = {};
    document.querySelectorAll('.card-body .row .col-md-3').forEach(col => {
        const label = col.querySelector('p.fw-bold').textContent.replace(':', '');
        const value = col.querySelectorAll('p')[1].textContent;
        params[label] = value;
    });
    
    let yPos = 60;
    Object.entries(params).forEach(([key, value], index) => {
        doc.setFontSize(10);
        doc.text(`${key}: ${value}`, 20, yPos + (index * 7));
    });
    
    // Add report content
    yPos = 90;
    
    // Check report type and add appropriate content
    if (params['Report Type'] === 'Team Performance') {
        // Add performance table if available
        const table = document.getElementById('performanceTable');
        if (table) {
            doc.setFontSize(14);
            doc.text('Performance Data', 20, yPos);
            yPos += 10;
            
            // Get table headers
            const headers = [];
            table.querySelectorAll('thead th').forEach(th => {
                headers.push(th.textContent);
            });
            
            // Get table data
            const data = [];
            table.querySelectorAll('tbody tr').forEach(tr => {
                const row = [];
                tr.querySelectorAll('td').forEach(td => {
                    row.push(td.textContent);
                });
                data.push(row);
            });
            
            // Add table to PDF
            doc.autoTable({
                head: [headers],
                body: data,
                startY: yPos,
                theme: 'striped',
                styles: { fontSize: 8 },
                headStyles: { fillColor: [30, 70, 150] }
            });
            
            yPos = doc.lastAutoTable.finalY + 15;
        }
        
        // Add performance chart if available
        const chart = document.getElementById('performanceChart');
        if (chart) {
            doc.setFontSize(14);
            doc.text('Performance Chart', 20, yPos);
            yPos += 10;
            
            // Convert chart to image
            const chartImage = chart.toDataURL('image/png');
            doc.addImage(chartImage, 'PNG', 20, yPos, 170, 80);
            
            yPos += 90;
        }
    } else if (params['Report Type'] === 'Athlete Comparison') {
        // Add comparison table if available
        const table = document.getElementById('comparisonTable');
        if (table) {
            doc.setFontSize(14);
            doc.text('Athlete Comparison', 20, yPos);
            yPos += 10;
            
            // Get table headers
            const headers = [];
            table.querySelectorAll('thead th').forEach(th => {
                headers.push(th.textContent);
            });
            
            // Get table data
            const data = [];
            table.querySelectorAll('tbody tr').forEach(tr => {
                const row = [];
                tr.querySelectorAll('td').forEach(td => {
                    row.push(td.textContent);
                });
                data.push(row);
            });
            
            // Add table to PDF
            doc.autoTable({
                head: [headers],
                body: data,
                startY: yPos,
                theme: 'striped',
                styles: { fontSize: 8 },
                headStyles: { fillColor: [30, 70, 150] }
            });
            
            yPos = doc.lastAutoTable.finalY + 15;
        }
        
        // Add comparison chart if available
        const chart = document.getElementById('comparisonChart');
        if (chart) {
            doc.setFontSize(14);
            doc.text('Comparison Chart', 20, yPos);
            yPos += 10;
            
            // Convert chart to image
            const chartImage = chart.toDataURL('image/png');
            doc.addImage(chartImage, 'PNG', 20, yPos, 170, 80);
            
            yPos += 90;
        }
    }
    
    // Add insights and recommendations
    if (yPos < 250) {
        doc.setFontSize(14);
        doc.text('Insights & Recommendations', 20, yPos);
        yPos += 10;
        
        // Extract insights from page
        const insights = [];
        document.querySelectorAll('#insight1, #insight2, #insight3').forEach(el => {
            if (el) insights.push(el.textContent);
        });
        
        const recommendations = [];
        document.querySelectorAll('#rec1, #rec2, #rec3').forEach(el => {
            if (el) recommendations.push(el.textContent);
        });
        
        doc.setFontSize(12);
        doc.text('Performance Insights:', 20, yPos);
        yPos += 7;
        
        insights.forEach((insight, index) => {
            doc.setFontSize(10);
            doc.text(`• ${insight}`, 25, yPos + (index * 6));
        });
        
        yPos += (insights.length * 6) + 10;
        
        doc.setFontSize(12);
        doc.text('Recommendations:', 20, yPos);
        yPos += 7;
        
        recommendations.forEach((rec, index) => {
            doc.setFontSize(10);
            doc.text(`• ${rec}`, 25, yPos + (index * 6));
        });
    }
    
    // Add footer
    doc.setFontSize(8);
    doc.text('Generated by Sports Performance Tracker', 105, 285, { align: 'center' });
    
    // Save PDF
    doc.save(`performance_report_${date.replace(/\//g, '-')}.pdf`);
}

/**
 * Exports performance data to CSV
 * @param {Array} data - The performance data
 * @param {string} filename - The output filename
 */
function exportToCsv(data, filename) {
    if (!data || data.length === 0) {
        console.error('No data to export');
        return;
    }
    
    // Get headers from first data object
    const headers = Object.keys(data[0]);
    
    // Create CSV content
    let csvContent = headers.join(',') + '\n';
    
    data.forEach(row => {
        const values = headers.map(header => {
            const value = row[header];
            // Handle values that need quotes (contain commas, quotes, or newlines)
            if (typeof value === 'string' && (value.includes(',') || value.includes('"') || value.includes('\n'))) {
                return `"${value.replace(/"/g, '""')}"`;
            }
            return value;
        });
        csvContent += values.join(',') + '\n';
    });
    
    // Create and trigger download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
