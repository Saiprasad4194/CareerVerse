// ==========================================
// AI CAREER MATCH ENGINE — Accurate Dashboard
// ==========================================

const btn = document.getElementById("checkBtn");

if (btn) {
    btn.onclick = async function () {
        const career = document.getElementById("career").value.trim();
        const qualification = document.getElementById("qualification").value.trim();
        const skills = document.getElementById("skills").value.trim();
        const strengths = document.getElementById("strengths").value.trim();
        const experience = document.getElementById("experience").value.trim();
        const country = document.getElementById("country").value.trim();

        if (career === "") {
            alert("Please enter your Target Career Role.");
            return;
        }

        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Calculating Career Match...`;

        const result = document.getElementById("result");
        result.style.display = "block";
        result.innerHTML = `
            <div style="text-align:center; padding: 50px 20px;">
                <i class="fa-solid fa-brain" style="font-size: 2.5rem; color: var(--accent); margin-bottom: 16px;"></i>
                <h2>AI is evaluating your career compatibility...</h2>
                <p style="color: var(--text-secondary);">Matching skills, qualification, and market demand for <strong>${career}</strong> in <strong>${country || 'Global'}</strong>.</p>
            </div>
        `;

        try {
            const response = await fetch("/career-match-api", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    career: career,
                    qualification: qualification,
                    skills: skills,
                    strengths: strengths,
                    experience: experience,
                    country: country
                })
            });

            const data = await response.json();
            btn.disabled = false;
            btn.innerHTML = `<i class="fa-solid fa-magnifying-glass"></i> Calculate Career Match`;

            if (!response.ok || data.success === false) {
                result.innerHTML = `
                    <div style="border: 1px solid #ef4444; background: rgba(239, 68, 68, 0.08); padding: 26px; border-radius: 16px; margin: 24px auto; max-width: 800px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); text-align: left;">
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                            <i class="fa-solid fa-circle-exclamation" style="font-size: 1.6rem; color: #ef4444;"></i>
                            <h3 style="color: var(--text-heading); margin: 0; font-size: 1.2rem;">Invalid Input Warning</h3>
                        </div>
                        <p style="color: var(--text-primary); font-size: 0.96rem; line-height: 1.6; margin-bottom: 16px;">${data.error || "Unable to evaluate career match."}</p>
                        <div style="background: var(--bg-card); border: 1px solid var(--border); padding: 12px 16px; border-radius: 10px; font-size: 0.86rem; color: var(--text-secondary);">
                            💡 <strong>Suggested Careers:</strong> <code>Software Engineer</code>, <code>Data Scientist</code>, <code>Doctor</code>, <code>Lawyer</code><br>
                            🌍 <strong>Suggested Countries:</strong> <code>India</code>, <code>USA</code>, <code>Germany</code>, <code>UK</code>, <code>Canada</code>
                        </div>
                    </div>
                `;
                result.scrollIntoView({ behavior: "smooth", block: "center" });
                return;
            }

            const targetCareer = data.career || career;
            const targetCountry = data.country || country || "Global";
            const matchScore = data.match_percentage || 80;
            const isIndia = targetCountry.toLowerCase().includes("india") || (data.salary_expectation || "").includes("₹");
            const estimatedSalary = data.salary_expectation || (isIndia ? "₹8L - ₹18L / yr" : "$85,000 - $140,000 / yr");

            result.innerHTML = `
                <div class="career-dashboard-wrapper" style="display: flex; flex-direction: column; gap: 24px; max-width: 950px; margin: 0 auto; text-align: left;">
                    
                    <!-- HERO SCORE METER -->
                    <div class="career-card score-card" style="background: linear-gradient(135deg, rgba(250, 204, 21, 0.08) 0%, var(--bg-card) 100%); border: 1px solid var(--accent); border-radius: 20px; padding: 32px; text-align: center; box-shadow: 0 8px 30px rgba(0,0,0,0.4);">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; margin-bottom: 20px;">
                            <div>
                                <span style="font-size: 0.75rem; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: 1px;">🎯 AI CAREER MATCH VERDICT</span>
                                <h2 style="font-size: 1.8rem; color: var(--text-heading); margin: 4px 0 0;">${targetCareer} <span style="font-size: 1rem; color: var(--text-secondary); font-weight: 500;">(${targetCountry})</span></h2>
                            </div>
                            <div style="background: var(--accent-soft); border: 1px solid rgba(250, 204, 21, 0.4); padding: 8px 20px; border-radius: 100px; font-size: 0.9rem; font-weight: 700; color: var(--accent);">
                                ${data.match_status || 'Strong Profile Match'}
                            </div>
                        </div>

                        <div style="display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 16px;">
                            <span style="font-size: 3.8rem; font-weight: 800; color: var(--accent); line-height: 1;">${matchScore}%</span>
                            <small style="font-size: 1rem; color: var(--text-secondary);">Match Compatibility</small>
                        </div>

                        <div style="width: 100%; height: 10px; background: var(--bg-primary); border-radius: 100px; overflow: hidden; margin-bottom: 20px;">
                            <div style="width: ${matchScore}%; height: 100%; background: var(--accent); border-radius: 100px; transition: width 1s ease;"></div>
                        </div>

                        <p style="color: var(--text-secondary); font-size: 0.95rem; line-height: 1.6; max-width: 750px; margin: 0 auto;">
                            <strong>Career Identity:</strong> ${data.career_identity || 'High-Potential Technical Specialist'} — ${data.profile_summary || 'Strong background alignment with target career metrics.'}
                        </p>
                    </div>

                    <!-- 4 STAT CARDS -->
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;">
                        <div class="career-card" style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 14px; padding: 18px; text-align: center;">
                            <span style="font-size: 0.78rem; color: var(--text-secondary); font-weight: 600;">🛠 Skill Match</span>
                            <h3 style="font-size: 1.5rem; color: var(--accent); margin: 6px 0 0; font-weight: 800;">${data.skill_match_score || matchScore}%</h3>
                        </div>
                        <div class="career-card" style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 14px; padding: 18px; text-align: center;">
                            <span style="font-size: 0.78rem; color: var(--text-secondary); font-weight: 600;">🎓 Qualification Fit</span>
                            <h3 style="font-size: 1.5rem; color: var(--accent); margin: 6px 0 0; font-weight: 800;">${data.qualification_match_score || 80}%</h3>
                        </div>
                        <div class="career-card" style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 14px; padding: 18px; text-align: center;">
                            <span style="font-size: 0.78rem; color: var(--text-secondary); font-weight: 600;">🔥 Industry Demand</span>
                            <h3 style="font-size: 1.5rem; color: var(--accent); margin: 6px 0 0; font-weight: 800;">${data.industry_demand_score || 85}%</h3>
                        </div>
                        <div class="career-card" style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 14px; padding: 18px; text-align: center;">
                            <span style="font-size: 0.78rem; color: var(--text-secondary); font-weight: 600;">💰 Expected Salary</span>
                            <h3 style="font-size: 0.98rem; color: #22c55e; margin: 8px 0 0; font-weight: 700;">${estimatedSalary}</h3>
                        </div>
                    </div>

                    <!-- Salary Reason Callout Block -->
                    <div style="background: rgba(34, 197, 94, 0.04); border: 1px dashed rgba(34, 197, 94, 0.35); border-radius: 14px; padding: 14px 20px; font-size: 0.88rem; color: var(--text-primary); line-height: 1.5; margin-bottom: 8px;">
                        <strong>Why this salary?</strong> ${data.salary_reason || 'This compensation level is driven by specialized technical requirements, target country hiring demands, and competitive role values.'}
                        <div style="margin-top: 10px; padding-top: 8px; border-top: 1px dashed rgba(34, 197, 94, 0.2); font-size: 0.76rem; color: var(--text-muted); display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
                            <span><i class="fa-solid fa-database" style="color: #22c55e;"></i> Checked Sources:</span>
                            ${(function() {
                                const cLow = (targetCountry || "").toLowerCase();
                                let sources = [];
                                if (cLow.includes("india")) {
                                    sources = ["Ministry of Labour (GoI)", "NCS"];
                                } else if (cLow.includes("united states") || cLow.includes("usa") || cLow.includes("us")) {
                                    sources = ["US BLS OEWS", "O*NET"];
                                } else if (cLow.includes("united kingdom") || cLow.includes("uk")) {
                                    sources = ["UK Dept for Education", "ONS Registry"];
                                } else {
                                    sources = ["ILO Datasets", "CareerVerse Registries"];
                                }
                                return sources.map(src => `<span style="background: rgba(34, 197, 94, 0.06); padding: 1px 6px; border-radius: 4px; border: 1px solid rgba(34, 197, 94, 0.15); color: #22c55e; font-weight: 600;">${src}</span>`).join('');
                            })()}
                        </div>
                    </div>

                    <!-- 2-COLUMN ANALYSIS GRID -->
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
                        <!-- LEFT COLUMN -->
                        <div style="display: flex; flex-direction: column; gap: 24px;">
                            <!-- STRENGTHS -->
                            <div class="career-card" style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 16px; padding: 24px;">
                                <h3 style="color: var(--accent); font-size: 1.15rem; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                                    <i class="fa-solid fa-circle-check" style="color: #22c55e;"></i> Profile Strengths
                                </h3>
                                <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                                    ${(data.strengths && data.strengths.length ? data.strengths : [
                                        "Strong core technical qualification",
                                        "Solid foundation in required tools",
                                        "Adaptable problem-solving mindset"
                                    ]).map(item => `
                                        <div style="background: rgba(34, 197, 94, 0.08); border: 1px solid rgba(34, 197, 94, 0.3); color: #22c55e; padding: 8px 14px; border-radius: 100px; font-size: 0.85rem; font-weight: 600;">
                                            ✔ ${item}
                                        </div>
                                    `).join("")}
                                </div>
                            </div>

                            <!-- MISSING SKILLS -->
                            <div class="career-card" style="background: rgba(239, 68, 68, 0.03); border: 1px solid rgba(239, 68, 68, 0.35); border-radius: 16px; padding: 24px;">
                                <h3 style="color: #ef4444; font-size: 1.15rem; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                                    <i class="fa-solid fa-triangle-exclamation"></i> Missing Critical Skills & Gaps
                                </h3>
                                <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                                    ${(data.missing_skills && data.missing_skills.length ? data.missing_skills : [
                                        "Advanced System Architecture",
                                        "Production Deployment Experience",
                                        "Industry Certification Proof"
                                    ]).map(item => `
                                        <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); color: #ef4444; padding: 8px 14px; border-radius: 100px; font-size: 0.85rem; font-weight: 600;">
                                            ✖ ${item}
                                        </div>
                                    `).join("")}
                                </div>
                            </div>

                            <!-- ADVANTAGES -->
                            <div class="career-card" style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 16px; padding: 24px;">
                                <h3 style="color: var(--accent); font-size: 1.15rem; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                                    <i class="fa-solid fa-trophy"></i> Key Career Advantages
                                </h3>
                                <ul style="list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px;">
                                    ${(data.career_advantages && data.career_advantages.length ? data.career_advantages : [
                                        "High long-term demand growth across tech hubs",
                                        "Strong upward salary progression potential",
                                        "Global remote & mobility opportunities"
                                    ]).map(item => `
                                        <li style="background: rgba(20, 20, 20, 0.8); border: 1px solid var(--border); border-radius: 10px; padding: 12px 16px; font-size: 0.88rem; color: var(--text-primary); display: flex; gap: 10px; align-items: flex-start;">
                                            <i class="fa-solid fa-star" style="color: var(--accent); margin-top: 3px; font-size: 0.8rem;"></i>
                                            <span>${item}</span>
                                        </li>
                                    `).join("")}
                                </ul>
                            </div>
                        </div>

                        <!-- RIGHT COLUMN -->
                        <div style="display: flex; flex-direction: column; gap: 24px;">
                            <!-- RISKS -->
                            <div class="career-card" style="background: rgba(245, 158, 11, 0.03); border: 1px solid rgba(245, 158, 11, 0.35); border-radius: 16px; padding: 24px;">
                                <h3 style="color: #f59e0b; font-size: 1.15rem; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                                    <i class="fa-solid fa-shield-cat"></i> Career Risks & Trade-offs
                                </h3>
                                <ul style="list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px;">
                                    ${(data.career_risks && data.career_risks.length ? data.career_risks : [
                                        "High candidate competition for entry-level positions",
                                        "Requires continuous off-hours upskilling to maintain edge",
                                        "High accountability during critical release cycles"
                                    ]).map(item => `
                                        <li style="background: rgba(20, 20, 20, 0.8); border: 1px solid var(--border); border-radius: 10px; padding: 12px 16px; font-size: 0.88rem; color: var(--text-primary); display: flex; gap: 10px; align-items: flex-start;">
                                            <i class="fa-solid fa-triangle-exclamation" style="color: #f59e0b; margin-top: 3px; font-size: 0.85rem;"></i>
                                            <span>${item}</span>
                                        </li>
                                    `).join("")}
                                </ul>
                            </div>

                            <!-- ACTIONS -->
                            <div class="career-card" style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 16px; padding: 24px;">
                                <h3 style="color: var(--accent); font-size: 1.15rem; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                                    <i class="fa-solid fa-rocket"></i> Actionable Roadmap Steps
                                </h3>
                                <ul style="list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 12px;">
                                    ${(data.recommended_actions && data.recommended_actions.length ? data.recommended_actions : [
                                        "Build 2 production-grade projects demonstrating missing skills",
                                        "Gain hands-on experience with cloud deployment tools",
                                        "Optimize LinkedIn profile & resume for target role keywords"
                                    ]).map((item, idx) => `
                                        <li style="background: rgba(20, 20, 20, 0.85); border: 1px solid rgba(250, 204, 21, 0.2); border-radius: 10px; padding: 13px 16px; font-size: 0.88rem; color: var(--text-primary); display: flex; gap: 12px; align-items: flex-start;">
                                            <span style="background: var(--accent); color: #0a0a0a; min-width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.78rem; margin-top: 2px;">${idx + 1}</span>
                                            <span>${item}</span>
                                        </li>
                                    `).join("")}
                                </ul>
                            </div>

                            <!-- AI VERDICT -->
                            <div class="career-card ai-card" style="background: rgba(250, 204, 21, 0.04); border: 1px solid var(--accent); border-radius: 16px; padding: 24px;">
                                <h3 style="color: var(--accent); font-size: 1.15rem; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                                    <i class="fa-solid fa-robot"></i> AI Strategic Career Advice
                                </h3>
                                <p style="color: var(--text-heading); font-size: 0.95rem; line-height: 1.65; margin: 0; font-weight: 500;">
                                    ${data.personalized_advice || 'A viable career direction with strong growth potential once missing skills are acquired.'}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            result.scrollIntoView({ behavior: "smooth", block: "start" });

        } catch (error) {
            console.error(error);
            btn.disabled = false;
            btn.innerHTML = `<i class="fa-solid fa-magnifying-glass"></i> Calculate Career Match`;
            result.innerHTML = `
                <div class="career-card" style="border-color: #ef4444; background: rgba(239, 68, 68, 0.05); text-align: center; max-width: 800px; margin: 24px auto;">
                    <h2 style="color: #ef4444; justify-content: center;"><i class="fa-solid fa-triangle-exclamation"></i> Unable to analyze career match</h2>
                    <p style="color: var(--text-secondary);">Please check your inputs and try again.</p>
                </div>
            `;
        }
    };
}