document.addEventListener('DOMContentLoaded', function() {
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
    
    // Template for variant inputs
    const variantTemplate = document.getElementById('variantTemplate');
    
    // Counter for variant numbering
    let variantCounter = 0;
    
    // Add initial variants (at least 2)
    addVariant('A');
    addVariant('B');
    
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
            
            row.innerHTML = `
                <td>${variant.variant}</td>
                <td>${variant.expected_loss.toLocaleString()}</td>
                <td>${formatProbability(variant.prob_being_best)}</td>
                <td>${formatLift(variant.lift)}</td>
            `;
            
            conversionTable.appendChild(row);
        });
        
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
            
            row.innerHTML = `
                <td>${variant.variant}</td>
                <td>${variant.expected_loss}</td>
                <td>${formatProbability(variant.prob_being_best)}</td>
                <td>${formatLift(variant.lift)}</td>
            `;
            
            arpuTable.appendChild(row);
        });
        
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
            
            row.innerHTML = `
                <td>${variant.variant}</td>
                <td>${variant.expected_loss}</td>
                <td>${formatProbability(variant.prob_being_best)}</td>
                <td>${formatLift(variant.lift)}</td>
            `;
            
            revenuePerSaleTable.appendChild(row);
        });
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
}); 