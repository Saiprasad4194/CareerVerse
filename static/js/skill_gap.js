// =====================================
// AI Skill Gap Analyzer — Executive Dashboard Engine
// =====================================

const analyzeBtn = document.getElementById("analyzeBtn");

if (analyzeBtn) {
    analyzeBtn.onclick = async function () {
        const careerInput = document.getElementById("career");
        const skillsInput = document.getElementById("skills");
        const resultContainer = document.getElementById("result");

        const career = careerInput ? careerInput.value.trim() : "";
        const skills = skillsInput ? skillsInput.value.trim() : "";

        if (!career) {
            alert("Please enter your dream career role.");
            return;
        }

        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Analyzing Skill Gap...`;

        resultContainer.innerHTML = `
            <div class="loading-box">
                <h2>🤖 AI is analyzing your technical & domain skill gaps...</h2>
                <p>Comparing your skills against real-world industry benchmarks for ${career}...</p>
            </div>
        `;

        try {
            const response = await fetch("/skill-gap-api", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    career: career,
                    skills: skills
                })
            });

            const resData = await response.json();

            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = `<i class="fa-solid fa-chart-line"></i> Analyze Skill Gap Now`;

            if (resData.success === false) {
                resultContainer.innerHTML = `
                    <div class="error-card" style="border: 1px solid #ef4444; background: rgba(239, 68, 68, 0.08); padding: 26px; border-radius: 16px; margin-top: 20px; text-align: left;">
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                            <i class="fa-solid fa-circle-exclamation" style="font-size: 1.6rem; color: #ef4444;"></i>
                            <h3 style="color: var(--text-heading, #f4f4f5); margin: 0; font-size: 1.2rem;">Invalid Career Input</h3>
                        </div>
                        <p style="color: var(--text-primary, #e4e4e7); font-size: 0.96rem; line-height: 1.6; margin-bottom: 16px;">${resData.error || "Unable to analyze skills. Please enter a valid job role."}</p>
                        <div style="background: rgba(0,0,0,0.4); border: 1px solid var(--border, rgba(255,255,255,0.1)); padding: 12px 16px; border-radius: 10px; font-size: 0.86rem; color: var(--text-secondary, #a1a1aa);">
                            💡 <strong>Try Real Careers:</strong> <code>Software Engineer</code>, <code>Data Scientist</code>, <code>Doctor</code>, <code>Lawyer</code>, <code>Pilot</code>, <code>Chef</code>, <code>Civil Engineer</code>
                        </div>
                    </div>
                `;
                return;
            }

            const data = resData.data || resData;
            renderSkillGapDashboard(data, career, resultContainer);

        } catch (error) {
            console.error("Skill Gap Analysis Error:", error);
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = `<i class="fa-solid fa-chart-line"></i> Analyze Skill Gap Now`;

            resultContainer.innerHTML = `
                <div class="error-card" style="border: 1px solid #ef4444; background: rgba(239, 68, 68, 0.08); padding: 26px; border-radius: 16px; margin-top: 20px;">
                    <h3 style="color: #ef4444; margin: 0 0 8px 0;">❌ Skill Analysis Interrupted</h3>
                    <p style="color: var(--text-secondary, #a1a1aa); margin: 0;">Unable to connect to the analysis engine. Please try again.</p>
                </div>
            `;
        }
    };
}

function renderSkillGapDashboard(data, targetCareer, container) {
    const score = Number(data.skill_gap_score || 70);
    const demandMatch = Number(data.industry_demand_match || 85);
    const level = data.career_level || "Intermediate";
    const severity = data.gap_severity || "Medium Gap";
    const statusText = data.readiness_status || (score >= 70 ? "Target Ready" : "Up-skilling Needed");
    const recommendation = data.recommendation || "Focus on mastering key missing tools and building 2-3 real-world projects.";

    // Score Color Logic
    let scoreColor = "#facc15"; // Amber default
    let scoreClass = "amber";
    if (score >= 75) {
        scoreColor = "#22c55e"; // Emerald
        scoreClass = "emerald";
    } else if (score < 45) {
        scoreColor = "#ef4444"; // Crimson
        scoreClass = "crimson";
    }

    const skillAnalysis = Array.isArray(data.skill_analysis) ? data.skill_analysis : [
        { skill: "Core Domain Competency", score: 75 },
        { skill: "Specialized Tools & Frameworks", score: 50 },
        { skill: "Industry Protocols & Standards", score: 65 },
        { skill: "Practical Execution & Projects", score: 60 },
        { skill: "Communication & Problem Solving", score: 70 }
    ];

    const existingSkills = Array.isArray(data.existing_skills) && data.existing_skills.length ? data.existing_skills : [
        "Foundational domain knowledge & core concepts",
        "Basic tool & software operational familiarity",
        "Analytical reasoning & problem-solving ability",
        "Teamwork & collaborative communication",
        "High motivation for professional growth"
    ];

    const missingSkills = Array.isArray(data.missing_skills) && data.missing_skills.length ? data.missing_skills : [
        "Advanced specialized software & industry tools",
        "Production-grade compliance & safety protocols",
        "End-to-end practical project lifecycle execution",
        "Data-driven decision making & quantitative metrics",
        "Senior stakeholder communication & leadership"
    ];

    const prioritySkills = Array.isArray(data.priority_skills) && data.priority_skills.length ? data.priority_skills : [
        "1. Master core missing technical tools & frameworks",
        "2. Complete 2 real-world capstone projects or internships",
        "3. Acquire recognized industry professional certifications",
        "4. Build a public portfolio demonstrating practical execution",
        "5. Develop senior-level project management skills"
    ];

    const harshRealities = Array.isArray(data.harsh_realities) && data.harsh_realities.length ? data.harsh_realities : [
        "High competition for entry-level roles in this field",
        "Continuous lifelong upskilling is mandatory to stay relevant",
        "Early-career pay might be lower than industry averages",
        "Burnout and high stress are common during project crunches"
    ];

    container.innerHTML = `
        <div class="skill-dashboard">
            <!-- 1. Header Banner -->
            <div class="dashboard-header-card">
                <div class="header-title">
                    <h2>🧠 Skill Gap Report: ${targetCareer}</h2>
                    <p>Comprehensive competency evaluation against current global industry standards</p>
                </div>
                <div class="header-pills">
                    <span class="status-pill ${scoreClass}">
                        <i class="fa-solid fa-shield-halved"></i> ${statusText}
                    </span>
                </div>
            </div>

            <!-- 2. 4-Grid Executive Metrics -->
            <div class="metrics-4grid">
                <div class="metric-card">
                    <div class="icon-head"><i class="fa-solid fa-bullseye" style="color: var(--accent);"></i> Readiness Score</div>
                    <div class="big-val" style="color: ${scoreColor};">${score}%</div>
                    <div class="sub-label">Overall Match</div>
                </div>

                <div class="metric-card">
                    <div class="icon-head"><i class="fa-solid fa-fire" style="color: #f97316;"></i> Demand Match</div>
                    <div class="big-val" style="color: #f97316;">${demandMatch}%</div>
                    <div class="sub-label">Industry Relevancy</div>
                </div>

                <div class="metric-card">
                    <div class="icon-head"><i class="fa-solid fa-user-graduate" style="color: #3b82f6;"></i> Current Standing</div>
                    <div class="big-val" style="color: var(--text-heading, #f4f4f5); font-size: 1.5rem; margin-top: 6px;">${level}</div>
                    <div class="sub-label">Career Stage</div>
                </div>

                <div class="metric-card">
                    <div class="icon-head"><i class="fa-solid fa-triangle-exclamation" style="color: #eab308;"></i> Gap Severity</div>
                    <div class="big-val" style="color: #eab308; font-size: 1.4rem; margin-top: 6px;">${severity}</div>
                    <div class="sub-label">Upskilling Priority</div>
                </div>
            </div>

            <!-- 3. Skill Proficiency Matrix (Circular) -->
            <div class="proficiency-card">
                <h3><i class="fa-solid fa-chart-pie"></i> Competency Benchmark Matrix</h3>
                <div class="skill-circle-grid" style="display: flex; gap: 24px; flex-wrap: wrap; justify-content: center; margin-top: 24px;">
                    ${skillAnalysis.map(item => {
                        const skName = typeof item === 'object' ? (item.skill || item.name || "Competency") : item;
                        const skScore = typeof item === 'object' ? (item.score || 60) : 60;
                        const color = skScore >= 75 ? '#22c55e' : (skScore >= 45 ? '#facc15' : '#ef4444');
                        return `
                            <div class="skill-circle-item" style="display: flex; flex-direction: column; align-items: center; width: 150px; text-align: center;">
                                <div class="circle-progress" style="width: 90px; height: 90px; border-radius: 50%; background: conic-gradient(${color} ${skScore}%, var(--bg-primary) 0); display: flex; align-items: center; justify-content: center; margin-bottom: 14px; position: relative; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
                                    <div style="width: 74px; height: 74px; border-radius: 50%; background: var(--bg-card); display: flex; align-items: center; justify-content: center; font-weight: 800; color: var(--text-heading); font-size: 1.2rem;">
                                        ${skScore}%
                                    </div>
                                </div>
                                <span style="font-size: 0.9rem; color: var(--text-secondary); line-height: 1.35;">${skName}</span>
                            </div>
                        `;
                    }).join("")}
                </div>
            </div>

            <!-- 4. Two-Column Breakdown (Verified vs Missing) -->
            <div class="skills-two-col">
                <div class="verified-box">
                    <h3><i class="fa-solid fa-circle-check"></i> Acquired & Verified Competencies</h3>
                    <div class="skill-tags-list">
                        ${existingSkills.map(sk => `
                            <div class="skill-tag-item">
                                <i class="fa-solid fa-check"></i>
                                <span>${sk}</span>
                            </div>
                        `).join("")}
                    </div>
                </div>

                <div class="missing-box">
                    <h3><i class="fa-solid fa-triangle-exclamation"></i> Critical Missing Competencies</h3>
                    <div class="skill-tags-list">
                        ${missingSkills.map(sk => `
                            <div class="skill-tag-item">
                                <i class="fa-solid fa-xmark"></i>
                                <span>${sk}</span>
                            </div>
                        `).join("")}
                    </div>
                </div>
            </div>

            <!-- 4.1 Harsh Realities (Market Reality Check) -->
            <div class="reality-card" style="background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 16px; padding: 24px; margin-top: 24px;">
                <h3 style="color: #ef4444; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;"><i class="fa-solid fa-skull-crossbones"></i> Market Reality Check (Harsh Truths)</h3>
                <div class="skill-tags-list">
                    ${harshRealities.map(hr => `
                        <div class="skill-tag-item" style="background: rgba(239, 68, 68, 0.1); color: #fca5a5; border-color: rgba(239, 68, 68, 0.2);">
                            <i class="fa-solid fa-bolt"></i>
                            <span>${hr}</span>
                        </div>
                    `).join("")}
                </div>
            </div>

            <!-- 5. Priority Action Plan -->
            <div class="priority-card">
                <h3><i class="fa-solid fa-rocket"></i> Priority Action Roadmap (1-5 Execution)</h3>
                <div class="priority-steps-list">
                    ${prioritySkills.map((step, idx) => {
                        const cleanStep = typeof step === 'string' ? step.replace(/^\d+\.\s*/, '') : step;
                        return `
                            <div class="priority-step-item">
                                <div class="num-badge">${idx + 1}</div>
                                <span>${cleanStep}</span>
                            </div>
                        `;
                    }).join("")}
                </div>
            </div>

            <!-- 6. Strategic Recommendation -->
            <div class="recommendation-card">
                <h3><i class="fa-solid fa-lightbulb"></i> AI Executive Recommendation</h3>
                <p>${recommendation}</p>
            </div>
        </div>
    `;
}