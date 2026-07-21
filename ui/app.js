document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const elements = {
        groupingModes: document.getElementsByName('grouping_mode'),
        
        // Sliders
        weightCommute: document.getElementById('weight-commute'),
        weightHousing: document.getElementById('weight-housing'),
        weightCrime: document.getElementById('weight-crime'),
        
        hweightPrice: document.getElementById('hweight-price'),
        hweightPpsf: document.getElementById('hweight-ppsf'),
        hweightTax: document.getElementById('hweight-tax'),
        
        commuteIdeal: document.getElementById('commute-ideal'),
        commuteMax: document.getElementById('commute-max'),
        
        budgetMin: document.getElementById('budget-min'),
        budgetIdeal: document.getElementById('budget-ideal'),
        budgetMax: document.getElementById('budget-max'),
        
        // Value spans
        valWeightCommute: document.getElementById('val-weight-commute'),
        valWeightHousing: document.getElementById('val-weight-housing'),
        valWeightCrime: document.getElementById('val-weight-crime'),
        
        valHweightPrice: document.getElementById('val-hweight-price'),
        valHweightPpsf: document.getElementById('val-hweight-ppsf'),
        valHweightTax: document.getElementById('val-hweight-tax'),
        
        valCommuteIdeal: document.getElementById('val-commute-ideal'),
        valCommuteMax: document.getElementById('val-commute-max'),
        
        valBudgetMin: document.getElementById('val-budget-min'),
        valBudgetIdeal: document.getElementById('val-budget-ideal'),
        valBudgetMax: document.getElementById('val-budget-max'),
        
        // UI
        weightWarning: document.getElementById('weight-warning'),
        hweightWarning: document.getElementById('hweight-warning'),
        btnSave: document.getElementById('btn-save'),
        loader: document.getElementById('loading-indicator'),
        tableBody: document.getElementById('table-body'),
        resultCount: document.getElementById('result-count')
    };

    let debounceTimer;
    let baseConfig = {};

    // Initialization
    async function init() {
        try {
            const response = await fetch('/api/config');
            baseConfig = await response.json();
            populateUIFromConfig();
            fetchScores();
        } catch (error) {
            console.error('Failed to load initial config:', error);
        }
    }

    // Populate sliders from backend config
    function populateUIFromConfig() {
        if (baseConfig.weights) {
            elements.weightCommute.value = baseConfig.weights.commute * 100;
            elements.weightHousing.value = baseConfig.weights.housing * 100;
            elements.weightCrime.value = baseConfig.weights.crime * 100;
        }
        
        if (baseConfig.housing_preferences && baseConfig.housing_preferences.housing_weights) {
            const hw = baseConfig.housing_preferences.housing_weights;
            elements.hweightPrice.value = hw.price * 100;
            elements.hweightPpsf.value = hw.ppsf * 100;
            elements.hweightTax.value = hw.tax * 100;
        }

        if (baseConfig.work_address_1 && baseConfig.work_address_1.preferences) {
            const p = baseConfig.work_address_1.preferences;
            elements.commuteIdeal.value = p.ideal_time_mins;
            elements.commuteMax.value = p.max_acceptable_time_mins;
        }

        if (baseConfig.housing_preferences) {
            const hp = baseConfig.housing_preferences;
            elements.budgetMin.value = hp.budget_min / 1000;
            elements.budgetIdeal.value = hp.budget_ideal / 1000;
            elements.budgetMax.value = hp.budget_max / 1000;
        }

        updateLabels();
    }

    // Update span labels
    function updateLabels() {
        elements.valWeightCommute.innerText = elements.weightCommute.value;
        elements.valWeightHousing.innerText = elements.weightHousing.value;
        elements.valWeightCrime.innerText = elements.weightCrime.value;
        
        elements.valHweightPrice.innerText = elements.hweightPrice.value;
        elements.valHweightPpsf.innerText = elements.hweightPpsf.value;
        elements.valHweightTax.innerText = elements.hweightTax.value;
        
        elements.valCommuteIdeal.innerText = elements.commuteIdeal.value;
        elements.valCommuteMax.innerText = elements.commuteMax.value;
        
        elements.valBudgetMin.innerText = elements.budgetMin.value;
        elements.valBudgetIdeal.innerText = elements.budgetIdeal.value;
        elements.valBudgetMax.innerText = elements.budgetMax.value;

        // Check sum constraints
        const totalWeight = parseInt(elements.weightCommute.value) + parseInt(elements.weightHousing.value) + parseInt(elements.weightCrime.value);
        if (totalWeight !== 100) {
            elements.weightWarning.classList.remove('hidden');
        } else {
            elements.weightWarning.classList.add('hidden');
        }

        const totalHweight = parseInt(elements.hweightPrice.value) + parseInt(elements.hweightPpsf.value) + parseInt(elements.hweightTax.value);
        if (totalHweight !== 100) {
            elements.hweightWarning.classList.remove('hidden');
        } else {
            elements.hweightWarning.classList.add('hidden');
        }
    }

    // Construct config payload from UI
    function buildConfigFromUI() {
        // Deep copy
        const config = JSON.parse(JSON.stringify(baseConfig));

        // Normalization fallback (if users submit when sums aren't 100, we'll let python handle it or they'll get weird scores)
        config.weights = {
            commute: parseInt(elements.weightCommute.value) / 100,
            housing: parseInt(elements.weightHousing.value) / 100,
            crime: parseInt(elements.weightCrime.value) / 100
        };

        if (!config.housing_preferences) config.housing_preferences = {};
        config.housing_preferences.housing_weights = {
            price: parseInt(elements.hweightPrice.value) / 100,
            ppsf: parseInt(elements.hweightPpsf.value) / 100,
            tax: parseInt(elements.hweightTax.value) / 100
        };

        if (!config.work_address_1) config.work_address_1 = { preferences: {} };
        config.work_address_1.preferences.ideal_time_mins = parseInt(elements.commuteIdeal.value);
        config.work_address_1.preferences.max_acceptable_time_mins = parseInt(elements.commuteMax.value);

        config.housing_preferences.budget_min = parseInt(elements.budgetMin.value) * 1000;
        config.housing_preferences.budget_ideal = parseInt(elements.budgetIdeal.value) * 1000;
        config.housing_preferences.budget_max = parseInt(elements.budgetMax.value) * 1000;

        return config;
    }

    // Fetch and render scores
    async function fetchScores() {
        elements.loader.classList.remove('hidden');
        elements.tableBody.innerHTML = '';
        
        const config = buildConfigFromUI();
        let groupingMode = 'zip';
        elements.groupingModes.forEach(radio => {
            if (radio.checked) groupingMode = radio.value;
        });

        try {
            const response = await fetch('/api/score', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    config: config,
                    grouping_mode: groupingMode
                })
            });
            const result = await response.json();
            
            if (result.error) {
                elements.tableBody.innerHTML = `<tr><td colspan="10" style="text-align:center;color:var(--danger)">${result.error}</td></tr>`;
                elements.resultCount.innerText = "Error";
                return;
            }

            renderTable(result.data || []);
        } catch (error) {
            console.error(error);
        } finally {
            elements.loader.classList.add('hidden');
        }
    }

    // Render table
    function renderTable(data) {
        elements.resultCount.innerText = `${data.length} Results`;
        
        if (data.length === 0) {
            elements.tableBody.innerHTML = `<tr><td colspan="10" style="text-align:center">No locations found. Adjust filters/budgets.</td></tr>`;
            return;
        }

        const html = data.map(row => {
            const tierLower = (row.Tier || 'F').charAt(0).toLowerCase();
            const priceStr = row.Median_Price ? `$${row.Median_Price.toLocaleString()}` : 'N/A';
            const timeStr = row.Avg_Commute_Min ? row.Avg_Commute_Min.toFixed(1) : 'N/A';
            
            return `
                <tr>
                    <td>#${row.Rank || '-'}</td>
                    <td><span class="tier-badge tier-${tierLower}">${row.Tier || '-'}</span></td>
                    <td>${row.Town || 'Unknown'}</td>
                    <td>${row.Zip || '-'}</td>
                    <td><strong>${row.Total_Score || 0}</strong></td>
                    <td>${row.Commute_Score || 0}</td>
                    <td>${row.Housing_Score || 0}</td>
                    <td>${row.Crime_Score || 0}</td>
                    <td>${priceStr}</td>
                    <td>${timeStr}</td>
                </tr>
            `;
        }).join('');

        elements.tableBody.innerHTML = html;
    }

    // Save Config
    async function saveConfig() {
        const config = buildConfigFromUI();
        const btn = elements.btnSave;
        const originalText = btn.innerText;
        btn.innerText = 'Saving...';

        try {
            await fetch('/api/config/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ config })
            });
            btn.style.background = 'var(--success)';
            btn.innerText = 'Saved!';
            setTimeout(() => {
                btn.style.background = 'var(--primary)';
                btn.innerText = originalText;
            }, 2000);
        } catch (e) {
            console.error(e);
            btn.style.background = 'var(--danger)';
            btn.innerText = 'Error!';
        }
    }

    // Event Listeners
    const allInputs = document.querySelectorAll('input[type=range], input[type=radio]');
    allInputs.forEach(input => {
        input.addEventListener('input', () => {
            updateLabels();
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(fetchScores, 500); // 500ms debounce
        });
    });

    elements.btnSave.addEventListener('click', saveConfig);

    // Boot
    init();
});
