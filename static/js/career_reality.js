// =====================================
// CAREER REALITY AI DASHBOARD ENGINE
// =====================================

document.addEventListener("DOMContentLoaded", () => {
    // Quick role selection
    document.querySelectorAll('.role-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            const input = document.getElementById('career');
            if (input) {
                input.value = pill.getAttribute('data-role');
                input.focus();
            }
        });
    });
});

const realityBtn = document.getElementById("realityBtn");

realityBtn.onclick = async function() {
    const careerInput = document.getElementById("career");
    const countryInput = document.getElementById("country");
    const result = document.getElementById("result");

    const career = careerInput.value.trim();
    const country = countryInput.value.trim();

    if (!career) {
        alert("Please enter a target career role.");
        return;
    }

    realityBtn.disabled = true;
    realityBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Uncovering Unfiltered Reality...`;

    result.innerHTML = `
        <div class="reality-card loading-card" style="text-align: center; padding: 50px 20px;">
            <div class="ai-loader" style="margin: 0 auto 20px;"></div>
            <h2>🤖 Uncovering Real-World Industry Truths...</h2>
            <p style="color: var(--text-secondary);">Analyzing workload stress, salary benchmarks, and daily responsibilities for <strong>${career}</strong>.</p>
        </div>
    `;
    result.scrollIntoView({ behavior: "smooth", block: "center" });

    try {
        const response = await fetch("/career-reality-api", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ career, country })
        });

        const data = await response.json();
        realityBtn.disabled = false;
        realityBtn.innerHTML = `<i class="fa-solid fa-masks-theater"></i> Reveal Unfiltered Career Reality`;

        if (!response.ok || data.success === false) {
            result.innerHTML = `
                <div style="border: 1px solid #ef4444; background: rgba(239, 68, 68, 0.08); padding: 26px; border-radius: 16px; margin: 24px auto; max-width: 900px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); text-align: left;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                        <i class="fa-solid fa-circle-exclamation" style="font-size: 1.6rem; color: #ef4444;"></i>
                        <h3 style="color: var(--text-heading); margin: 0; font-size: 1.2rem;">Invalid Input Warning</h3>
                    </div>
                    <p style="color: var(--text-primary); font-size: 0.96rem; line-height: 1.6; margin-bottom: 16px;">${data.error || "The entered career or country name is invalid or not recognized."}</p>
                    <div style="background: var(--bg-card); border: 1px solid var(--border); padding: 12px 16px; border-radius: 10px; font-size: 0.86rem; color: var(--text-secondary);">
                        💡 <strong>Suggested Careers:</strong> <code>Software Engineer</code>, <code>Data Scientist</code>, <code>Doctor</code>, <code>Lawyer</code><br>
                        🌍 <strong>Suggested Countries:</strong> <code>India</code>, <code>USA</code>, <code>Germany</code>, <code>UK</code>, <code>Canada</code>
                    </div>
                </div>
            `;
            result.scrollIntoView({ behavior: "smooth", block: "center" });
            return;
        }

        const cLow = (country || "").toLowerCase().trim();
        let countryFlag = "🌐";
        let countryName = country ? country.trim() : "Global";

        if (cLow.includes("india") || cLow.includes("bharat")) { countryFlag = "🇮🇳"; countryName = "India"; }
        else if (cLow.includes("usa") || cLow.includes("united states") || cLow.includes("us") || cLow.includes("america")) { countryFlag = "🇺🇸"; countryName = "USA"; }
        else if (cLow.includes("uk") || cLow.includes("united kingdom") || cLow.includes("england") || cLow.includes("scotland") || cLow.includes("wales") || cLow.includes("london") || cLow.includes("great britain")) { countryFlag = "🇬🇧"; countryName = "United Kingdom (England)"; }
        else if (cLow.includes("germany") || cLow.includes("deutschland")) { countryFlag = "🇩🇪"; countryName = "Germany"; }
        else if (cLow.includes("france")) { countryFlag = "🇫🇷"; countryName = "France"; }
        else if (cLow.includes("canada")) { countryFlag = "🇨🇦"; countryName = "Canada"; }
        else if (cLow.includes("australia")) { countryFlag = "🇦🇺"; countryName = "Australia"; }
        else if (cLow.includes("uae") || cLow.includes("dubai")) { countryFlag = "🇦🇪"; countryName = "UAE / Dubai"; }
        else if (cLow.includes("saudi") || cLow.includes("ksa")) { countryFlag = "🇸🇦"; countryName = "Saudi Arabia"; }
        else if (cLow.includes("singapore")) { countryFlag = "🇸🇬"; countryName = "Singapore"; }
        else if (cLow.includes("japan")) { countryFlag = "🇯🇵"; countryName = "Japan"; }
        else if (cLow.includes("korea")) { countryFlag = "🇰🇷"; countryName = "South Korea"; }
        else if (cLow.includes("switzerland")) { countryFlag = "🇨🇭"; countryName = "Switzerland"; }
        else if (cLow.includes("spain")) { countryFlag = "🇪🇸"; countryName = "Spain"; }
        else if (cLow.includes("italy")) { countryFlag = "🇮🇹"; countryName = "Italy"; }
        else if (cLow.includes("netherlands")) { countryFlag = "🇳🇱"; countryName = "Netherlands"; }

        const isIndia = cLow.includes("india") || (data.salary_reality || "").includes("₹");
        const fresherSal = data.fresher_salary && data.fresher_salary !== "--" ? data.fresher_salary : (isIndia ? "₹5.0L - ₹9.0L / yr" : "$65,000 - $90,000 / yr");
        const midSal = data.mid_salary && data.mid_salary !== "--" ? data.mid_salary : (isIndia ? "₹12.0L - ₹22.0L / yr" : "$110,000 - $155,000 / yr");
        const seniorSal = data.senior_salary && data.senior_salary !== "--" ? data.senior_salary : (isIndia ? "₹25.0L - ₹48.0L / yr" : "$165,000 - $250,000 / yr");

        const techDiff = data.technical_difficulty || 75;
        const compLvl = data.competition_level || 80;
        const learnDiff = data.learning_difficulty || 70;

        let html = `
            <div class="reality-dashboard-wrapper">
                <!-- HERO SCORE METER CARD -->
                <div class="reality-card reality-score-card" style="margin-bottom: 24px;">
                    <div class="score-header">
                        <div>
                            <span class="reality-badge-pill"><i class="fa-solid fa-gauge-high"></i> CAREER REALITY VERDICT</span>
                            <h2>${data.career || career} <span style="font-size: 0.95rem; color: var(--text-secondary); font-weight: 500;">(${countryName})</span></h2>
                            <p class="score-status-text">${data.reality_status || 'Realistic Industry Profile & Assessment'}</p>
                        </div>
                        <div class="score-circle-display">
                            <span class="score-number">${data.reality_score || 85}</span>
                            <small>/100</small>
                        </div>
                    </div>

                    <div class="reality-progress-bar">
                        <div class="reality-progress-fill" style="width: ${data.reality_score || 85}%;"></div>
                    </div>

                    <!-- 4 KEY METRICS -->
                    <div class="reality-metrics-grid">
                        <div class="metric-pill-box">
                            <span class="m-label"><i class="fa-solid fa-code"></i> Technical Difficulty</span>
                            <strong class="m-val">${techDiff} / 100</strong>
                        </div>
                        <div class="metric-pill-box">
                            <span class="m-label"><i class="fa-solid fa-fire"></i> Competition Level</span>
                            <strong class="m-val">${compLvl} / 100</strong>
                        </div>
                        <div class="metric-pill-box">
                            <span class="m-label"><i class="fa-solid fa-graduation-cap"></i> Learning Curve</span>
                            <strong class="m-val">${learnDiff} / 100</strong>
                        </div>
                        <div class="metric-pill-box">
                            <span class="m-label"><i class="fa-solid fa-heart-pulse"></i> Stress & Burnout Risk</span>
                            <strong class="m-val stress-val">${data.stress_level || 'Moderate to High Risk'}</strong>
                        </div>
                    </div>
                </div>

                <!-- UNFILTERED REALITY COMPARISON SPOTLIGHT CARD (STANDALONE BOX) -->
                <div class="reality-card" style="background: rgba(239, 68, 68, 0.04); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 16px; padding: 22px; margin-bottom: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.4);">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 12px;">
                        <i class="fa-solid fa-eye" style="font-size: 1.3rem; color: #ef4444;"></i>
                        <h2 style="margin: 0; font-size: 1.15rem; color: var(--text-heading);">The Proper Unfiltered Reality: Expectation vs. Ground Truth</h2>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1.2fr 1fr; gap: 16px;">
                        <div style="background: rgba(59, 130, 246, 0.06); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 14px; padding: 16px;">
                            <div style="font-size: 0.75rem; color: #3b82f6; font-weight: 800; text-transform: uppercase; margin-bottom: 6px;">💭 Social Expectation (The Myth)</div>
                            <p style="font-size: 0.85rem; color: var(--text-secondary); margin: 0; line-height: 1.5;">${(data.expectation_vs_reality?.expectation || "High starting income, minimal overtime, and immediate effortless career stability.")}</p>
                        </div>

                        <div style="background: rgba(239, 68, 68, 0.06); border: 1px solid rgba(239, 68, 68, 0.35); border-radius: 14px; padding: 16px;">
                            <div style="font-size: 0.75rem; color: #ef4444; font-weight: 800; text-transform: uppercase; margin-bottom: 6px;">🔥 Unfiltered Ground Reality (The Truth)</div>
                            <p style="font-size: 0.85rem; color: var(--text-heading); margin: 0; line-height: 1.5; font-weight: 500;">${(data.expectation_vs_reality?.unfiltered_reality || "Requires 3-5+ years of intense initial preparation, long working shifts, high stress resilience, and continuous skill updates to reach top-tier compensation.")}</p>
                        </div>

                        <div style="background: rgba(34, 197, 94, 0.06); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 14px; padding: 16px;">
                            <div style="font-size: 0.75rem; color: #22c55e; font-weight: 800; text-transform: uppercase; margin-bottom: 6px;">🎯 Key to Survival & Success</div>
                            <p style="font-size: 0.85rem; color: var(--text-secondary); margin: 0; line-height: 1.5;">${(data.expectation_vs_reality?.success_key || "Build verifiable proof of work, develop emotional stamina under pressure, and commit to 100% continuous upskilling.")}</p>
                        </div>
                    </div>
                </div>

                <!-- 2-COLUMN DASHBOARD -->
                <div class="reality-grid-2col">
                    <!-- LEFT COLUMN -->
                    <div class="reality-col">
                        <!-- DAY IN THE LIFE -->
                        <div class="reality-card">
                            <h2><i class="fa-solid fa-clock"></i> A Day In This Career</h2>
                            <ul class="reality-list icon-list">
                                ${(data.daily_work && data.daily_work.length ? data.daily_work : [
                                    "Executing core daily operational tasks and technical deliverables",
                                    "Aligning with cross-functional stakeholders and team leads",
                                    "Reviewing quality benchmarks and resolving complex bottlenecks",
                                    "Adapting to tight deadlines and real-time client requirements",
                                    "Engaging in continuous professional learning and skill upgrades"
                                ]).map(item => `
                                    <li><i class="fa-solid fa-circle-dot list-icon"></i> <span>${item}</span></li>
                                `).join("")}
                            </ul>
                        </div>

                        <!-- HIDDEN TRUTHS -->
                        <div class="reality-card warning-card">
                            <h2><i class="fa-solid fa-triangle-exclamation"></i> Hidden Truths & Hard Realities</h2>
                            <ul class="reality-list warning-list">
                                ${(data.hidden_truths && data.hidden_truths.length ? data.hidden_truths : [
                                    "Entry-level compensation requires proven hands-on portfolio proof",
                                    "Frequent overtime during critical product release and launch cycles",
                                    "Rapid technological changes require self-driven off-hours learning",
                                    "High accountability for system failures or missed milestones",
                                    "Promotion criteria heavily depend on measurable business impact"
                                ]).map(item => `
                                    <li><i class="fa-solid fa-triangle-exclamation list-icon-warn"></i> <span>${item}</span></li>
                                `).join("")}
                            </ul>
                        </div>

                        <!-- INDUSTRY REALITY -->
                        <div class="reality-card">
                            <h2><i class="fa-solid fa-building"></i> Industry Reality & Market Context</h2>
                            <p class="industry-text" style="color: var(--text-secondary); font-size: 0.95rem; line-height: 1.65; margin: 0;">${data.industry_reality || 'Steady industry demand with strong long-term growth opportunities for skilled professionals.'}</p>
                        </div>
                    </div>

                    <!-- RIGHT COLUMN -->
                    <div class="reality-col">
                        <!-- SALARY BREAKDOWN CARD (UPGRADED ACCURATE STACKED TIERS) -->
                        <div class="reality-card salary-reality-card" style="border: 1px solid rgba(250, 204, 21, 0.35);">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 10px;">
                                <span style="font-size: 0.98rem; font-weight: 800; color: var(--text-heading); display: flex; align-items: center; gap: 8px;">
                                    <span style="font-size: 1.2rem;">${countryFlag}</span> ${countryName} Earning Scope
                                </span>
                            </div>
                            <p class="salary-overview-text" style="color: var(--text-secondary); font-size: 0.86rem; margin-bottom: 16px; line-height: 1.4;">${data.salary_reality || `Realistic compensation progression for ${data.career || career} in ${countryName}.`}</p>
                            
                            <div style="display: flex; flex-direction: column; gap: 10px;">
                                <div style="background: rgba(34, 197, 94, 0.06); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 12px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <span style="font-size: 0.72rem; color: #22c55e; font-weight: 800; text-transform: uppercase;">🌱 Entry Level (0-2 Yrs)</span>
                                        <small style="display: block; font-size: 0.75rem; color: var(--text-secondary);">Junior / Resident / Intern</small>
                                    </div>
                                    <h4 style="color: #22c55e; font-size: 1.05rem; margin: 0; font-weight: 900;">${fresherSal}</h4>
                                </div>

                                <div style="background: rgba(250, 204, 21, 0.06); border: 1px solid rgba(250, 204, 21, 0.3); border-radius: 12px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <span style="font-size: 0.72rem; color: var(--accent); font-weight: 800; text-transform: uppercase;">⚡ Mid Level (3-6 Yrs)</span>
                                        <small style="display: block; font-size: 0.75rem; color: var(--text-secondary);">Experienced Practitioner</small>
                                    </div>
                                    <h4 style="color: var(--accent); font-size: 1.05rem; margin: 0; font-weight: 900;">${midSal}</h4>
                                </div>

                                <div style="background: rgba(168, 85, 247, 0.06); border: 1px solid rgba(168, 85, 247, 0.3); border-radius: 12px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <span style="font-size: 0.72rem; color: #a855f7; font-weight: 800; text-transform: uppercase;">🏆 Senior / Lead (7+ Yrs)</span>
                                        <small style="display: block; font-size: 0.75rem; color: var(--text-secondary);">Lead Consultant / Director</small>
                                    </div>
                                    <h4 style="color: #a855f7; font-size: 1.05rem; margin: 0; font-weight: 900;">${seniorSal}</h4>
                                </div>
                            </div>
                        </div>

                        <!-- WHO SHOULD AVOID THIS -->
                        <div class="reality-card danger-card">
                            <h2><i class="fa-solid fa-ban"></i> Who Should Avoid This Career?</h2>
                            <ul class="reality-list danger-list">
                                ${(data.not_for_you && data.not_for_you.length ? data.not_for_you : [
                                    "Individuals who prefer repetitive tasks without problem-solving",
                                    "Anyone uncomfortable with continuous learning and tech updates",
                                    "Professionals looking for low-stress jobs with no accountability"
                                ]).map(item => `
                                    <li><i class="fa-solid fa-circle-xmark list-icon-danger"></i> <span>${item}</span></li>
                                `).join("")}
                            </ul>
                        </div>

                        <!-- AI VERDICT -->
                        <div class="reality-card ai-verdict-card">
                            <h2><i class="fa-solid fa-robot"></i> AI Strategic Reality Verdict</h2>
                            <p class="verdict-text" style="color: var(--text-heading); font-size: 0.95rem; line-height: 1.65; margin: 0;">${data.ai_verdict || 'A highly rewarding career path for dedicated professionals willing to invest in continuous upskilling.'}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        result.innerHTML = html;
        result.scrollIntoView({ behavior: "smooth", block: "start" });

    } catch (error) {
        console.error(error);
        realityBtn.disabled = false;
        realityBtn.innerHTML = `<i class="fa-solid fa-masks-theater"></i> Reveal Unfiltered Career Reality`;
        result.innerHTML = `
            <div class="reality-card error-card">
                <h2>❌ Analysis Failed</h2>
                <p>Something went wrong during career reality synthesis. Please try again.</p>
            </div>
        `;
    }
};