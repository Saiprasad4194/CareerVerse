// ==========================================
// Cost of Living & PPP Calculator Script
// ==========================================

(function () {
    'use strict';

    const calculateBtn = document.getElementById("calculateBtn");
    const baseSalaryInput = document.getElementById("baseSalary");
    const baseCountrySelect = document.getElementById("baseCountry");
    const targetCountrySelect = document.getElementById("targetCountry");
    const careerInput = document.getElementById("career");
    const experienceSelect = document.getElementById("experience");
    const targetCityInput = document.getElementById("targetCity");
    
    const loading = document.getElementById("loading");
    const resultDashboard = document.getElementById("result");
    
    // Result displays
    const convertedSalaryDisplay = document.getElementById("convertedSalaryDisplay");
    const pppSalaryDisplay = document.getElementById("pppSalaryDisplay");
    const marketRangeDisplay = document.getElementById("marketRangeDisplay");
    const marketReasonDisplay = document.getElementById("marketReasonDisplay");
    const colComparisonTextDisplay = document.getElementById("colComparisonTextDisplay");
    
    // Bars
    const categories = ["Housing", "Food", "Transportation", "Utilities", "General"];
    
    // Recommendation & Insights
    const intelligentAnalysisDisplay = document.getElementById("intelligentAnalysisDisplay");
    const insightsList = document.getElementById("insightsList");

    // Initialize Page
    document.addEventListener("DOMContentLoaded", loadCountries);

    if (calculateBtn) {
        calculateBtn.addEventListener("click", calculatePPP);
    }

    async function loadCountries() {
        try {
            const response = await fetch("/static/data/countries_currency.json");
            const countriesData = await response.json();
            
            const sortedCountries = Object.keys(countriesData).sort();
            
            // Populate select inputs
            populateDropdown(baseCountrySelect, sortedCountries, "United States");
            populateDropdown(targetCountrySelect, sortedCountries, "India");
            
        } catch (error) {
            console.error("Failed to load country list:", error);
        }
    }

    function populateDropdown(selectElement, countriesList, defaultValue) {
        selectElement.innerHTML = "";
        countriesList.forEach(country => {
            const opt = document.createElement("option");
            opt.value = country;
            opt.textContent = country;
            if (country === defaultValue) {
                opt.selected = true;
            }
            selectElement.appendChild(opt);
        });
    }

    async function calculatePPP() {
        const baseSalary = baseSalaryInput.value.trim();
        const baseCountry = baseCountrySelect.value;
        const targetCountry = targetCountrySelect.value;
        const career = careerInput.value.trim();
        const experience = experienceSelect.value;
        const targetCity = targetCityInput.value.trim();

        // 1. Validation
        if (!baseSalary) {
            alert("Please enter your current base salary.");
            return;
        }

        const numericSalary = parseFloat(baseSalary.replace(/,/g, ''));
        if (isNaN(numericSalary) || numericSalary <= 0) {
            alert("Please enter a valid positive salary amount.");
            return;
        }

        if (!career) {
            alert("Please enter your career or job role.");
            return;
        }

        loading.classList.remove("hidden");
        resultDashboard.classList.add("hidden");
        calculateBtn.disabled = true;

        try {
            const response = await fetch("/col-calculator-api", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    base_salary: numericSalary,
                    base_country: baseCountry,
                    target_country: targetCountry,
                    career: career,
                    experience: experience,
                    target_city: targetCity
                })
            });

            const data = await response.json();
            calculateBtn.disabled = false;
            loading.classList.add("hidden");

            if (!response.ok || !data.success) {
                alert(data.error || "A calculation error occurred.");
                return;
            }

            // 2. Render Results dashboard
            resultDashboard.classList.remove("hidden");

            // A. Currency Conversion Card
            if (data.currency_conversion.converted_salary) {
                animateNumber(
                    convertedSalaryDisplay,
                    0,
                    data.currency_conversion.converted_salary,
                    1000,
                    data.target_currency_code,
                    data.target_currency_symbol
                );
            } else {
                convertedSalaryDisplay.textContent = "Unavailable";
            }

            // B. PPP Card
            if (data.ppp_comparison.ppp_available && data.ppp_comparison.ppp_salary) {
                animateNumber(
                    pppSalaryDisplay,
                    0,
                    data.ppp_comparison.ppp_salary,
                    1200,
                    data.target_currency_code,
                    data.target_currency_symbol
                );
            } else {
                pppSalaryDisplay.textContent = "Unavailable";
            }

            // C. Actual Market Salary Card
            if (data.market_salary.available) {
                marketRangeDisplay.textContent = `${data.market_salary.min_fmt} – ${data.market_salary.max_fmt}`;
                marketReasonDisplay.textContent = data.market_salary.reason;
            } else {
                marketRangeDisplay.textContent = "Unavailable";
                marketReasonDisplay.textContent = `No verified salary benchmarks found for ${career} in ${data.target_country}.`;
            }

            // D. Cost of Living Card & Category Bars
            colComparisonTextDisplay.textContent = data.cost_of_living.comparison_text;
            
            categories.forEach(cat => {
                const catData = data.cost_of_living.categories[cat];
                const badgeEl = document.getElementById(`${cat.toLowerCase()}DiffDisplay`);
                const fillEl = document.getElementById(`${cat.toLowerCase()}BarFill`);
                
                if (catData && badgeEl && fillEl) {
                    const diff = catData.diff;
                    const diffSign = diff >= 0 ? "+" : "";
                    badgeEl.textContent = `${diffSign}${diff.toFixed(1)}%`;
                    
                    // Style badge
                    if (diff >= 0) {
                        badgeEl.className = "diff-badge plus";
                        fillEl.className = "bar-fill red";
                    } else {
                        badgeEl.className = "diff-badge minus";
                        fillEl.className = "bar-fill green";
                    }
                    
                    // Fill Ratio
                    const fillRatio = Math.min(100, Math.max(5, (catData.target / (catData.base + catData.target)) * 100));
                    fillEl.style.width = `${fillRatio}%`;
                }
            });

            // E. Intelligent Relocation Summary & Insights
            intelligentAnalysisDisplay.textContent = data.intelligent_analysis;
            
            insightsList.innerHTML = "";
            (data.insights || []).forEach(tip => {
                const li = document.createElement("li");
                li.textContent = tip;
                insightsList.appendChild(li);
            });

            // Scroll to results beautifully
            resultDashboard.scrollIntoView({ behavior: 'smooth', block: 'start' });

        } catch (error) {
            console.error(error);
            calculateBtn.disabled = false;
            loading.classList.add("hidden");
            alert("A network error occurred. Please verify your connection.");
        }
    }

    function animateNumber(element, start, end, duration, code, symbol) {
        if (isNaN(end) || end <= 0) {
            element.textContent = "Unavailable";
            return;
        }
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const currentVal = Math.floor(progress * (end - start) + start);
            element.textContent = formatCurrency(currentVal, code, symbol);
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    function formatCurrency(val, code, symbol) {
        const rounded = Math.round(val);
        if (code === "INR") {
            if (rounded >= 100000) {
                return `${symbol}${(rounded / 100000).toFixed(2)} Lakhs / yr`;
            }
            return `${symbol}${rounded.toLocaleString('en-IN')} / yr`;
        }
        return `${symbol}${rounded.toLocaleString()} / yr`;
    }

})();
