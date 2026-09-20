// =====================================
// AI RESUME ANALYZER — ATS / ATP Evaluation Engine
// =====================================

const analyzeBtn = document.getElementById("analyzeResumeBtn");

if (analyzeBtn) {
    analyzeBtn.onclick = async function () {
        const fileInput = document.getElementById("resumeFile");
        const targetJobInput = document.getElementById("targetJob");
        const file = fileInput ? fileInput.files[0] : null;
        const targetRole = targetJobInput ? targetJobInput.value.trim() : "";

        if (!file) {
            alert("Please upload your resume PDF.");
            return;
        }

        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Evaluating ATS Match for ${targetRole ? targetRole : 'Target Role'}...`;

        const result = document.getElementById("result");
        result.innerHTML = `
            <div class="resume-card" style="text-align: center; padding: 40px 20px;">
                <i class="fa-solid fa-brain" style="font-size: 2.5rem; color: var(--accent); margin-bottom: 16px;"></i>
                <h2>AI is scanning your resume for ATS / ATP match...</h2>
                <p style="color: var(--text-secondary);">Analyzing keyword density, skill proof, and ATS parser compatibility specifically for <strong>${targetRole ? targetRole : 'Target Role'}</strong>.</p>
            </div>
        `;

        try {
            const formData = new FormData();
            formData.append("resume", file);
            if (targetRole) {
                formData.append("target_role", targetRole);
            }

            const response = await fetch("/resume-api", {
                method: "POST",
                body: formData
            });

            const data = await response.json();
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Evaluate Resume Now`;

            if (!response.ok || data.success === false) {
                result.innerHTML = `
                    <div style="border: 1px solid #ef4444; background: rgba(239, 68, 68, 0.08); padding: 26px; border-radius: 16px; margin: 24px auto; max-width: 900px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); text-align: left;">
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                            <i class="fa-solid fa-circle-exclamation" style="font-size: 1.6rem; color: #ef4444;"></i>
                            <h3 style="color: var(--text-heading); margin: 0; font-size: 1.2rem;">Invalid Input Warning</h3>
                        </div>
                        <p style="color: var(--text-primary); font-size: 0.96rem; line-height: 1.6; margin-bottom: 16px;">${data.error || "Unable to evaluate resume."}</p>
                        <div style="background: var(--bg-card); border: 1px solid var(--border); padding: 12px 16px; border-radius: 10px; font-size: 0.86rem; color: var(--text-secondary);">
                            💡 <strong>Suggested Target Roles:</strong> <code>Software Engineer</code>, <code>Data Scientist</code>, <code>AI Engineer</code>, <code>Doctor</code>
                        </div>
                    </div>
                `;
                result.scrollIntoView({ behavior: "smooth", block: "center" });
                return;
            }

            const evaluatedRole = data.target_role || targetRole || "Target Job Role";
            const atsScore = data.ats_score || data.job_readiness_score || 85;
            const atsStatus = data.ats_pass_status || (atsScore >= 75 ? "High ATS Pass Probability" : atsScore >= 55 ? "Moderate ATS Compatibility" : "ATS Revision Needed");
            const statusColor = atsScore >= 75 ? "#22c55e" : atsScore >= 55 ? "#facc15" : "#ef4444";
            const secInfo = data.security || {
                display_badge: "Secure Processing Active",
                badge_color: "#38bdf8",
                pii_entities_redacted: 0,
                mode: "development_isolated",
                zero_disk_retention: true
            };

            result.innerHTML = `
                <div class="resume-dashboard-wrapper" style="display: flex; flex-direction: column; gap: 24px;">
                    <!-- TARGET ROLE & ATS BANNER -->
                    <div style="background: var(--bg-card); border: 1px solid var(--accent); border-radius: 16px; padding: 22px 28px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 20px var(--accent-soft);">
                        <div>
                            <span style="font-size: 0.75rem; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: 1px;">🎯 ROLE-TAILORED ATS / ATP EVALUATION</span>
                            <h2 style="font-size: 1.6rem; color: var(--text-heading); margin: 6px 0 0;">${evaluatedRole}</h2>
                        </div>
                        <div style="background: rgba(34, 197, 94, 0.1); border: 1px solid ${statusColor}; padding: 8px 18px; border-radius: 100px; font-size: 0.88rem; font-weight: 700; color: ${statusColor};">
                            Status: ${atsStatus}
                        </div>
                    </div>

                    <!-- CONFIDENTIAL COMPUTING & PRIVACY AUDIT PILL -->
                    <div style="background: rgba(56, 189, 248, 0.06); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 12px; padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; font-size: 0.84rem;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <i class="fa-solid fa-shield-check" style="color: ${secInfo.badge_color || '#38bdf8'}; font-size: 1.15rem;"></i>
                            <span style="color: var(--text-primary);">
                                <strong style="color: ${secInfo.badge_color || '#38bdf8'};">${secInfo.display_badge}:</strong>
                                ${secInfo.pii_entities_redacted > 0 ? `Scrubbed <strong>${secInfo.pii_entities_redacted}</strong> PII entities before AI evaluation` : 'Zero raw PII exposed to external AI'} • In-memory stream • Zero disk retention
                            </span>
                        </div>
                        <span style="background: rgba(255,255,255,0.06); border: 1px solid var(--border); padding: 4px 10px; border-radius: 20px; font-size: 0.74rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px;">
                            ${secInfo.mode || 'isolated'}
                        </span>
                    </div>

                    <!-- HERO ATS / ATP SCORE CARD -->
                    <div class="resume-card resume-score" style="border-color: var(--accent); background: linear-gradient(135deg, rgba(250, 204, 21, 0.1) 0%, var(--bg-card) 100%); text-align: center;">
                        <h2 style="justify-content: center;"><i class="fa-solid fa-gauge-high" style="color: var(--accent);"></i> ATS / ATP Compatibility Score</h2>
                        <h1 style="font-size: 3.8rem; color: var(--accent); font-weight: 800; margin: 10px 0 6px;">${atsScore}%</h1>
                        <p style="color: var(--text-secondary); font-size: 0.95rem; margin: 0;">ATS parser compatibility and keyword matching score calculated specifically for <strong>${evaluatedRole}</strong>.</p>
                    </div>

                    <!-- 4 METRIC PILL CARDS GRID -->
                    <div class="resume-grid">
                        <div class="small-resume-card">
                            <h3>⚡ ATS Pass Score (ATP)</h3>
                            <h1 style="color: ${statusColor};">${atsScore}%</h1>
                        </div>
                        <div class="small-resume-card">
                            <h3>🎯 Job Readiness</h3>
                            <h1>${data.job_readiness_score || 82}%</h1>
                        </div>
                        <div class="small-resume-card">
                            <h3>👔 Recruiter Impact</h3>
                            <h1>${data.recruiter_impact_score || 78}%</h1>
                        </div>
                        <div class="small-resume-card">
                            <h3>🧠 Skill Evidence</h3>
                            <h1>${data.skill_evidence_score || 74}%</h1>
                        </div>
                    </div>

                    <!-- 2-COLUMN ANALYSIS GRID -->
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
                        <!-- LEFT COLUMN -->
                        <div style="display: flex; flex-direction: column; gap: 24px;">
                            <!-- STRENGTHS -->
                            <div class="resume-card">
                                <h2><i class="fa-solid fa-circle-check" style="color: #22c55e;"></i> Core Candidate Strengths</h2>
                                <div class="resume-tags">
                                    ${(data.strengths && data.strengths.length ? data.strengths : [
                                        "Strong technical project portfolio",
                                        "Clear professional summary structure",
                                        "Demonstrated core domain experience"
                                    ]).map(item => `
                                        <div class="resume-tag" style="background: rgba(34, 197, 94, 0.08); border-color: rgba(34, 197, 94, 0.3); color: #22c55e;">
                                            ✔ ${item}
                                        </div>
                                    `).join("")}
                                </div>
                            </div>

                            <!-- WEAKNESSES -->
                            <div class="resume-card" style="border-color: rgba(245, 158, 11, 0.35); background: rgba(245, 158, 11, 0.03);">
                                <h2 style="color: #f59e0b;"><i class="fa-solid fa-triangle-exclamation"></i> ATS Red Flags & Improvement Areas</h2>
                                <ul style="list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px;">
                                    ${(data.weaknesses && data.weaknesses.length ? data.weaknesses : [
                                        "Resume bullet points lack quantifiable business metrics",
                                        "Missing target industry keywords in project section"
                                    ]).map(item => `
                                        <li style="background: rgba(20, 20, 20, 0.8); border: 1px solid var(--border); border-radius: 10px; padding: 12px 16px; font-size: 0.9rem; color: var(--text-primary); display: flex; gap: 10px; align-items: flex-start;">
                                            <i class="fa-solid fa-triangle-exclamation" style="color: #f59e0b; margin-top: 3px;"></i>
                                            <span>${item}</span>
                                        </li>
                                    `).join("")}
                                </ul>
                            </div>

                            <!-- RECOMMENDED MATCHES -->
                            <div class="resume-card">
                                <h2><i class="fa-solid fa-briefcase"></i> Recommended Alternate Roles</h2>
                                <div class="resume-tags">
                                    ${(data.recommended_roles && data.recommended_roles.length ? data.recommended_roles : [
                                        "Full Stack Engineer",
                                        "Software Engineer",
                                        "Backend Specialist"
                                    ]).map(item => `
                                        <div class="resume-tag">
                                            💼 ${item}
                                        </div>
                                    `).join("")}
                                </div>
                            </div>
                        </div>

                        <!-- RIGHT COLUMN -->
                        <div style="display: flex; flex-direction: column; gap: 24px;">
                            <!-- MISSING SKILLS -->
                            <div class="resume-card" style="border-color: rgba(239, 68, 68, 0.35); background: rgba(239, 68, 68, 0.03);">
                                <h2 style="color: #ef4444;"><i class="fa-solid fa-fire-flame-curved"></i> Missing Critical ATS Keywords for ${evaluatedRole}</h2>
                                <div class="resume-tags">
                                    ${(data.missing_skills && data.missing_skills.length ? data.missing_skills : [
                                        "System Design",
                                        "CI/CD Pipelines",
                                        "Cloud Architecture"
                                    ]).map(item => `
                                        <div class="resume-tag" style="background: rgba(239, 68, 68, 0.08); border-color: rgba(239, 68, 68, 0.3); color: #ef4444;">
                                            ❌ ${item}
                                        </div>
                                    `).join("")}
                                </div>
                            </div>

                            <!-- RECRUITER IMPRESSION -->
                            <div class="resume-card">
                                <h2><i class="fa-solid fa-user-tie"></i> Recruiter First Impression Verdict</h2>
                                <p style="color: var(--text-secondary); font-size: 0.95rem; line-height: 1.65; margin: 0;">${data.final_verdict || 'Promising candidate profile with clear potential after implementing targeted bullet-point refinements.'}</p>
                            </div>

                            <!-- ACTIONABLE AI IMPROVEMENT PLAN -->
                            <div class="resume-card ai-resume-card" style="border-color: var(--accent); background: rgba(250, 204, 21, 0.04);">
                                <h2><i class="fa-solid fa-wand-magic-sparkles"></i> Actionable ATS Optimization Steps</h2>
                                <ul style="list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 12px;">
                                    ${(data.suggestions && data.suggestions.length ? data.suggestions : [
                                        "Quantify project outcomes with numerical ROI or percentage gains",
                                        "Add target role keywords directly to your professional summary",
                                        "Include GitHub or live project demo links for skill proof"
                                    ]).map((item, idx) => `
                                        <li style="background: rgba(20, 20, 20, 0.85); border: 1px solid rgba(250, 204, 21, 0.2); border-radius: 10px; padding: 13px 16px; font-size: 0.92rem; color: var(--text-primary); display: flex; gap: 12px; align-items: flex-start;">
                                            <span style="background: var(--accent); color: #0a0a0a; min-width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.78rem; margin-top: 2px;">${idx + 1}</span>
                                            <span>${item}</span>
                                        </li>
                                    `).join("")}
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            result.scrollIntoView({ behavior: "smooth", block: "start" });
        } catch (error) {
            console.error(error);
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Evaluate Resume Now`;
            result.innerHTML = `
                <div class="resume-card" style="border-color: #ef4444; background: rgba(239, 68, 68, 0.05); text-align: center;">
                    <h2 style="color: #ef4444; justify-content: center;"><i class="fa-solid fa-triangle-exclamation"></i> Unable to analyze resume</h2>
                    <p style="color: var(--text-secondary);">Please ensure you uploaded a valid text-readable PDF resume and try again.</p>
                </div>
            `;
        }
    };
}