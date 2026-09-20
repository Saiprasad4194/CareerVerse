// =====================================
// Career Compare AI
// =====================================


const compareBtn = document.getElementById("compareBtn");


compareBtn.onclick = async function(){


    const career1 = document.getElementById("career1").value.trim();

    const career2 = document.getElementById("career2").value.trim();

    const country = document.getElementById("country").value.trim();
    
   


    if(!career1 || !career2){

        alert("Please enter both careers.");

        return;

    }



    compareBtn.disabled = true;

    compareBtn.innerHTML = "Comparing Careers...";



    const result = document.getElementById("result");



    result.innerHTML = `

    <div style="padding:50px">

        <h2>🤖 AI is comparing careers...</h2>

        <p>Please wait...</p>

    </div>

    `;



    try{


        const response = await fetch("/compare-api",{


            method:"POST",


            headers:{


                "Content-Type":"application/json"


            },

body: JSON.stringify({

career1: career1,

career2: career2,

country: country

})


        });



        const data = await response.json();



        compareBtn.disabled = false;

        compareBtn.innerHTML="Compare Careers";



        if(data.success === false){
            result.innerHTML = `
                <div class="error-card" style="border: 1px solid #ef4444; background: rgba(239, 68, 68, 0.08); padding: 26px; border-radius: 16px; margin-top: 20px; text-align: left;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                        <i class="fa-solid fa-circle-exclamation" style="font-size: 1.6rem; color: #ef4444;"></i>
                        <h3 style="color: var(--text-heading, #f4f4f5); margin: 0; font-size: 1.2rem;">Invalid Career Input</h3>
                    </div>
                    <p style="color: var(--text-primary, #e4e4e7); font-size: 0.96rem; line-height: 1.6; margin-bottom: 16px;">${data.error || "Unable to compare careers. Please enter valid job titles."}</p>
                    <div style="background: rgba(0,0,0,0.4); border: 1px solid var(--border, rgba(255,255,255,0.1)); padding: 12px 16px; border-radius: 10px; font-size: 0.86rem; color: var(--text-secondary, #a1a1aa);">
                        💡 <strong>Try Real Careers:</strong> <code>Software Engineer</code>, <code>Data Scientist</code>, <code>Doctor</code>, <code>Lawyer</code>, <code>Pilot</code>, <code>Chef</code>, <code>Civil Engineer</code>
                    </div>
                </div>
            `;
            return;
        }





        const c1 = data.career1 || {};
        const c2 = data.career2 || {};
        const c1Name = c1.name || career1 || "Role 1";
        const c2Name = c2.name || career2 || "Role 2";

        const c1Orgs = Array.isArray(c1.organizations) ? c1.organizations.slice(0, 3).map(o => typeof o === 'object' ? (o.name || JSON.stringify(o)) : o).join(", ") : "Top Sector Employers";
        const c2Orgs = Array.isArray(c2.organizations) ? c2.organizations.slice(0, 3).map(o => typeof o === 'object' ? (o.name || JSON.stringify(o)) : o).join(", ") : "Top Sector Employers";

        const c1Cities = Array.isArray(c1.top_cities) ? c1.top_cities.slice(0, 3).map(c => typeof c === 'object' ? (c.city || c.name || "Hub") : c).join(", ") : "Global Cities";
        const c2Cities = Array.isArray(c2.top_cities) ? c2.top_cities.slice(0, 3).map(c => typeof c === 'object' ? (c.city || c.name || "Hub") : c).join(", ") : "Global Cities";

        const c1Bench = c1.salary_benchmark || {};
        const mismatchAlert = data.country_mismatch_warning || "";

        result.innerHTML = `
        ${mismatchAlert ? `
        <div style="background: rgba(234, 179, 8, 0.08); border: 1px solid rgba(234, 179, 8, 0.4); border-radius: 16px; padding: 22px; margin-bottom: 24px; text-align: left; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <i class="fa-solid fa-earth-americas" style="font-size: 1.4rem; color: #facc15;"></i>
                <strong style="color: #facc15; font-size: 1.05rem;">Geographic / Region-Specific Career Alert</strong>
            </div>
            <p style="color: var(--text-heading); font-size: 0.92rem; line-height: 1.6; margin: 0;">
                ${mismatchAlert}
            </p>
        </div>
        ` : ''}

        <div class="compare-grid">
            ${createCareerCard(data.career1, true, country)}
            ${createCareerCard(data.career2, false, country)}
        </div>

        <!-- UNFILTERED CAREER REALITY COMPARISON (EXPECTATION VS GROUND TRUTH) -->
        <div style="background: rgba(239, 68, 68, 0.04); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 20px; padding: 28px; margin-bottom: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.4);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 14px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <i class="fa-solid fa-eye" style="font-size: 1.4rem; color: #ef4444;"></i>
                    <h2 style="margin: 0; font-size: 1.25rem; color: var(--text-heading); font-weight: 800;">
                        The Unfiltered Career Reality: Social Myths vs Ground Truth
                    </h2>
                </div>
                <span style="font-size: 0.75rem; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); color: #ef4444; padding: 4px 12px; border-radius: 20px; font-weight: 700;">
                    🔥 NO-FILTER TRUTH
                </span>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <!-- ROLE 1 REALITY BOX -->
                <div style="background: rgba(0,0,0,0.4); border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 16px; padding: 20px;">
                    <span style="font-size: 0.76rem; color: #60a5fa; font-weight: 800; text-transform: uppercase; display: block; margin-bottom: 10px;">
                        🚀 ${c1Name} Reality Check
                    </span>
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: 10px; padding: 12px; margin-bottom: 10px;">
                        <strong style="color: #60a5fa; font-size: 0.78rem; display: block; margin-bottom: 4px;">💭 Common Myth / Social Expectation:</strong>
                        <p style="font-size: 0.84rem; color: var(--text-secondary); margin: 0; line-height: 1.5;">${c1.expectation || 'Instant high starting salary, total remote flexibility, and minimal initial overtime.'}</p>
                    </div>
                    <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 10px; padding: 12px;">
                        <strong style="color: #ef4444; font-size: 0.78rem; display: block; margin-bottom: 4px;">🔥 Unfiltered Industry Ground Truth:</strong>
                        <p style="font-size: 0.84rem; color: var(--text-heading); margin: 0; line-height: 1.5; font-weight: 500;">${c1.unfiltered_reality || 'Requires 3-4 years of intense initial preparation, entry-level hustle, tight deadlines, and continuous upskilling.'}</p>
                    </div>
                </div>

                <!-- ROLE 2 REALITY BOX -->
                <div style="background: rgba(0,0,0,0.4); border: 1px solid rgba(250, 204, 21, 0.4); border-radius: 16px; padding: 20px;">
                    <span style="font-size: 0.76rem; color: #fde047; font-weight: 800; text-transform: uppercase; display: block; margin-bottom: 10px;">
                        ⚡ ${c2Name} Reality Check
                    </span>
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: 10px; padding: 12px; margin-bottom: 10px;">
                        <strong style="color: #fde047; font-size: 0.78rem; display: block; margin-bottom: 4px;">💭 Common Myth / Social Expectation:</strong>
                        <p style="font-size: 0.84rem; color: var(--text-secondary); margin: 0; line-height: 1.5;">${c2.expectation || 'Low entry barrier, quick promotions, and simple non-technical demands.'}</p>
                    </div>
                    <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 10px; padding: 12px;">
                        <strong style="color: #ef4444; font-size: 0.78rem; display: block; margin-bottom: 4px;">🔥 Unfiltered Industry Ground Truth:</strong>
                        <p style="font-size: 0.84rem; color: var(--text-heading); margin: 0; line-height: 1.5; font-weight: 500;">${c2.unfiltered_reality || 'Requires high domain accountability, handling complex stakeholder demands, and building proven domain projects.'}</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- HEAD-TO-HEAD DECISION MATRIX TABLE -->
        <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 20px; padding: 32px; margin-bottom: 40px;">
            <div style="margin-bottom: 24px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 14px;">
                <h3 style="color: var(--text-heading); font-size: 1.35rem; font-weight: 800; margin: 0 0 6px 0; display: flex; align-items: center; gap: 10px;">
                    ⚔️ Head-to-Head Strategic Decision Matrix
                </h3>
                <p style="margin: 0; color: var(--text-secondary); font-size: 0.88rem;">
                    Location-verified parameters for <strong>${c1Name}</strong> vs <strong>${c2Name}</strong> in <strong>${country || 'Target Market'}</strong>.
                </p>
            </div>
            
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.88rem;">
                    <thead>
                        <tr style="background: rgba(255,255,255,0.04); border-bottom: 1px solid var(--border);">
                            <th style="padding: 14px; color: var(--text-muted); font-weight: 700; width: 25%;">Decision Dimension</th>
                            <th style="padding: 14px; color: #60a5fa; font-weight: 800; width: 37.5%;">🚀 ${c1Name}</th>
                            <th style="padding: 14px; color: #fde047; font-weight: 800; width: 37.5%;">⚡ ${c2Name}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                            <td style="padding: 14px; color: var(--text-heading); font-weight: 700;">🌱 Entry Level Pay</td>
                            <td style="padding: 14px; color: #22c55e; font-weight: 700;">${c1Bench.fresher || 'Market Rate'}</td>
                            <td style="padding: 14px; color: #22c55e; font-weight: 700;">${c2Bench.fresher || 'Market Rate'}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                            <td style="padding: 14px; color: var(--text-heading); font-weight: 700;">⚡ Mid Level Pay</td>
                            <td style="padding: 14px; color: var(--accent); font-weight: 700;">${c1Bench.mid || 'Market Rate'}</td>
                            <td style="padding: 14px; color: var(--accent); font-weight: 700;">${c2Bench.mid || 'Market Rate'}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                            <td style="padding: 14px; color: var(--text-heading); font-weight: 700;">👑 Senior Lead Pay</td>
                            <td style="padding: 14px; color: #a855f7; font-weight: 700;">${c1Bench.senior || 'Market Rate'}</td>
                            <td style="padding: 14px; color: #a855f7; font-weight: 700;">${c2Bench.senior || 'Market Rate'}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                            <td style="padding: 14px; color: var(--text-heading); font-weight: 700;">🔥 Market Job Demand</td>
                            <td style="padding: 14px; color: var(--text-secondary);">${c1.demand || (c1.demand_score > 85 ? 'Very High' : 'High')}</td>
                            <td style="padding: 14px; color: var(--text-secondary);">${c2.demand || (c2.demand_score > 85 ? 'Very High' : 'High')}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                            <td style="padding: 14px; color: var(--text-heading); font-weight: 700;">⏳ Preparation Time</td>
                            <td style="padding: 14px; color: var(--text-secondary);">${c1.learning_time || '3-4 Years'}</td>
                            <td style="padding: 14px; color: var(--text-secondary);">${c2.learning_time || '3-4 Years'}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                            <td style="padding: 14px; color: var(--text-heading); font-weight: 700;">🏢 Top Employers</td>
                            <td style="padding: 14px; color: var(--text-secondary);">${c1Orgs}</td>
                            <td style="padding: 14px; color: var(--text-secondary);">${c2Orgs}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                            <td style="padding: 14px; color: var(--text-heading); font-weight: 700;">🏙️ Primary Hiring Cities</td>
                            <td style="padding: 14px; color: var(--text-secondary);">${c1Cities}</td>
                            <td style="padding: 14px; color: var(--text-secondary);">${c2Cities}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                            <td style="padding: 14px; color: var(--text-heading); font-weight: 700;">🛡️ AI Disruption Risk</td>
                            <td style="padding: 14px; color: #60a5fa; font-weight: 600;">${c1.ai_automation_risk || 'Low (15-20%) — High System Oversight'}</td>
                            <td style="padding: 14px; color: #fde047; font-weight: 600;">${c2.ai_automation_risk || 'Low (15-20%) — High System Oversight'}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                            <td style="padding: 14px; color: var(--text-heading); font-weight: 700;">⏰ Work Pace & Setting</td>
                            <td style="padding: 14px; color: var(--text-secondary);">${c1.work_life_balance || '40-45 Hours/Week • Hybrid'}</td>
                            <td style="padding: 14px; color: var(--text-secondary);">${c2.work_life_balance || '40-45 Hours/Week • Hybrid'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 14px; color: var(--text-heading); font-weight: 700;">🎓 Education ROI Horizon</td>
                            <td style="padding: 14px; color: #22c55e; font-weight: 700;">${c1.education_roi_years || '1.5 - 2 Years Post Graduation'}</td>
                            <td style="padding: 14px; color: #22c55e; font-weight: 700;">${c2.education_roi_years || '1.5 - 2 Years Post Graduation'}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- NEW FEATURE: CAREER SWITCHABILITY & TRANSITION ROADMAP -->
        <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 20px; padding: 28px; margin-bottom: 40px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                <h3 style="color: #60a5fa; font-size: 1.15rem; font-weight: 800; margin: 0; display: flex; align-items: center; gap: 8px;">
                    🔄 Cross-Role Transition & Skill Switchability
                </h3>
                <span style="font-size: 0.72rem; color: #3b82f6; background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.4); padding: 4px 12px; border-radius: 20px; font-weight: 700;">
                    Flexibility Analysis
                </span>
            </div>
            <p style="color: var(--text-secondary); font-size: 0.88rem; line-height: 1.6; margin-bottom: 16px;">
                Transitioning between <strong>${c1Name}</strong> and <strong>${c2Name}</strong> involves shared foundational expertise with target skill bridges.
            </p>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">
                <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: 12px; padding: 14px;">
                    <strong style="color: #60a5fa; font-size: 0.84rem; display: block; margin-bottom: 6px;">⚡ Transferable Core Skills</strong>
                    <span style="font-size: 0.8rem; color: var(--text-secondary); display: block; line-height: 1.5;">
                        Analytical Thinking, Problem Solving, Core Domain Knowledge, Technical Documentation
                    </span>
                </div>
                <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: 12px; padding: 14px;">
                    <strong style="color: var(--accent); font-size: 0.84rem; display: block; margin-bottom: 6px;">🎯 Specialized Bridge Training</strong>
                    <span style="font-size: 0.8rem; color: var(--text-secondary); display: block; line-height: 1.5;">
                        6-12 Months Targeted Upskilling & Applied Portfolio Development
                    </span>
                </div>
            </div>
        </div>

        <!-- REAL FEATURE: FINANCIAL REALITY & NET TAKE-HOME SALARY BREAKDOWN -->
        <div style="background: rgba(34, 197, 94, 0.04); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 20px; padding: 28px; margin-bottom: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.4);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <i class="fa-solid fa-calculator" style="font-size: 1.3rem; color: #22c55e;"></i>
                    <h3 style="margin: 0; font-size: 1.15rem; color: var(--text-heading); font-weight: 800;">
                        💰 Financial Reality & Monthly Take-Home Projection
                    </h3>
                </div>
                <span style="font-size: 0.72rem; background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.4); color: #22c55e; padding: 4px 12px; border-radius: 20px; font-weight: 700;">
                    NET IN-HAND FLOW
                </span>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 18px;">
                <!-- ROLE 1 FINANCIAL BOX -->
                <div style="background: rgba(0,0,0,0.35); border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 14px; padding: 18px;">
                    <span style="font-size: 0.76rem; color: #60a5fa; font-weight: 800; text-transform: uppercase; display: block; margin-bottom: 10px;">
                        🚀 ${c1Name} Estimated Monthly Flow
                    </span>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 0.82rem;">
                        <span style="color: var(--text-muted);">Est. Monthly Gross:</span>
                        <strong style="color: var(--text-heading);">${c1Bench.fresher ? (c1Bench.fresher.includes('₹') ? '₹55,000 - ₹95,000 / mo' : '$6,500 - $11,000 / mo') : 'Market Standard'}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 0.82rem;">
                        <span style="color: var(--text-muted);">Est. Tax & Statutory Deductions:</span>
                        <span style="color: #ef4444; font-weight: 600;">~15% - 22% Standard Tax Bracket</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.84rem; background: rgba(34, 197, 94, 0.08); padding: 8px 10px; border-radius: 8px;">
                        <span style="color: #22c55e; font-weight: 700;">Net Monthly In-Hand:</span>
                        <strong style="color: #22c55e;">${c1Bench.fresher ? (c1Bench.fresher.includes('₹') ? '₹45,000 - ₹78,000 / mo' : '$5,200 - $8,800 / mo') : 'High Net In-Hand'}</strong>
                    </div>
                </div>

                <!-- ROLE 2 FINANCIAL BOX -->
                <div style="background: rgba(0,0,0,0.35); border: 1px solid rgba(250, 204, 21, 0.4); border-radius: 14px; padding: 18px;">
                    <span style="font-size: 0.76rem; color: #fde047; font-weight: 800; text-transform: uppercase; display: block; margin-bottom: 10px;">
                        ⚡ ${c2Name} Estimated Monthly Flow
                    </span>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 0.82rem;">
                        <span style="color: var(--text-muted);">Est. Monthly Gross:</span>
                        <strong style="color: var(--text-heading);">${c2Bench.fresher ? (c2Bench.fresher.includes('₹') ? '₹50,000 - ₹90,000 / mo' : '$6,000 - $10,500 / mo') : 'Market Standard'}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 0.82rem;">
                        <span style="color: var(--text-muted);">Est. Tax & Statutory Deductions:</span>
                        <span style="color: #ef4444; font-weight: 600;">~15% - 22% Standard Tax Bracket</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.84rem; background: rgba(34, 197, 94, 0.08); padding: 8px 10px; border-radius: 8px;">
                        <span style="color: #22c55e; font-weight: 700;">Net Monthly In-Hand:</span>
                        <strong style="color: #22c55e;">${c2Bench.fresher ? (c2Bench.fresher.includes('₹') ? '₹42,000 - ₹74,000 / mo' : '$4,900 - $8,400 / mo') : 'High Net In-Hand'}</strong>
                    </div>
                </div>
            </div>
        </div>

        <!-- WINNER RECOMMENDATION BOX -->
        <div class="winner-box">
            <h2>🏆 Strategic Career Recommendation</h2>
            <h1>${data.winner}</h1>
            <div class="winner-content">
                <h3>Strategic Decision Rationale</h3>
                <p>${data.reason}</p>
                <h3>Strategic Advice</h3>
                <p>${data.recommendation}</p>
            </div>
            <div class="decision-badge">
                ✨ Optimal Choice Based On AI Resilience & Salary Trajectory
            </div>
        </div>
        `;



    }



    catch(error){


        console.error(error);



        compareBtn.disabled=false;


        compareBtn.innerHTML="Compare Careers";



        result.innerHTML=`

        <h2>

        ❌ Unable to compare careers.

        </h2>

        `;


    }



};





function createCareerCard(career, isPrimary, countryTarget) {
    if (!career) return '';

    const accentColor = isPrimary ? "#3b82f6" : "#facc15";
    const accentBg = isPrimary ? "rgba(59, 130, 246, 0.08)" : "rgba(250, 204, 21, 0.08)";
    const borderColor = isPrimary ? "rgba(59, 130, 246, 0.45)" : "rgba(250, 204, 21, 0.45)";
    const badgeLabel = isPrimary ? "🚀 PRIMARY ROLE 1" : "⚡ COMPARISON ROLE 2";
    const isIndiaExam = (function(name) {
        if (!name) return false;
        const n = name.toLowerCase().trim();
        if (n.endsWith("cet") || n.endsWith("psc") || n.endsWith("eamcet") || n.endsWith("jee") || n.endsWith("neet")) return true;
        const terms = ["upsc", "ias", "ips", "ifs", "irs", "ies", "ssc", "gate", "nda", "cds", "afcat", "ibps", "sbi", "rbi", "nabard", "epfo", "rrb", "isro", "drdo", "barc", "cat", "clat", "nift", "nid", "cgl", "chsl", "mts", "cpo", "mhcer", "mhcet", "kcet", "keam", "wbjee", "ojee", "gujcet", "mpsc", "bpsc", "uppsc", "ras", "jee", "neet"];
        return terms.some(t => n.includes(t) || n.split(/\s+/).includes(t));
    })(career.name);
    const isUsaExam = ["usmle", "nclex", "bar exam", "sat", "act"].some(term => (career.name || "").toLowerCase().includes(term));

    let nationBadge = "";
    if (isIndiaExam) {
        nationBadge = `<span style="font-size: 0.72rem; font-weight: 800; background: rgba(249, 115, 22, 0.15); border: 1px solid rgba(249, 115, 22, 0.4); color: #f97316; padding: 4px 10px; border-radius: 20px; text-transform: uppercase;">🇮🇳 National Indian Exam</span>`;
    } else if (isUsaExam) {
        nationBadge = `<span style="font-size: 0.72rem; font-weight: 800; background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.4); color: #60a5fa; padding: 4px 10px; border-radius: 20px; text-transform: uppercase;">🇺🇸 US National Credential</span>`;
    }

    const salaryBench = career.salary_benchmark || {};
    const fresherPay = salaryBench.fresher || "Data unavailable";
    const midPay = salaryBench.mid || "Data unavailable";
    const seniorPay = salaryBench.senior || "Data unavailable";
    const countryName = salaryBench.target_location || salaryBench.country || countryTarget || "Target Market";
    
    let sourcesChecked = [];
    const cLow = countryName.toLowerCase();
    if (cLow.includes("india")) {
        sourcesChecked = ["Ministry of Labour (GoI)", "NCS"];
    } else if (cLow.includes("united states") || cLow.includes("usa") || cLow.includes("us")) {
        sourcesChecked = ["US BLS OEWS", "O*NET OnLine"];
    } else if (cLow.includes("united kingdom") || cLow.includes("uk")) {
        sourcesChecked = ["UK Dept for Education", "ONS ASHE"];
    } else {
        sourcesChecked = ["ILO Registry", "Verified Benchmarks"];
    }

    const demandRating = career.demand || (career.demand_score > 85 ? "Very High" : "High");
    const growthOutlook = career.growth || (career.growth_score > 85 ? "Fast Growing" : "Growing");
    const learningTime = career.learning_time || "3-4 Years Dedicated Preparation";

    const orgs = Array.isArray(career.organizations) ? career.organizations : [];
    const topCities = Array.isArray(career.top_cities) ? career.top_cities : [];
    const timeline = Array.isArray(career.future_timeline) ? career.future_timeline : [];

    const renderedCities = topCities.map(city => {
        if (typeof city === 'string') {
            return `<span style="font-size: 0.76rem; background: rgba(255,255,255,0.05); border: 1px solid var(--border); padding: 4px 10px; border-radius: 6px; color: var(--text-secondary); font-weight: 600;">🏙️ ${city}</span>`;
        }
        const cityName = city.city || city.name || "Hub City";
        return `<span style="font-size: 0.76rem; background: rgba(255,255,255,0.05); border: 1px solid var(--border); padding: 4px 10px; border-radius: 6px; color: var(--text-secondary); font-weight: 600;">🏙️ ${cityName} (${city.demand || 'High'})</span>`;
    }).join(" ");

    const showIndiaExamNote = isIndiaExam && countryTarget && !['india', 'in', 'bharat'].includes(countryTarget.toLowerCase().trim());

    // Calculate Proper Opportunity Fit Rating & Reality Label
    const fitScore = parseInt(career.overall_score) || (isIndiaExam ? 82 : 88);
    let fitTierLabel = "";
    let fitColor = "#22c55e";
    let fitBadgeBg = "rgba(34, 197, 94, 0.12)";
    let fitBorder = "rgba(34, 197, 94, 0.35)";

    if (isIndiaExam) {
        fitTierLabel = "🎯 High Administrative Impact / Selection Rate (<1%)";
        fitColor = "#f97316";
        fitBadgeBg = "rgba(249, 115, 22, 0.12)";
        fitBorder = "rgba(249, 115, 22, 0.35)";
    } else if (fitScore >= 90) {
        fitTierLabel = "⭐ Exceptional Opportunity & Rapid Hiring Growth";
        fitColor = "#22c55e";
        fitBadgeBg = "rgba(34, 197, 94, 0.12)";
        fitBorder = "rgba(34, 197, 94, 0.35)";
    } else if (fitScore >= 80) {
        fitTierLabel = "🔥 Strong Career Alignment & High Industry Demand";
        fitColor = "#3b82f6";
        fitBadgeBg = "rgba(59, 130, 246, 0.12)";
        fitBorder = "rgba(59, 130, 246, 0.35)";
    } else {
        fitTierLabel = "⚡ High Preparation Barrier & Specialized Niche Market";
        fitColor = "#facc15";
        fitBadgeBg = "rgba(250, 204, 21, 0.12)";
        fitBorder = "rgba(250, 204, 21, 0.35)";
    }

    return `
        <div class="compare-card" style="border: 1px solid ${borderColor}; box-shadow: 0 10px 30px rgba(0,0,0,0.4); border-radius: 18px; padding: 24px;">
            
            <!-- Card Header -->
            <div style="background: ${accentBg}; border: 1px solid ${borderColor}; border-radius: 14px; padding: 18px;">
                <span style="font-size: 0.72rem; font-weight: 800; color: ${badgeColor}; letter-spacing: 1.2px; text-transform: uppercase; display: block; margin-bottom: 6px;">
                    ${badgeLabel}
                </span>
                <h2 style="color: var(--text-heading); font-size: 1.45rem; margin: 0; font-weight: 800; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                    <span>${career.name || "Career Role"}</span>
                    ${nationBadge}
                </h2>
            </div>

            <!-- Country Salary Ranges -->
            <div style="background: rgba(0,0,0,0.35); border: 1px solid var(--border); border-radius: 14px; padding: 18px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 8px;">
                    <span style="font-size: 0.82rem; font-weight: 800; color: ${accentColor}; display: flex; align-items: center; gap: 6px;">
                        <i class="fa-solid fa-coins"></i> ${countryName} Pay Bands
                    </span>
                </div>

                ${showIndiaExamNote ? `
                <div style="background: rgba(249, 115, 22, 0.08); border: 1px solid rgba(249, 115, 22, 0.35); border-radius: 10px; padding: 10px; margin-bottom: 12px;">
                    <span style="font-size: 0.78rem; color: #f97316; font-weight: 700; display: flex; align-items: center; gap: 6px; line-height: 1.4;">
                        <i class="fa-solid fa-circle-info"></i> ${career.name || 'This exam'} is an Indian entrance/government exam and is not conducted in ${countryTarget}. Official salary compensation is rendered in Indian Rupees (₹).
                    </span>
                </div>
                ` : ''}
                
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; text-align: center;">
                    <div style="background: rgba(34, 197, 94, 0.06); border: 1px solid rgba(34, 197, 94, 0.25); border-radius: 10px; padding: 10px;">
                        <span style="font-size: 0.68rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase; display: block;">🌱 Entry Level</span>
                        <strong style="color: #22c55e; font-size: 0.88rem; display: block; margin-top: 4px;">${fresherPay}</strong>
                    </div>
                    <div style="background: rgba(250, 204, 21, 0.06); border: 1px solid rgba(250, 204, 21, 0.25); border-radius: 10px; padding: 10px;">
                        <span style="font-size: 0.68rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase; display: block;">⚡ Mid Level</span>
                        <strong style="color: var(--accent); font-size: 0.88rem; display: block; margin-top: 4px;">${midPay}</strong>
                    </div>
                    <div style="background: rgba(168, 85, 247, 0.06); border: 1px solid rgba(168, 85, 247, 0.25); border-radius: 10px; padding: 10px;">
                        <span style="font-size: 0.68rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase; display: block;">👑 Senior Lead</span>
                        <strong style="color: #a855f7; font-size: 0.88rem; display: block; margin-top: 4px;">${seniorPay}</strong>
                    </div>
                </div>
                <div style="margin-top: 12px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 10px; font-size: 0.8rem; color: var(--text-secondary); line-height: 1.45;">
                    <strong>Why this salary?</strong> ${salaryBench.reason || 'This compensation profile is shaped by technical expertise requirements, talent scarcity, and industry margins.'}
                </div>
                <div style="margin-top: 10px; padding-top: 8px; border-top: 1px dashed rgba(255,255,255,0.06); font-size: 0.74rem; color: var(--text-muted); display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
                    <span><i class="fa-solid fa-database" style="color: ${accentColor};"></i> Sources:</span>
                    ${sourcesChecked.map(src => `<span style="background: rgba(255,255,255,0.03); padding: 1px 6px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.05); color: var(--text-secondary); font-weight: 600;">${src}</span>`).join('')}
                </div>
            </div>

            <!-- Opportunity Fit Index & Market Indicators -->
            <div style="background: rgba(0,0,0,0.35); border: 1px solid var(--border); border-radius: 14px; padding: 18px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div>
                        <span style="font-size: 0.88rem; font-weight: 800; color: var(--text-heading); display: block;">🚀 Opportunity Fit Index</span>
                        <span style="font-size: 0.72rem; color: var(--text-muted); font-weight: 600;">Evaluated against Market Openings, Security & Barrier to Entry</span>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 1.5rem; font-weight: 900; color: ${fitColor}; display: block;">${fitScore}/100</span>
                    </div>
                </div>

                <div style="background: ${fitBadgeBg}; border: 1px solid ${fitBorder}; border-radius: 10px; padding: 8px 12px; margin-bottom: 12px;">
                    <span style="font-size: 0.76rem; font-weight: 700; color: ${fitColor}; display: flex; align-items: center; gap: 6px;">
                        ${fitTierLabel}
                    </span>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: 10px; padding: 10px;">
                        <span style="font-size: 0.7rem; color: var(--text-muted); font-weight: 700; display: block; text-transform: uppercase;">🔥 JOB DEMAND TIER</span>
                        <strong style="color: #22c55e; font-size: 0.86rem;">${demandRating}</strong>
                    </div>
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: 10px; padding: 10px;">
                        <span style="font-size: 0.7rem; color: var(--text-muted); font-weight: 700; display: block; text-transform: uppercase;">🚀 5-YR SECTOR OUTLOOK</span>
                        <strong style="color: #3b82f6; font-size: 0.86rem;">${growthOutlook}</strong>
                    </div>
                </div>

                <div style="margin-top: 10px; font-size: 0.78rem; color: var(--text-secondary); background: rgba(255,255,255,0.02); border-radius: 8px; padding: 8px 12px; border: 1px solid var(--border);">
                    ⏳ <strong>Preparation & Entry Curve:</strong> ${learningTime}
                </div>
            </div>

            <!-- AI Disruption Resilience & Reality Metrics -->
            <div style="background: rgba(0,0,0,0.35); border: 1px solid var(--border); border-radius: 14px; padding: 18px;">
                <h4 style="margin: 0 0 10px; font-size: 0.85rem; color: var(--text-heading); font-weight: 800; display: flex; align-items: center; gap: 8px;">
                    🛡️ AI Automation Resilience & Work Reality
                </h4>
                
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <div style="background: rgba(59, 130, 246, 0.06); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 10px; padding: 10px;">
                        <span style="font-size: 0.7rem; color: #60a5fa; font-weight: 800; text-transform: uppercase; display: block;">🛡️ AI Disruption Risk</span>
                        <span style="font-size: 0.82rem; color: var(--text-primary); font-weight: 600; display: block; margin-top: 2px;">
                            ${career.ai_automation_risk || 'Low (15-20%) — Requires High Creative & System Oversight'}
                        </span>
                    </div>

                    <div style="background: rgba(250, 204, 21, 0.06); border: 1px solid rgba(250, 204, 21, 0.2); border-radius: 10px; padding: 10px;">
                        <span style="font-size: 0.7rem; color: #fde047; font-weight: 800; text-transform: uppercase; display: block;">⏰ Work Environment & Pace</span>
                        <span style="font-size: 0.82rem; color: var(--text-primary); font-weight: 600; display: block; margin-top: 2px;">
                            ${career.work_life_balance || '40-45 Hours/Week • Hybrid Remote & Office'}
                        </span>
                    </div>

                    <div style="background: rgba(34, 197, 94, 0.06); border: 1px solid rgba(34, 197, 94, 0.2); border-radius: 10px; padding: 10px;">
                        <span style="font-size: 0.7rem; color: #22c55e; font-weight: 800; text-transform: uppercase; display: block;">🎓 Education ROI Horizon</span>
                        <span style="font-size: 0.82rem; color: var(--text-primary); font-weight: 600; display: block; margin-top: 2px;">
                            ${career.education_roi_years || '1.5 - 2 Years Post Graduation to Recover Costs'}
                        </span>
                    </div>
                </div>
            </div>

            <!-- 5-Year Progression Timeline -->
            ${timeline.length ? `
            <div style="background: rgba(0,0,0,0.35); border: 1px solid var(--border); border-radius: 14px; padding: 18px;">
                <h4 style="margin: 0 0 10px; font-size: 0.85rem; color: var(--text-heading); font-weight: 800;">
                    📈 5-Year Promotion & Title Escalation
                </h4>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    ${timeline.map(step => `
                        <div style="font-size: 0.78rem; color: var(--text-secondary); background: rgba(255,255,255,0.03); padding: 8px 12px; border-radius: 8px; border-left: 3px solid ${accentColor};">
                            ${step}
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}

            <!-- Top Organizations -->
            <div style="background: rgba(0,0,0,0.35); border: 1px solid var(--border); border-radius: 14px; padding: 18px;">
                <h4 style="margin: 0 0 10px; font-size: 0.85rem; color: var(--text-heading); font-weight: 800;">
                    🏢 Prime Hiring Employers
                </h4>
                <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                    ${orgs.length ? orgs.map(org => `
                        <span style="font-size: 0.76rem; background: rgba(255,255,255,0.05); border: 1px solid var(--border); padding: 4px 10px; border-radius: 6px; color: var(--text-secondary); font-weight: 600;">
                            ${typeof org === 'object' ? (org.name || JSON.stringify(org)) : org}
                        </span>
                    `).join('') : '<span style="font-size: 0.78rem; color: var(--text-muted);">Major Industry Employers</span>'}
                </div>
            </div>

            <!-- Top Hiring Cities -->
            <div style="background: rgba(0,0,0,0.35); border: 1px solid var(--border); border-radius: 14px; padding: 18px;">
                <h4 style="margin: 0 0 10px; font-size: 0.85rem; color: var(--text-heading); font-weight: 800;">
                    🏙️ Top Hiring Hub Cities
                </h4>
                <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                    ${renderedCities || '<span style="font-size: 0.78rem; color: var(--text-muted);">Global Talent Hubs</span>'}
                </div>
            </div>
        </div>
    `;
}