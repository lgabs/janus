document.addEventListener('DOMContentLoaded', function() {
    // Check if Chart.js is available
    if (typeof Chart === 'undefined') {
        console.error('Chart.js not loaded, charts will not be displayed');
    } else {
        console.log('Chart.js is available, version:', Chart.version);
    }
    
    // DOM elements
    const experimentForm = document.getElementById('experimentForm');
    const variantsContainer = document.getElementById('variantsContainer');
    const addVariantBtn = document.getElementById('addVariantBtn');
    const baselineVariantInput = document.getElementById('baselineVariant');
    const resultsSection = document.getElementById('resultsSection');
    const summaryTable = document.getElementById('summaryTable').querySelector('tbody');
    const conversionTable = document.getElementById('conversionTable').querySelector('tbody');
    const arpuTable = document.getElementById('arpuTable').querySelector('tbody');
    const revenuePerSaleTable = document.getElementById('revenuePerSaleTable').querySelector('tbody');
    const exportResultsBtn = document.getElementById('exportResultsBtn');
    const conversionDistributionChart = document.getElementById('conversionDistributionChart');
    const arpuDistributionChart = document.getElementById('arpuDistributionChart');
    const revenuePerSaleDistributionChart = document.getElementById('revenuePerSaleDistributionChart');
    
    // Chart instances
    let distributionChartInstance = null;
    let arpuDistributionChartInstance = null;
    let revenuePerSaleDistributionChartInstance = null;
    
    // Color palette for variants (baseline is always red)
    const variantColors = {
        baseline: 'rgba(220, 53, 69, 0.7)', // Red for baseline
        others: [
            'rgba(0, 123, 255, 0.7)',       // Blue
            'rgba(40, 167, 69, 0.7)',       // Green
            'rgba(255, 193, 7, 0.7)',       // Yellow
            'rgba(165, 42, 42, 0.7)',       // Brown
            'rgba(111, 66, 193, 0.7)',      // Purple
            'rgba(23, 162, 184, 0.7)',      // Cyan
            'rgba(255, 102, 0, 0.7)',       // Orange
            'rgba(0, 128, 128, 0.7)',       // Teal
            'rgba(128, 0, 128, 0.7)'        // Magenta
        ]
    };
    
    // Template for variant inputs
    const variantTemplate = document.getElementById('variantTemplate');
    
    // Counter for variant numbering
    let variantCounter = 0;
    
    // Add initial variants (at least 2)
    addVariant('A');
    addVariant('B');
    
    // Set default values for variants
    setTimeout(() => {
        // Get all variant cards
        const variantCards = document.querySelectorAll('.variant-card');
        
        // Set default values for variant A (baseline)
        if (variantCards.length > 0) {
            const variantA = variantCards[0];
            variantA.querySelector('.variant-impressions').value = 1000;
            variantA.querySelector('.variant-conversions').value = 100;
            variantA.querySelector('.variant-revenue').value = 100;
        }
        
        // Set default values for variant B
        if (variantCards.length > 1) {
            const variantB = variantCards[1];
            variantB.querySelector('.variant-impressions').value = 1000;
            variantB.querySelector('.variant-conversions').value = 120;
            variantB.querySelector('.variant-revenue').value = 110;
        }
        
        // Set variant A as baseline
        baselineVariantInput.value = 'A';
    }, 100);
    
    // Event listeners
    addVariantBtn.addEventListener('click', () => {
        const nextLetter = String.fromCharCode(65 + variantCounter); // A, B, C, ...
        addVariant(nextLetter);
    });
    
    experimentForm.addEventListener('submit', handleFormSubmit);
    exportResultsBtn.addEventListener('click', exportResults);
    
    // Add a new variant input to the form
    function addVariant(suggestedName = '') {
        variantCounter++;
        
        // Clone the template
        const variantNode = document.importNode(variantTemplate.content, true);
        
        // Update variant number
        variantNode.querySelector('.variant-number').textContent = variantCounter;
        
        // Set suggested name if provided
        if (suggestedName) {
            variantNode.querySelector('.variant-name').value = suggestedName;
        }
        
        // Add remove event listener
        variantNode.querySelector('.remove-variant').addEventListener('click', function() {
            this.closest('.variant-card').remove();
            updateVariantNumbers();
        });
        
        // Add to container
        variantsContainer.appendChild(variantNode);
        
        // If this is the first variant, suggest it as baseline
        if (variantCounter === 1 && !baselineVariantInput.value) {
            baselineVariantInput.value = suggestedName;
        }
    }
    
    // Update variant numbers after removal
    function updateVariantNumbers() {
        const variants = variantsContainer.querySelectorAll('.variant-card');
        variants.forEach((variant, index) => {
            variant.querySelector('.variant-number').textContent = index + 1;
        });
        variantCounter = variants.length;
    }
    
    // Handle form submission
    async function handleFormSubmit(event) {
        event.preventDefault();
        
        // Validate form
        if (!validateForm()) {
            return;
        }
        
        // Show loading state
        const submitBtn = experimentForm.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="loading-spinner"></span> Analyzing...';
        submitBtn.disabled = true;
        
        try {
            // Collect form data
            const formData = collectFormData();
            
            // Send API request
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                throw new Error('API request failed');
            }
            
            const data = await response.json();
            
            // Store the data globally for later use
            window.lastAnalysisData = data;
            
            // Display results
            displayResults(data);
            
            // Show results section
            resultsSection.classList.remove('d-none');
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while analyzing the experiment. Please try again.');
        } finally {
            // Restore button state
            submitBtn.innerHTML = originalBtnText;
            submitBtn.disabled = false;
        }
    }
    
    // Validate form inputs
    function validateForm() {
        // Check if baseline variant is specified
        if (!baselineVariantInput.value.trim()) {
            alert('Please specify a baseline variant.');
            baselineVariantInput.focus();
            return false;
        }
        
        // Check if at least 2 variants are added
        const variants = variantsContainer.querySelectorAll('.variant-card');
        if (variants.length < 2) {
            alert('Please add at least 2 variants for comparison.');
            return false;
        }
        
        // Check if baseline variant exists in the variants
        let baselineExists = false;
        const baselineName = baselineVariantInput.value.trim();
        
        variants.forEach(variant => {
            const variantName = variant.querySelector('.variant-name').value.trim();
            if (variantName === baselineName) {
                baselineExists = true;
            }
        });
        
        if (!baselineExists) {
            alert(`Baseline variant "${baselineName}" does not exist. Please add it as a variant or choose an existing variant as baseline.`);
            return false;
        }
        
        // Check for duplicate variant names
        const variantNames = new Set();
        let hasDuplicates = false;
        
        variants.forEach(variant => {
            const variantName = variant.querySelector('.variant-name').value.trim();
            if (variantNames.has(variantName)) {
                hasDuplicates = true;
            }
            variantNames.add(variantName);
        });
        
        if (hasDuplicates) {
            alert('Duplicate variant names found. Please ensure all variants have unique names.');
            return false;
        }
        
        // Check if conversions <= impressions for each variant
        let invalidConversions = false;
        
        variants.forEach(variant => {
            const impressions = parseInt(variant.querySelector('.variant-impressions').value);
            const conversions = parseInt(variant.querySelector('.variant-conversions').value);
            
            if (conversions > impressions) {
                invalidConversions = true;
                variant.querySelector('.variant-conversions').classList.add('is-invalid');
            } else {
                variant.querySelector('.variant-conversions').classList.remove('is-invalid');
            }
        });
        
        if (invalidConversions) {
            alert('Conversions cannot be greater than impressions. Please check your inputs.');
            return false;
        }
        
        return true;
    }
    
    // Collect form data
    function collectFormData() {
        const variants = [];
        const variantElements = variantsContainer.querySelectorAll('.variant-card');
        
        variantElements.forEach(variantElement => {
            variants.push({
                name: variantElement.querySelector('.variant-name').value.trim(),
                impressions: parseInt(variantElement.querySelector('.variant-impressions').value),
                conversions: parseInt(variantElement.querySelector('.variant-conversions').value),
                revenue: parseFloat(variantElement.querySelector('.variant-revenue').value)
            });
        });
        
        return {
            variants: variants,
            baseline_variant: baselineVariantInput.value.trim()
        };
    }
    
    // Display results in tables
    function displayResults(data) {
        // Clear previous results
        summaryTable.innerHTML = '';
        conversionTable.innerHTML = '';
        arpuTable.innerHTML = '';
        revenuePerSaleTable.innerHTML = '';
        
        // Find best variant for each metric
        const bestConversionVariant = findBestVariant(data.conversion_stats, 'prob_being_best');
        const bestArpuVariant = findBestVariant(data.arpu_stats, 'prob_being_best');
        const bestRevenuePerSaleVariant = findBestVariant(data.revenue_per_sale_stats, 'prob_being_best');
        
        // Populate summary table
        data.summary.forEach(variant => {
            const row = document.createElement('tr');
            
            // Highlight baseline
            if (variant.variant === baselineVariantInput.value.trim()) {
                row.classList.add('table-secondary');
            }
            
            row.innerHTML = `
                <td>${variant.variant}</td>
                <td>${variant.impressions.toLocaleString()}</td>
                <td>${variant.conversions.toLocaleString()}</td>
                <td>${variant.revenue}</td>
                <td>${formatPercentage(variant.conversion)}</td>
                <td>${variant.avg_ticket}</td>
                <td>${variant.arpu}</td>
            `;
            
            summaryTable.appendChild(row);
        });
        
        // Populate conversion stats table
        data.conversion_stats.forEach(variant => {
            const row = document.createElement('tr');
            
            // Highlight baseline and best variant
            if (variant.variant === baselineVariantInput.value.trim()) {
                row.classList.add('table-secondary');
            }
            if (variant.variant === bestConversionVariant) {
                row.classList.add('best-variant');
            }
            
            // Add posterior mean column
            const posteriorMean = variant.posterior_mean !== undefined ? 
                formatPercentage(variant.posterior_mean) : 
                formatPercentage(data.summary.find(v => v.variant === variant.variant)?.conversion || 0);
            
            row.innerHTML = `
                <td>${variant.variant}</td>
                <td>${posteriorMean}</td>
                <td>${variant.expected_loss.toLocaleString()}</td>
                <td>${formatProbability(variant.prob_being_best)}</td>
                <td>${formatLift(variant.lift)}</td>
            `;
            
            conversionTable.appendChild(row);
        });
        
        // Create conversion distribution chart
        createConversionDistributionChart(data.conversion_distributions);
        
        // Populate ARPU stats table
        data.arpu_stats.forEach(variant => {
            const row = document.createElement('tr');
            
            // Highlight baseline and best variant
            if (variant.variant === baselineVariantInput.value.trim()) {
                row.classList.add('table-secondary');
            }
            if (variant.variant === bestArpuVariant) {
                row.classList.add('best-variant');
            }
            
            // Add posterior mean column
            const posteriorMean = variant.posterior_mean !== undefined ? 
                variant.posterior_mean.toFixed(4) : 
                data.summary.find(v => v.variant === variant.variant)?.arpu.toFixed(4) || "0.0000";
            
            row.innerHTML = `
                <td>${variant.variant}</td>
                <td>${posteriorMean}</td>
                <td>${variant.expected_loss}</td>
                <td>${formatProbability(variant.prob_being_best)}</td>
                <td>${formatLift(variant.lift)}</td>
            `;
            
            arpuTable.appendChild(row);
        });
        
        // Create ARPU distribution chart
        createArpuDistributionChart(data.arpu_distributions);
        
        // Populate revenue per sale stats table
        data.revenue_per_sale_stats.forEach(variant => {
            const row = document.createElement('tr');
            
            // Highlight baseline and best variant
            if (variant.variant === baselineVariantInput.value.trim()) {
                row.classList.add('table-secondary');
            }
            if (variant.variant === bestRevenuePerSaleVariant) {
                row.classList.add('best-variant');
            }
            
            // Add posterior mean column
            const posteriorMean = variant.posterior_mean !== undefined ? 
                variant.posterior_mean.toFixed(4) : 
                data.summary.find(v => v.variant === variant.variant)?.avg_ticket.toFixed(4) || "0.0000";
            
            row.innerHTML = `
                <td>${variant.variant}</td>
                <td>${posteriorMean}</td>
                <td>${variant.expected_loss}</td>
                <td>${formatProbability(variant.prob_being_best)}</td>
                <td>${formatLift(variant.lift)}</td>
            `;
            
            revenuePerSaleTable.appendChild(row);
        });
        
        // Create Revenue Per Sale distribution chart
        createRevenuePerSaleDistributionChart(data.revenue_per_sale_distributions);
    }
    
    // Find the best variant based on a metric
    function findBestVariant(variants, metric) {
        let bestVariant = null;
        let bestValue = -Infinity;
        
        variants.forEach(variant => {
            if (variant[metric] > bestValue) {
                bestValue = variant[metric];
                bestVariant = variant.variant;
            }
        });
        
        return bestVariant;
    }
    
    // Format percentage values
    function formatPercentage(value) {
        return (value * 100).toFixed(4) + '%';
    }
    
    // Format lift values
    function formatLift(value) {
        const sign = value >= 0 ? '+' : '';
        const className = value >= 0 ? 'text-success' : 'text-danger';
        return `<span class="${className}">${sign}${(value * 100).toFixed(4)}%</span>`;
    }
    
    // Format probability values with color coding
    function formatProbability(value) {
        let className = 'low-prob';
        if (value >= 0.8) {
            className = 'high-prob';
        } else if (value >= 0.5) {
            className = 'medium-prob';
        }
        
        return `<span class="prob-value ${className}">${(value * 100).toFixed(4)}%</span>`;
    }
    
    // Export results as CSV
    function exportResults() {
        // Get table data
        const summaryData = getTableData(document.getElementById('summaryTable'));
        const conversionData = getTableData(document.getElementById('conversionTable'));
        const arpuData = getTableData(document.getElementById('arpuTable'));
        const revenuePerSaleData = getTableData(document.getElementById('revenuePerSaleTable'));
        
        // Combine data
        const csvContent = [
            '# Summary',
            summaryData,
            '',
            '# Conversion Statistics',
            conversionData,
            '',
            '# ARPU Statistics',
            arpuData,
            '',
            '# Revenue Per Sale Statistics',
            revenuePerSaleData
        ].join('\n');
        
        // Create download link
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', 'experiment_results.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    // Get table data as CSV
    function getTableData(table) {
        const rows = Array.from(table.querySelectorAll('tr'));
        
        return rows.map(row => {
            const cells = Array.from(row.querySelectorAll('th, td'));
            return cells.map(cell => {
                // Get text content without HTML
                return `"${cell.textContent.trim().replace(/"/g, '""')}"`;
            }).join(',');
        }).join('\n');
    }
    
    // Create conversion distribution chart
    function createConversionDistributionChart(distributionData) {
        // If there's an existing chart, destroy it
        if (distributionChartInstance) {
            distributionChartInstance.destroy();
        }
        
        // Prepare data for the chart
        const datasets = [];
        const baselineVariant = baselineVariantInput.value.trim();
        let colorIndex = 0;
        
        // Process each variant's distribution
        for (const [variantName, distribution] of Object.entries(distributionData)) {
            // Calculate kernel density estimation for smoother visualization
            const kdePoints = calculateKDE(distribution);
            
            // Determine color based on whether it's baseline or not
            let color;
            if (variantName === baselineVariant) {
                color = variantColors.baseline;
            } else {
                color = variantColors.others[colorIndex % variantColors.others.length];
                colorIndex++;
            }
            
            datasets.push({
                label: variantName,
                data: kdePoints,
                borderColor: color,
                backgroundColor: color.replace('0.7', '0.2'),
                borderWidth: 2,
                pointRadius: 0,
                fill: true,
                tension: 0.4
            });
            
            // Find posterior mean for this variant
            const variantData = window.lastAnalysisData?.conversion_stats.find(v => v.variant === variantName);
            let posteriorMean = null;
            
            if (variantData) {
                if (variantData.posterior_mean !== undefined) {
                    posteriorMean = variantData.posterior_mean;
                } else {
                    // If posterior_mean is not available, try to use conversion rate from summary
                    const summaryData = window.lastAnalysisData?.summary.find(v => v.variant === variantName);
                    if (summaryData && summaryData.conversion !== undefined) {
                        posteriorMean = summaryData.conversion;
                    }
                }
            }
            
            if (posteriorMean !== null) {
                // Add a vertical line dataset for the posterior mean
                datasets.push({
                    label: `${variantName} Mean`,
                    data: [
                        { x: posteriorMean, y: 0 },
                        { x: posteriorMean, y: 50 } // Use a high value to ensure it spans the chart
                    ],
                    borderColor: color,
                    borderWidth: 2,
                    borderDash: [6, 4],
                    pointRadius: 0,
                    fill: false,
                    tension: 0,
                    showLine: true
                });
            }
        }
        
        // Create chart options
        const chartOptions = {
            scales: {
                x: {
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'Conversion Rate',
                        padding: {
                            top: 15,
                            bottom: 10
                        }
                    },
                    ticks: {
                        callback: function(value) {
                            return (value * 100).toFixed(1) + '%';
                        }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Density'
                    },
                    beginAtZero: true
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            const value = context[0].parsed.x;
                            return 'Conversion Rate: ' + (value * 100).toFixed(2) + '%';
                        }
                    },
                    filter: function(tooltipItem) {
                        // Hide tooltips for the mean lines
                        return !tooltipItem.dataset.label.includes('Mean');
                    }
                },
                legend: {
                    position: 'right',
                    align: 'start',
                    labels: {
                        boxWidth: 12,
                        font: {
                            size: 11
                        },
                        filter: function(legendItem, chartData) {
                            // Hide the mean lines from the legend
                            return !legendItem.text.includes('Mean');
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Conversion Rate Distributions',
                    font: {
                        size: 14
                    },
                    padding: {
                        top: 10,
                        bottom: 20
                    }
                }
            },
            layout: {
                padding: {
                    top: 30,  // Add padding at the top for variant labels
                    right: 10,
                    bottom: 10,
                    left: 10
                }
            },
            interaction: {
                mode: 'nearest',
                intersect: false
            },
            responsive: true,
            maintainAspectRatio: false
        };
        
        // Create the chart
        try {
            console.log('Creating chart with options:', chartOptions);
            distributionChartInstance = new Chart(conversionDistributionChart, {
                type: 'line',
                data: {
                    datasets: datasets
                },
                options: chartOptions
            });
        } catch (error) {
            console.error('Error creating chart:', error);
        }
    }
    
    // Calculate Kernel Density Estimation for smoother distribution visualization
    function calculateKDE(data) {
        // Sort the data
        const sortedData = [...data].sort((a, b) => a - b);
        
        // Determine min and max for the range
        const min = Math.max(0, sortedData[0] - 0.01);
        const max = sortedData[sortedData.length - 1] + 0.01;
        
        // Generate points for the KDE
        const points = [];
        const bandwidth = 0.005; // Adjust based on your data
        const numPoints = 100;
        
        for (let i = 0; i < numPoints; i++) {
            const x = min + (i / (numPoints - 1)) * (max - min);
            let density = 0;
            
            // Calculate density at point x
            for (const value of sortedData) {
                const z = (x - value) / bandwidth;
                density += Math.exp(-0.5 * z * z) / (bandwidth * Math.sqrt(2 * Math.PI));
            }
            
            density /= sortedData.length;
            points.push({x, y: density});
        }
        
        return points;
    }
    
    // Create ARPU distribution chart
    function createArpuDistributionChart(distributionData) {
        // If there's an existing chart, destroy it
        if (arpuDistributionChartInstance) {
            arpuDistributionChartInstance.destroy();
        }
        
        // Prepare data for the chart
        const datasets = [];
        const baselineVariant = baselineVariantInput.value.trim();
        let colorIndex = 0;
        
        // Process each variant's distribution
        for (const [variantName, distribution] of Object.entries(distributionData)) {
            // Calculate kernel density estimation for smoother visualization
            const kdePoints = calculateKDE(distribution);
            
            // Determine color based on whether it's baseline or not
            let color;
            if (variantName === baselineVariant) {
                color = variantColors.baseline;
            } else {
                color = variantColors.others[colorIndex % variantColors.others.length];
                colorIndex++;
            }
            
            datasets.push({
                label: variantName,
                data: kdePoints,
                borderColor: color,
                backgroundColor: color.replace('0.7', '0.2'),
                borderWidth: 2,
                pointRadius: 0,
                fill: true,
                tension: 0.4
            });
            
            // Find posterior mean for this variant
            const variantData = window.lastAnalysisData?.arpu_stats.find(v => v.variant === variantName);
            let posteriorMean = null;
            
            if (variantData) {
                if (variantData.posterior_mean !== undefined) {
                    posteriorMean = variantData.posterior_mean;
                } else {
                    // If posterior_mean is not available, try to use ARPU from summary
                    const summaryData = window.lastAnalysisData?.summary.find(v => v.variant === variantName);
                    if (summaryData && summaryData.arpu !== undefined) {
                        posteriorMean = summaryData.arpu;
                    }
                }
            }
            
            if (posteriorMean !== null) {
                // Add a vertical line dataset for the posterior mean
                datasets.push({
                    label: `${variantName} Mean`,
                    data: [
                        { x: posteriorMean, y: 0 },
                        { x: posteriorMean, y: 50 } // Use a high value to ensure it spans the chart
                    ],
                    borderColor: color,
                    borderWidth: 2,
                    borderDash: [6, 4],
                    pointRadius: 0,
                    fill: false,
                    tension: 0,
                    showLine: true
                });
            }
        }
        
        // Create chart options
        const chartOptions = {
            scales: {
                x: {
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'ARPU (Average Revenue Per User)',
                        padding: {
                            top: 15,
                            bottom: 10
                        }
                    },
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(2);
                        }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Density'
                    },
                    beginAtZero: true
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            const value = context[0].parsed.x;
                            return 'ARPU: ' + value.toFixed(4);
                        }
                    },
                    filter: function(tooltipItem) {
                        // Hide tooltips for the mean lines
                        return !tooltipItem.dataset.label.includes('Mean');
                    }
                },
                legend: {
                    position: 'right',
                    align: 'start',
                    labels: {
                        boxWidth: 12,
                        font: {
                            size: 11
                        },
                        filter: function(legendItem, chartData) {
                            // Hide the mean lines from the legend
                            return !legendItem.text.includes('Mean');
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'ARPU Distributions',
                    font: {
                        size: 14
                    },
                    padding: {
                        top: 10,
                        bottom: 20
                    }
                }
            },
            layout: {
                padding: {
                    top: 30,  // Add padding at the top for variant labels
                    right: 10,
                    bottom: 10,
                    left: 10
                }
            },
            interaction: {
                mode: 'nearest',
                intersect: false
            },
            responsive: true,
            maintainAspectRatio: false
        };
        
        // Create the chart
        try {
            console.log('Creating ARPU chart with options:', chartOptions);
            arpuDistributionChartInstance = new Chart(arpuDistributionChart, {
                type: 'line',
                data: {
                    datasets: datasets
                },
                options: chartOptions
            });
        } catch (error) {
            console.error('Error creating ARPU chart:', error);
        }
    }
    
    // Create Revenue Per Sale distribution chart
    function createRevenuePerSaleDistributionChart(distributionData) {
        // If there's an existing chart, destroy it
        if (revenuePerSaleDistributionChartInstance) {
            revenuePerSaleDistributionChartInstance.destroy();
        }
        
        // Prepare data for the chart
        const datasets = [];
        const baselineVariant = baselineVariantInput.value.trim();
        let colorIndex = 0;
        
        // Process each variant's distribution
        for (const [variantName, distribution] of Object.entries(distributionData)) {
            // Calculate kernel density estimation for smoother visualization
            const kdePoints = calculateKDE(distribution);
            
            // Determine color based on whether it's baseline or not
            let color;
            if (variantName === baselineVariant) {
                color = variantColors.baseline;
            } else {
                color = variantColors.others[colorIndex % variantColors.others.length];
                colorIndex++;
            }
            
            datasets.push({
                label: variantName,
                data: kdePoints,
                borderColor: color,
                backgroundColor: color.replace('0.7', '0.2'),
                borderWidth: 2,
                pointRadius: 0,
                fill: true,
                tension: 0.4
            });
            
            // Find posterior mean for this variant
            const variantData = window.lastAnalysisData?.revenue_per_sale_stats.find(v => v.variant === variantName);
            let posteriorMean = null;
            
            if (variantData) {
                if (variantData.posterior_mean !== undefined) {
                    posteriorMean = variantData.posterior_mean;
                } else {
                    // If posterior_mean is not available, try to use avg_ticket from summary
                    const summaryData = window.lastAnalysisData?.summary.find(v => v.variant === variantName);
                    if (summaryData && summaryData.avg_ticket !== undefined) {
                        posteriorMean = summaryData.avg_ticket;
                    }
                }
            }
            
            if (posteriorMean !== null) {
                // Add a vertical line dataset for the posterior mean
                datasets.push({
                    label: `${variantName} Mean`,
                    data: [
                        { x: posteriorMean, y: 0 },
                        { x: posteriorMean, y: 50 } // Use a high value to ensure it spans the chart
                    ],
                    borderColor: color,
                    borderWidth: 2,
                    borderDash: [6, 4],
                    pointRadius: 0,
                    fill: false,
                    tension: 0,
                    showLine: true
                });
            }
        }
        
        // Create chart options
        const chartOptions = {
            scales: {
                x: {
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'Revenue Per Sale',
                        padding: {
                            top: 15,
                            bottom: 10
                        }
                    },
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(2);
                        }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Density'
                    },
                    beginAtZero: true
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            const value = context[0].parsed.x;
                            return 'Revenue Per Sale: ' + value.toFixed(4);
                        }
                    },
                    filter: function(tooltipItem) {
                        // Hide tooltips for the mean lines
                        return !tooltipItem.dataset.label.includes('Mean');
                    }
                },
                legend: {
                    position: 'right',
                    align: 'start',
                    labels: {
                        boxWidth: 12,
                        font: {
                            size: 11
                        },
                        filter: function(legendItem, chartData) {
                            // Hide the mean lines from the legend
                            return !legendItem.text.includes('Mean');
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Revenue Per Sale Distributions',
                    font: {
                        size: 14
                    },
                    padding: {
                        top: 10,
                        bottom: 20
                    }
                }
            },
            layout: {
                padding: {
                    top: 30,  // Add padding at the top for variant labels
                    right: 10,
                    bottom: 10,
                    left: 10
                }
            },
            interaction: {
                mode: 'nearest',
                intersect: false
            },
            responsive: true,
            maintainAspectRatio: false
        };
        
        // Create the chart
        try {
            console.log('Creating Revenue Per Sale chart with options:', chartOptions);
            revenuePerSaleDistributionChartInstance = new Chart(revenuePerSaleDistributionChart, {
                type: 'line',
                data: {
                    datasets: datasets
                },
                options: chartOptions
            });
        } catch (error) {
            console.error('Error creating Revenue Per Sale chart:', error);
        }
    }
}); 