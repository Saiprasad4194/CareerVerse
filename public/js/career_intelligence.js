// ==========================================
// Career Intelligence Dashboard
// ==========================================

const analyzeBtn = document.getElementById("analyzeBtn");
const careerInput = document.getElementById("career");
const countryInput = document.getElementById("country");
const dashboard = document.getElementById("dashboard");
const loading = document.getElementById("loading");

const futureRating = document.getElementById("futureRating");
const averageSalary = document.getElementById("averageSalary");
const confidence = document.getElementById("confidence");
const education = document.getElementById("education");
const overview = document.getElementById("overview");

if (analyzeBtn) {
    analyzeBtn.addEventListener("click", analyzeCareer);
}

async function analyzeCareer() {
    const career = careerInput.value.trim();
    const country = countryInput.value.trim() || "India";

    if (!career) {
        alert("Please enter a target career role.");
        return;
    }

    loading.classList.remove("hidden");
    dashboard.classList.add("hidden");

    try {
        const response = await fetch("/career-intelligence-api", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ career, country })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            loading.classList.add("hidden");
            dashboard.classList.add("hidden");

            let errorContainer = document.getElementById("intelError");
            if (!errorContainer) {
                errorContainer = document.createElement("div");
                errorContainer.id = "intelError";
                document.querySelector(".search-card").insertAdjacentElement("afterend", errorContainer);
            }
            errorContainer.innerHTML = `
                <div style="border: 1px solid #ef4444; background: rgba(239, 68, 68, 0.08); padding: 26px; border-radius: 16px; margin: 24px auto; max-width: 900px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); text-align: left;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                        <i class="fa-solid fa-circle-exclamation" style="font-size: 1.6rem; color: #ef4444;"></i>
                        <h3 style="color: var(--text-heading); margin: 0; font-size: 1.2rem;">Invalid Career Input Warning</h3>
                    </div>
                    <p style="color: var(--text-primary); font-size: 0.96rem; line-height: 1.6; margin-bottom: 16px;">${data.error || "The entered career name is invalid or not recognized."}</p>
                    <div style="background: var(--bg-card); border: 1px solid var(--border); padding: 12px 16px; border-radius: 10px; font-size: 0.86rem; color: var(--text-secondary);">
                        💡 <strong>Suggested Careers:</strong> <code>Software Engineer</code>, <code>Environmental Engineer</code>, <code>Data Scientist</code>, <code>Doctor</code>, <code>Lawyer</code>
                    </div>
                </div>
            `;
            errorContainer.classList.remove("hidden");
            errorContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return;
        }

        const errorContainer = document.getElementById("intelError");
        if (errorContainer) errorContainer.classList.add("hidden");

        loading.classList.add("hidden");
        dashboard.classList.remove("hidden");

        renderDashboard(data);

        // Smooth scroll to results
        dashboard.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
        loading.classList.add("hidden");
        dashboard.classList.add("hidden");
        let errorContainer = document.getElementById("intelError");
        if (!errorContainer) {
            errorContainer = document.createElement("div");
            errorContainer.id = "intelError";
            document.querySelector(".search-card").insertAdjacentElement("afterend", errorContainer);
        }
        errorContainer.innerHTML = `
            <div style="border: 1px solid #ef4444; background: rgba(239, 68, 68, 0.08); padding: 26px; border-radius: 16px; margin: 24px auto; max-width: 900px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); text-align: left;">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <i class="fa-solid fa-circle-exclamation" style="font-size: 1.6rem; color: #ef4444;"></i>
                    <h3 style="color: var(--text-heading); margin: 0; font-size: 1.2rem;">Invalid Career Input Warning</h3>
                </div>
                <p style="color: var(--text-primary); font-size: 0.96rem; line-height: 1.6; margin-bottom: 16px;">${error.message || "Invalid career input. Please enter a valid job title."}</p>
                <div style="background: var(--bg-card); border: 1px solid var(--border); padding: 12px 16px; border-radius: 10px; font-size: 0.86rem; color: var(--text-secondary);">
                    💡 <strong>Suggested Careers:</strong> <code>Software Engineer</code>, <code>Data Scientist</code>, <code>Doctor</code>, <code>Lawyer</code>
                </div>
            </div>
        `;
        errorContainer.classList.remove("hidden");
        errorContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function renderDashboard(data) {
    renderSummary(data);
    renderCharts(data);
    renderLists(data);
    renderTimeline(data);
    renderAdvice(data);
}

function renderSummary(data) {
    const summary = data.summary || {};
    window.lastSummaryData = summary;
    futureRating.textContent = summary.future_rating || "--";
    averageSalary.textContent = summary.average_salary || "--";
    confidence.textContent = summary.confidence || "--";
    education.textContent = summary.education || "--";
    overview.textContent = summary.overview || "No market overview available.";

    const fresherEl = document.getElementById("fresherSalary");
    const midEl = document.getElementById("midSalary");
    const seniorEl = document.getElementById("seniorSalary");

    const isIndia = (countryInput?.value || "India").toLowerCase().includes("india") || String(summary.average_salary || "").includes("₹");

    if (fresherEl) fresherEl.textContent = summary.fresher_salary && summary.fresher_salary !== "--" ? summary.fresher_salary : (isIndia ? "₹5L - ₹9L / yr" : "$65,000 - $90,000 / yr");
    if (midEl) midEl.textContent = summary.mid_salary && summary.mid_salary !== "--" ? summary.mid_salary : (isIndia ? "₹12L - ₹22L / yr" : "$110,000 - $155,000 / yr");
    if (seniorEl) seniorEl.textContent = summary.senior_salary && summary.senior_salary !== "--" ? summary.senior_salary : (isIndia ? "₹25L - ₹48L / yr" : "$165,000 - $250,000 / yr");
}

// Chart Instances
let demandChart = null;
let salaryChart = null;
let competitionChart = null;
let technologyChart = null;
let skillsChart = null;
let globalChart = null;

function destroyChart(chart) {
    if (chart) {
        chart.destroy();
    }
}

// 2. Salary Growth Chart (Emerald Green Bars with Actual Currency Values - NO Percentages)
function renderSalaryChart(chart) {
    destroyChart(salaryChart);
    const canvas = document.getElementById("salaryGrowthChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    const summary = window.lastSummaryData || {};
    const isIndia = (countryInput?.value || "India").toLowerCase().includes("india") || String(summary.average_salary || "").includes("₹");

    let rawVals = chart.values || [];
    let salaryValues = [];

    const parseSalaryNum = (val) => {
        if (val === null || val === undefined) return 0;
        const str = String(val);
        if (!str) return 0;
        const matches = str.match(/(\d+(\.\d+)?)/g);
        if (matches && matches.length > 0) {
            const nums = matches.map(Number);
            return (nums.reduce((a, b) => a + b, 0) / nums.length);
        }
        return 0;
    };

    const fresherVal = parseSalaryNum(summary.fresher_salary) || (isIndia ? 7 : 75);
    const midVal = parseSalaryNum(summary.mid_salary) || (isIndia ? 17 : 135);
    const seniorVal = parseSalaryNum(summary.senior_salary) || (isIndia ? 35 : 210);

    if (Array.isArray(rawVals) && rawVals.length === 7 && rawVals.some(v => v > 100)) {
        salaryValues = rawVals.map(v => isIndia ? (v > 1000 ? Math.round(v / 100000) : v) : (v > 1000 ? Math.round(v / 1000) : v));
    } else if (Array.isArray(rawVals) && rawVals.length === 7 && rawVals.some(v => v > 0 && v <= 100)) {
        salaryValues = [
            0,
            Math.round(fresherVal * 0.35 * 10) / 10,
            Math.round(fresherVal * 10) / 10,
            Math.round((fresherVal + (midVal - fresherVal) * 0.45) * 10) / 10,
            Math.round(midVal * 10) / 10,
            Math.round(seniorVal * 10) / 10,
            Math.round(seniorVal * 1.45 * 10) / 10
        ];
    } else {
        salaryValues = isIndia ? [0, 2.5, Math.round(fresherVal), 11, Math.round(midVal), Math.round(seniorVal), 48]
                               : [0, 25, Math.round(fresherVal), 105, Math.round(midVal), Math.round(seniorVal), 260];
    }

    salaryChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: chart.labels || ["Student", "Intern", "Entry", "Junior", "Mid", "Senior", "Expert"],
            datasets: [{
                label: isIndia ? "Salary (₹ Lakhs / yr)" : "Salary ($k / yr)",
                data: salaryValues,
                backgroundColor: (context) => {
                    const chartArea = context.chart.chartArea;
                    if (!chartArea) return "#10b981";
                    const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
                    gradient.addColorStop(0, "#10b981");
                    gradient.addColorStop(1, "rgba(16, 185, 129, 0.2)");
                    return gradient;
                },
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 1400,
                easing: "easeOutQuart"
            },
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    enabled: true,
                    backgroundColor: '#141414',
                    titleColor: '#ffffff',
                    bodyColor: '#10b981',
                    borderColor: 'rgba(16, 185, 129, 0.5)',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 10,
                    callbacks: {
                        label: function(context) {
                            const val = context.parsed.y;
                            return isIndia ? `Annual Pay: ₹${val} Lakhs / yr` : `Annual Pay: $${val}k / yr`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: "rgba(255, 255, 255, 0.04)", drawBorder: false },
                    ticks: { color: "#9ca3af", font: { size: 11, weight: '600' } }
                },
                y: {
                    grid: { color: "rgba(255, 255, 255, 0.04)", drawBorder: false },
                    ticks: {
                        color: "#10b981",
                        font: { size: 11, weight: '700' },
                        callback: function(value) {
                            return isIndia ? `₹${value}L` : `$${value}k`;
                        }
                    },
                    beginAtZero: true
                }
            }
        }
    });

    const reasonEl = document.getElementById("salaryReason");
    if (reasonEl) reasonEl.textContent = chart.reason || "Real compensation levels mapped across career experience tiers.";
}

// Standard Dark Theme Options for Cartesian Charts (Line & Bar)
// ==========================================
// Professional Dark Theme Chart.js Options
// ==========================================

const commonCartesianOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
        duration: 1400,
        easing: "easeOutQuart"
    },
    interaction: {
        mode: 'index',
        intersect: false
    },
    plugins: {
        legend: { display: false },
        tooltip: {
            enabled: true,
            backgroundColor: '#141414',
            titleColor: '#ffffff',
            bodyColor: '#e5e5e5',
            borderColor: 'rgba(250, 204, 21, 0.4)',
            borderWidth: 1,
            padding: 12,
            cornerRadius: 10,
            boxPadding: 6,
            titleFont: { size: 12, weight: '700' },
            bodyFont: { size: 12, weight: '600' }
        }
    },
    scales: {
        x: {
            grid: { color: "rgba(255, 255, 255, 0.04)", drawBorder: false },
            ticks: { color: "#9ca3af", font: { size: 11, weight: '600' }, padding: 8 }
        },
        y: {
            grid: { color: "rgba(255, 255, 255, 0.04)", drawBorder: false },
            ticks: { 
                color: "#9ca3af", 
                font: { size: 11, weight: '600' },
                padding: 8
            },
            suggestedMin: 0,
            suggestedMax: 100,
            beginAtZero: true
        }
    }
};

function sanitizeChartData(vals, defaultBase = 70) {
    if (!Array.isArray(vals) || vals.length === 0) {
        return [defaultBase - 15, defaultBase - 5, defaultBase, defaultBase + 8, defaultBase + 15];
    }
    return vals.map((v, i) => {
        let num = parseFloat(v);
        if (isNaN(num) || num === 0) {
            num = Math.min(95, Math.max(20, defaultBase + (i * 4)));
        }
        return Math.min(100, Math.max(5, Math.round(num)));
    });
}

function renderCharts(data) {
    const charts = data.charts || {};
    renderDemandChart(charts.career_demand || {});
    renderSalaryChart(charts.salary_growth || {});
    renderCompetitionChart(charts.competition || {});
    renderTechnologyChart(charts.technology || {});
    renderSkillsChart(charts.skills || {});
    renderGlobalChart(charts.global_demand || {});
    renderAutomation(charts.automation || {});
}

// 1. Demand Chart (Gold Gradient Line)
function renderDemandChart(chart) {
    destroyChart(demandChart);
    const canvas = document.getElementById("careerDemandChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    const cleanValues = sanitizeChartData(chart.values, 78);

    demandChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: chart.labels || ["2021", "2022", "2023", "2024", "2025", "2026", "2027"],
            datasets: [{
                label: "Hiring Demand Index",
                data: cleanValues,
                borderColor: "#facc15",
                borderWidth: 3,
                backgroundColor: (context) => {
                    const chartArea = context.chart.chartArea;
                    if (!chartArea) return "rgba(250, 204, 21, 0.1)";
                    const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
                    gradient.addColorStop(0, "rgba(250, 204, 21, 0.35)");
                    gradient.addColorStop(1, "rgba(250, 204, 21, 0.01)");
                    return gradient;
                },
                fill: true,
                tension: 0.42,
                pointBackgroundColor: "#facc15",
                pointBorderColor: "#0a0a0a",
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 8
            }]
        },
        options: commonCartesianOptions
    });

    const reasonEl = document.getElementById("careerDemandReason");
    if (reasonEl) reasonEl.textContent = chart.reason || "Strong multi-year hiring velocity driven by industry digital transformation.";
}

// 3. Competition Chart (Red Line)
function renderCompetitionChart(chart) {
    destroyChart(competitionChart);
    const canvas = document.getElementById("competitionChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    competitionChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: chart.labels || [],
            datasets: [{
                label: "Competition Index",
                data: chart.values || [],
                borderColor: "#f43f5e",
                borderWidth: 3,
                backgroundColor: "rgba(244, 63, 94, 0.15)",
                fill: true,
                tension: 0.4,
                pointBackgroundColor: "#f43f5e",
                pointBorderColor: "#0a0a0a",
                pointRadius: 4
            }]
        },
        options: commonCartesianOptions
    });

    const reasonEl = document.getElementById("competitionReason");
    if (reasonEl) reasonEl.textContent = chart.reason || "";
}

// 4. Technology Chart (Teal Line)
function renderTechnologyChart(chart) {
    destroyChart(technologyChart);
    const canvas = document.getElementById("technologyChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    technologyChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: chart.labels || [],
            datasets: [{
                label: "Tech Adoption %",
                data: chart.values || [],
                borderColor: "#06b6d4",
                borderWidth: 3,
                backgroundColor: "rgba(6, 182, 212, 0.15)",
                fill: true,
                tension: 0.4,
                pointBackgroundColor: "#06b6d4",
                pointBorderColor: "#0a0a0a",
                pointRadius: 4
            }]
        },
        options: commonCartesianOptions
    });

    const reasonEl = document.getElementById("technologyReason");
    if (reasonEl) reasonEl.textContent = chart.reason || "";
}

// 5. Skills Radar Chart
function renderSkillsChart(chart) {
    destroyChart(skillsChart);
    const canvas = document.getElementById("skillsChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    skillsChart = new Chart(ctx, {
        type: "radar",
        data: {
            labels: ["Technical", "Communication", "Leadership", "Management", "Problem Solving"],
            datasets: [{
                label: "Skill Weight",
                data: [
                    chart.technical || 70,
                    chart.communication || 60,
                    chart.leadership || 50,
                    chart.management || 55,
                    chart.problem_solving || 80
                ],
                backgroundColor: "rgba(250, 204, 21, 0.2)",
                borderColor: "#facc15",
                borderWidth: 2,
                pointBackgroundColor: "#facc15",
                pointBorderColor: "#0a0a0a",
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 1200 },
            plugins: {
                legend: { display: false },
                tooltip: {
                    enabled: true,
                    backgroundColor: '#141414',
                    titleColor: '#ffffff',
                    bodyColor: '#a3a3a3',
                    borderColor: '#facc15',
                    borderWidth: 1
                }
            },
            scales: {
                r: {
                    angleLines: { color: "rgba(255, 255, 255, 0.1)" },
                    grid: { color: "rgba(255, 255, 255, 0.08)" },
                    pointLabels: {
                        color: "#f5f5f5",
                        font: { size: 10, weight: "600" }
                    },
                    ticks: { display: false },
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            }
        }
    });

    const reasonEl = document.getElementById("skillsReason");
    if (reasonEl) reasonEl.textContent = chart.reason || "";
}

// 6. Global Demand Chart (Purple-to-Indigo Multi-Stop Linear Gradient Bars)
function renderGlobalChart(chart) {
    destroyChart(globalChart);
    const canvas = document.getElementById("globalDemandChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    const cleanValues = sanitizeChartData(chart.values, 85);
    const countries = chart.countries || chart.labels || ["USA", "Germany", "UK", "India", "Japan"];

    globalChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: countries,
            datasets: [{
                label: "Hiring Demand Index",
                data: cleanValues,
                backgroundColor: (context) => {
                    const chartArea = context.chart.chartArea;
                    if (!chartArea) return "#8b5cf6";
                    const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
                    gradient.addColorStop(0, "#a855f7");
                    gradient.addColorStop(1, "#6366f1");
                    return gradient;
                },
                borderRadius: 10,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 1400, easing: "easeOutQuart" },
            plugins: {
                legend: { display: false },
                tooltip: {
                    enabled: true,
                    backgroundColor: '#141414',
                    titleColor: '#ffffff',
                    bodyColor: '#a855f7',
                    borderColor: 'rgba(168, 85, 247, 0.4)',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 10,
                    callbacks: {
                        label: function(context) {
                            return `Hiring Score: ${context.parsed.y} / 100`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: "rgba(255, 255, 255, 0.04)", drawBorder: false },
                    ticks: { color: "#9ca3af", font: { size: 11, weight: '700' } }
                },
                y: {
                    grid: { color: "rgba(255, 255, 255, 0.04)", drawBorder: false },
                    ticks: { color: "#9ca3af", font: { size: 11, weight: '600' } },
                    suggestedMin: 0,
                    suggestedMax: 100,
                    beginAtZero: true
                }
            }
        }
    });

    const reasonEl = document.getElementById("globalReason");
    if (reasonEl) reasonEl.textContent = chart.reason || "High demand driven by global talent shortage and industry expansion.";
}

// 7. Automation Risk
function renderAutomation(chart) {
    const scoreEl = document.getElementById("automationScore");
    const reasonEl = document.getElementById("automationReason");
    if (scoreEl) scoreEl.textContent = chart.score ? `${chart.score}%` : "--";
    if (reasonEl) reasonEl.textContent = chart.reason || "";
}

// 8. Lists & Timeline
function renderLists(data) {
    populateList("topCompanies", data.top_companies || []);
    populateList("recommendedTools", data.recommended_tools || []);
    populateList("certifications", data.certifications || []);
    populateList("futureOpportunities", data.future_opportunities || []);
}

function populateList(id, items) {
    const ul = document.getElementById(id);
    if (!ul) return;
    ul.innerHTML = "";

    if (!items || !items.length) {
        ul.innerHTML = "<li>No data available</li>";
        return;
    }

    items.forEach(item => {
        const li = document.createElement("li");
        li.textContent = item;
        ul.appendChild(li);
    });
}

function renderTimeline(data) {
    const container = document.getElementById("careerPath");
    if (!container) return;
    container.innerHTML = "";

    const path = data.career_path || [];

    if (!path.length) {
        container.innerHTML = "<p style='color: var(--text-secondary); font-size: 0.95rem;'>No career path available.</p>";
        return;
    }

    const pathwayDiv = document.createElement("div");
    pathwayDiv.className = "pathway-container";

    path.forEach((step, index) => {
        const stepDiv = document.createElement("div");
        stepDiv.className = "pathway-step";
        stepDiv.innerHTML = `
            <div class="step-badge">${index + 1}</div>
            <div class="step-content">
                <span class="step-title">Stage ${index + 1} Pathway</span>
                <p class="step-desc">${step}</p>
            </div>
        `;
        pathwayDiv.appendChild(stepDiv);
    });

    container.appendChild(pathwayDiv);
}

function renderAdvice(data) {
    const adviceContainer = document.getElementById("aiAdvice");
    if (!adviceContainer) return;
    adviceContainer.innerHTML = "";

    const advice = data.ai_advice || [];

    if (!advice.length) {
        adviceContainer.innerHTML = "<div class='advice-card-item'><i class='fa-solid fa-lightbulb'></i> No specific advice available.</div>";
        return;
    }

    const adviceGrid = document.createElement("div");
    adviceGrid.className = "advice-grid";

    advice.forEach(item => {
        const div = document.createElement("div");
        div.className = "advice-card-item";
        div.innerHTML = `<i class="fa-solid fa-lightbulb"></i> <span>${item}</span>`;
        adviceGrid.appendChild(div);
    });

    adviceContainer.appendChild(adviceGrid);
}