/**
 * CareerVerse AI — Career Navigator Agent
 * Persistence: Supabase (Source of Truth) + localStorage (fast client cache)
 * Identity: UUID cookie `cv_user_id` + localStorage fallback
 */

// ─── State & Storage Keys ─────────────────────────────────────────────────────
const STATE_KEY = 'cv_navigator_v2';
const USER_ID_KEY = 'cv_user_id';

let state = {
    userId: null,
    profile: {},
    currentSkills: [],      // tag array
    gapData: null,
    roadmapData: null,
    milestones: {},         // { milestoneId: boolean }
    currentStep: 1
};

// ─── Cookie & UUID Helpers ────────────────────────────────────────────────────
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

function setCookie(name, val, days = 365) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    document.cookie = `${name}=${val};expires=${date.toUTCString()};path=/;SameSite=Lax`;
}

function generateUUID() {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        return crypto.randomUUID();
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function getUserId() {
    if (state.userId) return state.userId;
    let uid = getCookie('cv_user_id') || localStorage.getItem(USER_ID_KEY);
    if (!uid) {
        uid = generateUUID();
    }
    setCookie('cv_user_id', uid, 365);
    localStorage.setItem(USER_ID_KEY, uid);
    state.userId = uid;
    return uid;
}

// ─── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    state.userId = getUserId();
    initSkillTagInput();
    initQuickSkills();

    // 1. Fast restore from local cache first for instant responsiveness
    loadLocalCache();
    restoreProfileForm();
    if (state.currentStep > 1) {
        restoreToStep(state.currentStep);
    }

    // 2. Fetch ground-truth state from Supabase in background
    await syncWithSupabase();
});

// ─── Supabase Profile Sync ────────────────────────────────────────────────────
async function syncWithSupabase() {
    const uid = getUserId();
    updateSyncBadge('syncing', 'Syncing with Supabase...');
    try {
        const res = await fetch('/navigator-profile-init', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: uid })
        });
        const json = await res.json();
        if (!json.success) {
            updateSyncBadge('offline', 'Local Cache Active');
            return;
        }

        // Merge Supabase ground truth
        let hasRemoteData = false;
        if (json.profile && Object.keys(json.profile).length > 0) {
            state.profile = Object.assign({}, state.profile, json.profile);
            hasRemoteData = true;
        }
        if (Array.isArray(json.current_skills) && json.current_skills.length > 0) {
            state.currentSkills = json.current_skills;
            hasRemoteData = true;
        }
        if (json.gap_data) {
            state.gapData = json.gap_data;
            hasRemoteData = true;
        }
        if (json.roadmap_data) {
            state.roadmapData = json.roadmap_data;
            hasRemoteData = true;
        }
        if (json.milestones && Object.keys(json.milestones).length > 0) {
            state.milestones = json.milestones;
            hasRemoteData = true;
        }
        if (json.current_step && json.current_step > 1) {
            state.currentStep = json.current_step;
        }

        // Save fresh ground truth into local cache
        saveLocalCache();

        // Refresh UI with Supabase data
        restoreProfileForm();
        if (state.currentStep > 1) {
            restoreToStep(state.currentStep);
        }

        updateSyncBadge('synced', 'Supabase Cloud Synced');
    } catch(err) {
        console.warn('[NAVIGATOR] Supabase sync fallback:', err);
        updateSyncBadge('offline', 'Local Cache Active');
    }
}

function updateSyncBadge(status, text) {
    const badge = document.getElementById('syncStatusBadge');
    if (!badge) return;
    if (status === 'synced') {
        badge.innerHTML = `<i class="fa-solid fa-cloud-check" style="color:#10b981"></i> <span>${text}</span>`;
        badge.style.borderColor = 'rgba(16,185,129,0.3)';
        badge.style.color = '#34d399';
    } else if (status === 'syncing') {
        badge.innerHTML = `<i class="fa-solid fa-arrows-rotate fa-spin" style="color:#a78bfa"></i> <span>${text}</span>`;
        badge.style.borderColor = 'rgba(167,139,250,0.3)';
        badge.style.color = '#c4b5fd';
    } else {
        badge.innerHTML = `<i class="fa-solid fa-hard-drive" style="color:#f59e0b"></i> <span>${text}</span>`;
        badge.style.borderColor = 'rgba(245,158,11,0.3)';
        badge.style.color = '#fbbf24';
    }
}

// ─── Local Cache Persistence ──────────────────────────────────────────────────
function saveLocalCache() {
    try {
        localStorage.setItem(STATE_KEY, JSON.stringify(state));
    } catch(e) {}
}

function loadLocalCache() {
    try {
        const raw = localStorage.getItem(STATE_KEY);
        if (raw) {
            const parsed = JSON.parse(raw);
            Object.assign(state, parsed);
        }
    } catch(e) {
        state = {
            userId: getUserId(),
            profile: {},
            currentSkills: [],
            gapData: null,
            roadmapData: null,
            milestones: {},
            currentStep: 1
        };
    }
}

// ─── Profile Form Restore ─────────────────────────────────────────────────────
function restoreProfileForm() {
    const p = state.profile;
    if (!p) return;
    const fields = ['profileName','profileEducation','profileDegree','profileExperience',
                    'profileInterests','profileTargetRole','profileCountry','profileGoal'];
    fields.forEach(id => {
        const el = document.getElementById(id);
        if (el && p[id] !== undefined && p[id] !== null) {
            el.value = p[id];
        }
    });

    // Clear and restore skill tags
    const wrapper = document.getElementById('skillsTagsWrapper');
    if (wrapper) {
        wrapper.querySelectorAll('.skill-tag').forEach(t => t.remove());
    }
    if (state.currentSkills && state.currentSkills.length) {
        state.currentSkills.forEach(s => addSkillTag(s, false));
    }
}

// ─── Skill Tag Input ──────────────────────────────────────────────────────────
function initSkillTagInput() {
    const input = document.getElementById('skillsTagInput');
    const wrapper = document.getElementById('skillsTagsWrapper');
    if (!input || !wrapper) return;

    wrapper.addEventListener('click', () => input.focus());

    input.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            const val = input.value.trim().replace(/,$/, '');
            if (val) { addSkillTag(val); input.value = ''; }
        }
        if (e.key === 'Backspace' && !input.value) {
            const tags = wrapper.querySelectorAll('.skill-tag');
            if (tags.length) {
                const last = tags[tags.length - 1];
                const skill = last.querySelector('span') ? last.querySelector('span').textContent : last.textContent.replace('×','').trim();
                last.remove();
                state.currentSkills = state.currentSkills.filter(s => s !== skill);
                saveLocalCache();
            }
        }
    });
}

function addSkillTag(skill, save = true) {
    skill = skill.trim();
    if (!skill) return;
    if (state.currentSkills.includes(skill)) return;

    const wrapper = document.getElementById('skillsTagsWrapper');
    const input   = document.getElementById('skillsTagInput');
    if (!wrapper) return;

    const tag = document.createElement('div');
    tag.className = 'skill-tag';
    tag.innerHTML = `<span>${skill}</span><span class="skill-tag-remove" onclick="removeSkillTag(this, '${skill.replace(/'/g,"\\'")}')">×</span>`;
    wrapper.insertBefore(tag, input);

    if (save) {
        state.currentSkills.push(skill);
        saveLocalCache();
    }
}

function removeSkillTag(el, skill) {
    el.closest('.skill-tag').remove();
    state.currentSkills = state.currentSkills.filter(s => s !== skill);
    saveLocalCache();
}

function initQuickSkills() {
    document.querySelectorAll('.q-skill').forEach(el => {
        el.addEventListener('click', () => {
            const skill = el.textContent.trim();
            addSkillTag(skill);
        });
    });
}

// ─── Step Navigation ──────────────────────────────────────────────────────────
function setStepUI(step) {
    for (let i = 1; i <= 4; i++) {
        const panel = document.getElementById(`panel${i}`);
        const item  = document.getElementById(`stepItem${i}`);
        if (panel) panel.classList.toggle('active', i === step);
        if (item) {
            item.classList.toggle('active', i === step);
            item.classList.toggle('completed', i < step);
        }
    }
    state.currentStep = step;
    saveLocalCache();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function goToStep(step) { setStepUI(step); }

function restoreToStep(step) {
    if (step === 2 && state.gapData) {
        setStepUI(2);
        updateBanners();
        renderGapResults(state.gapData);
    } else if (step === 3 && state.roadmapData) {
        setStepUI(3);
        updateBanners();
        renderRoadmap(state.roadmapData);
    } else if (step === 4 && state.roadmapData) {
        setStepUI(4);
        updateBanners();
        runAdaptiveAnalysis();
    } else {
        setStepUI(1);
    }
}

// ─── Step 1 → 2: Save Profile to Supabase & Trigger Gap Analysis ─────────────
async function goToStep2() {
    const targetRole = document.getElementById('profileTargetRole').value.trim();
    if (!targetRole) {
        alert('Please enter your target career / role to continue.');
        document.getElementById('profileTargetRole').focus();
        return;
    }

    // Collect profile data
    state.profile = {
        profileName:        document.getElementById('profileName').value.trim(),
        profileEducation:   document.getElementById('profileEducation').value,
        profileDegree:      document.getElementById('profileDegree').value.trim(),
        profileExperience:  document.getElementById('profileExperience').value,
        profileInterests:   document.getElementById('profileInterests').value.trim(),
        profileTargetRole:  targetRole,
        profileCountry:     document.getElementById('profileCountry').value.trim() || 'India',
        profileGoal:        document.getElementById('profileGoal').value.trim()
    };
    saveLocalCache();

    // Persist profile to Supabase (Source of Truth)
    updateSyncBadge('syncing', 'Saving to Supabase...');
    fetch('/navigator-profile-save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: getUserId(),
            profile: state.profile,
            current_skills: state.currentSkills,
            current_step: 2
        })
    }).then(res => res.json())
      .then(json => {
          if (json.success) updateSyncBadge('synced', 'Profile Saved to Supabase');
      }).catch(err => {
          console.warn('[NAVIGATOR] Supabase profile save error:', err);
      });

    setStepUI(2);
    updateBanners();
    runGapAnalysis();
}

// ─── Step 2 → 3 ───────────────────────────────────────────────────────────────
function goToStep3() {
    setStepUI(3);
    updateBanners();
    runRoadmapGeneration();
}

function updateBanners() {
    const name = state.profile.profileName || 'You';
    const role = state.profile.profileTargetRole || '…';
    safeSet('bannerName', name);
    safeSet('bannerName3', name);
    safeSet('bannerRole3', role);
    safeSet('bannerName4', name);
}

function safeSet(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

// ─── Gap Analysis (Supabase-backed) ──────────────────────────────────────────
async function runGapAnalysis() {
    showEl('gapLoadingCard');
    hideEl('gapResultsWrap');
    hideEl('gapErrorWrap');
    animateLoaderSteps(['lstep1','lstep2','lstep3','lstep4','lstep5'], 600);

    const body = {
        user_id: getUserId(),
        profile: state.profile,
        current_skills: state.currentSkills
    };

    try {
        const res = await fetch('/navigator-gap-api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const json = await res.json();
        if (!json.success) throw new Error(json.error || 'API error');

        const gapData = json.data || json;
        state.gapData = gapData;
        saveLocalCache();
        hideEl('gapLoadingCard');
        showEl('gapResultsWrap');
        renderGapResults(gapData);
    } catch(err) {
        hideEl('gapLoadingCard');
        const errEl = document.getElementById('gapErrorMsg');
        if (errEl) errEl.textContent = err.message || 'Could not analyze skill gap. Please try again.';
        showEl('gapErrorWrap');
    }
}

function renderGapResults(data) {
    // Score ring
    const score = Math.min(100, Math.max(0, Number(data.skill_gap_score || 0)));
    const circumference = 326;
    const offset = circumference - (score / 100) * circumference;
    const circle = document.getElementById('scoreRingCircle');
    if (circle) {
        setTimeout(() => { circle.style.strokeDashoffset = offset; }, 100);
    }
    // Animate score number
    animateNumber('scoreNum', 0, score, 1400);

    safeSet('readinessStatus', data.readiness_status || '—');
    safeSet('readinessSub',    data.gap_severity || 'Career readiness');
    safeSet('statLevel',       data.career_level || '—');
    safeSet('statSeverity',    data.gap_severity || '—');
    safeSet('statMatch',       data.industry_demand_match ? `${data.industry_demand_match}%` : '—');
    safeSet('statSkillsFound', data.existing_skills ? `${data.existing_skills.length} skills` : '—');

    // Radar chart
    if (data.skill_analysis && data.skill_analysis.length) renderRadar(data.skill_analysis);

    // Gap list
    renderGapList(data.missing_skills || [], data.priority_skills || [], data.why_explanations || {}, data.how_to_close || {});

    // Existing skills
    const existingWrap = document.getElementById('existingSkillsList');
    if (existingWrap) {
        existingWrap.innerHTML = (data.existing_skills || []).map(s =>
            `<div class="existing-chip"><i class="fa-solid fa-check"></i>${s}</div>`
        ).join('');
    }

    // Recommendation
    safeSet('aiRecommendation', data.recommendation || '');
}

function renderRadar(skillAnalysis) {
    const canvas = document.getElementById('radarChart');
    if (!canvas || !window.Chart) return;

    if (window._radarInstance) { window._radarInstance.destroy(); }

    const labels = skillAnalysis.map(s => s.skill);
    const values = skillAnalysis.map(s => Number(s.score));

    window._radarInstance = new Chart(canvas, {
        type: 'radar',
        data: {
            labels,
            datasets: [{
                label: 'Current Competency',
                data: values,
                backgroundColor: 'rgba(167,139,250,0.15)',
                borderColor: 'rgba(167,139,250,0.8)',
                borderWidth: 2,
                pointBackgroundColor: '#a78bfa',
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            scales: {
                r: {
                    min: 0, max: 100,
                    ticks: { stepSize: 25, color: '#525252', backdropColor: 'transparent', font: { size: 10 } },
                    grid: { color: 'rgba(255,255,255,0.06)' },
                    pointLabels: { color: '#a3a3a3', font: { size: 11 } },
                    angleLines: { color: 'rgba(255,255,255,0.06)' }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function renderGapList(missingSkills, prioritySkills, whyMap, howMap) {
    const list = document.getElementById('gapList');
    if (!list) return;

    const priorityLevels = ['critical','critical','high','high','medium','medium','low'];

    list.innerHTML = missingSkills.slice(0, 7).map((skill, i) => {
        const cleanSkill = skill.replace(/^\d+\.\s*/, '').trim();
        const priority   = priorityLevels[i] || 'low';
        const rankClass  = i < 2 ? `rank-${i+1}` : (i < 4 ? 'rank-3' : 'rank-other');
        const why = whyMap[cleanSkill] || (prioritySkills[i] ? prioritySkills[i].replace(/^\d+\.\s*/, '') : `Essential for your ${state.profile.profileTargetRole || 'target'} role`);
        const how = howMap[cleanSkill] || `Take targeted courses, build hands-on projects, and seek practical experience with ${cleanSkill}.`;

        return `
        <div class="gap-item" onclick="this.classList.toggle('expanded')">
            <div class="gap-item-rank ${rankClass}">#${i+1}</div>
            <div class="gap-item-body">
                <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:4px">
                    <span class="gap-item-name">${cleanSkill}</span>
                    <span class="gap-item-priority priority-${priority}">${priority}</span>
                </div>
                <div class="gap-item-why">${why}</div>
                <div class="gap-item-how"><i class="fa-solid fa-lightbulb" style="color:#facc15;margin-right:6px"></i>${how}</div>
            </div>
            <i class="fa-solid fa-chevron-down" style="color:var(--text-muted);font-size:0.7rem;margin-top:4px;transition:transform 0.2s"></i>
        </div>`;
    }).join('');
}

// ─── Roadmap Generation (Supabase-backed) ─────────────────────────────────────
async function runRoadmapGeneration() {
    showEl('roadmapLoadingCard');
    hideEl('roadmapResultsWrap');
    hideEl('roadmapErrorWrap');
    animateLoaderSteps(['rstep1','rstep2','rstep3','rstep4'], 900);

    const body = {
        user_id: getUserId(),
        profile: state.profile,
        current_skills: state.currentSkills,
        gap_data: state.gapData
    };

    try {
        const res = await fetch('/navigator-roadmap-api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const json = await res.json();
        if (!json.success) throw new Error(json.error || 'API error');

        const roadmapData = json.data || json;
        state.roadmapData = roadmapData;
        saveLocalCache();
        hideEl('roadmapLoadingCard');
        showEl('roadmapResultsWrap');
        renderRoadmap(roadmapData);
    } catch(err) {
        hideEl('roadmapLoadingCard');
        const errEl = document.getElementById('roadmapErrorMsg');
        if (errEl) errEl.textContent = err.message || 'Could not generate roadmap.';
        showEl('roadmapErrorWrap');
    }
}

function renderRoadmap(data) {
    const role = state.profile.profileTargetRole || 'Your Career';
    safeSet('roadmapTitle', `${role} — Learning Roadmap`);

    const phases = data.phases || [];
    const timeline = document.getElementById('roadmapTimeline');
    if (!timeline) return;

    let totalMilestones = 0;
    phases.forEach(phase => {
        if (phase.milestones) totalMilestones += phase.milestones.length;
    });

    timeline.innerHTML = phases.map((phase, pi) => {
        const phaseId = `phase_${pi}`;
        const milestones = phase.milestones || [];

        const milestonesHTML = milestones.map((m, mi) => {
            const mId = `${phaseId}_m${mi}`;
            const isDone = !!state.milestones[mId];
            return `
            <div class="milestone-item ${isDone ? 'done' : ''}" id="mitem_${mId}">
                <div class="milestone-checkbox" id="mcheck_${mId}" onclick="toggleMilestone('${mId}', ${pi}, ${totalMilestones})">
                    ${isDone ? '<i class="fa-solid fa-check"></i>' : ''}
                </div>
                <div class="milestone-body">
                    <div class="milestone-title">${m.title || m}</div>
                    ${m.type ? `<div class="milestone-meta"><i class="fa-solid fa-tag" style="font-size:0.6rem;margin-right:4px;color:var(--accent)"></i>${m.type}</div>` : ''}
                </div>
            </div>`;
        }).join('');

        const skillsHTML = (phase.skills || []).slice(0, 6).map(s =>
            `<span class="phase-skill-chip">${s}</span>`
        ).join('');

        const resourcesHTML = (phase.resources || []).slice(0, 3).map(r =>
            `<a href="${r.url || '#'}" target="_blank" rel="noopener" class="resource-link">
                <i class="fa-solid fa-arrow-up-right-from-square"></i>${r.name || r}
             </a>`
        ).join('');

        const phaseCompleted = milestones.length > 0 && milestones.every((m, mi) => !!state.milestones[`${phaseId}_m${mi}`]);
        const phaseInProgress = !phaseCompleted && milestones.some((m, mi) => !!state.milestones[`${phaseId}_m${mi}`]);
        const phaseClass = phaseCompleted ? 'completed' : (phaseInProgress ? 'in-progress' : '');
        const badgeClass = phaseCompleted ? 'badge-done' : (phaseInProgress ? 'badge-inprogress' : 'badge-todo');
        const badgeText  = phaseCompleted ? '✓ Done' : (phaseInProgress ? '▶ In Progress' : 'Not started');

        return `
        <div class="timeline-phase ${phaseClass}" id="tphase_${phaseId}">
            <div class="phase-node">${pi + 1}</div>
            <div class="phase-content">
                <div class="phase-header">
                    <span class="phase-title">${phase.title || `Phase ${pi+1}`}</span>
                    <span class="phase-status-badge ${badgeClass}">${badgeText}</span>
                </div>
                ${phase.description ? `<p style="font-size:0.78rem;color:var(--text-secondary);margin-bottom:10px;line-height:1.5">${phase.description}</p>` : ''}
                <div class="phase-skills-list">${skillsHTML}</div>
                <div class="milestones-list">${milestonesHTML}</div>
                ${resourcesHTML ? `<div class="phase-resources">${resourcesHTML}</div>` : ''}
            </div>
        </div>`;
    }).join('');

    updateProgressBar(totalMilestones);
}

// ─── Milestone Progress (Supabase-backed) ─────────────────────────────────────
function toggleMilestone(mId, phaseIdx, total) {
    state.milestones[mId] = !state.milestones[mId];
    saveLocalCache();

    const item  = document.getElementById(`mitem_${mId}`);
    const check = document.getElementById(`mcheck_${mId}`);
    if (item)  item.classList.toggle('done', state.milestones[mId]);
    if (check) check.innerHTML = state.milestones[mId] ? '<i class="fa-solid fa-check"></i>' : '';

    // Update phase status
    const phaseKey = mId.replace(/_m\d+$/, '');
    const phaseEl  = document.getElementById(`tphase_${phaseKey}`);
    if (phaseEl) {
        const allChecks = phaseEl.querySelectorAll('.milestone-item');
        const doneCount = phaseEl.querySelectorAll('.milestone-item.done').length;
        const isComplete = allChecks.length > 0 && doneCount === allChecks.length;
        const isPartial  = doneCount > 0 && !isComplete;
        phaseEl.classList.toggle('completed',   isComplete);
        phaseEl.classList.toggle('in-progress', isPartial && !isComplete);
    }

    updateProgressBar(total);

    // Save milestone progress to Supabase asynchronously
    fetch('/navigator-progress-save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: getUserId(),
            milestones: state.milestones,
            current_step: 3
        })
    }).then(res => res.json())
      .then(json => {
          if (json.success) updateSyncBadge('synced', 'Progress Saved to Supabase');
      }).catch(err => {
          console.warn('[NAVIGATOR] Progress save error:', err);
      });
}

function updateProgressBar(total) {
    const done = Object.values(state.milestones).filter(Boolean).length;
    const pct  = total > 0 ? Math.round((done / total) * 100) : 0;

    const fill = document.getElementById('progressBarFill');
    const pctEl = document.getElementById('progressPct');
    const labelEl = document.getElementById('progressLabel');
    if (fill)  fill.style.width = `${pct}%`;
    if (pctEl) pctEl.textContent = `${pct}%`;
    if (labelEl) labelEl.textContent = `${done} of ${total} milestones done`;

    const subtextEl = document.getElementById('progressSubtext');
    if (subtextEl) {
        if (pct === 0) subtextEl.textContent = 'Check off milestones as you complete them';
        else if (pct < 30) subtextEl.textContent = "Great start — keep it going! 🚀";
        else if (pct < 60) subtextEl.textContent = "You're making real progress! 🔥";
        else if (pct < 90) subtextEl.textContent = "Almost there — finish strong! 💪";
        else if (pct === 100) subtextEl.textContent = "🎉 Roadmap complete! You're ready.";
        else subtextEl.textContent = "Incredible momentum — keep pushing!";
    }
}

// ─── Adaptive Analysis (Supabase-backed) ──────────────────────────────────────
async function runAdaptiveAnalysis() {
    const adaptResult = document.getElementById('adaptResult');
    if (adaptResult) adaptResult.classList.add('visible');

    showEl('adaptLoadingCard');
    hideEl('adaptContent');
    hideEl('adaptError');

    const completedMilestones = Object.entries(state.milestones)
        .filter(([,v]) => v).map(([k]) => k);

    const body = {
        user_id: getUserId(),
        profile: state.profile,
        current_skills: state.currentSkills,
        gap_data: state.gapData,
        roadmap_data: state.roadmapData,
        milestones: state.milestones,
        completed_milestones: completedMilestones,
        total_milestones: Object.keys(state.milestones).length || 0,
        target_role: state.profile.profileTargetRole || 'Software Engineer'
    };

    try {
        const res = await fetch('/navigator-adapt-api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const json = await res.json();
        if (!json.success) throw new Error(json.error || 'API error');

        const adaptData = json.data || json;
        hideEl('adaptLoadingCard');
        renderAdaptiveResults(adaptData, completedMilestones.length, body.total_milestones);
        showEl('adaptContent');
        updateSyncBadge('synced', 'Adaptive Progress Saved');
    } catch(err) {
        hideEl('adaptLoadingCard');
        const errEl = document.getElementById('adaptErrorMsg');
        if (errEl) errEl.textContent = err.message || 'Could not run adaptive analysis.';
        showEl('adaptError');
    }
}

function renderAdaptiveResults(data, doneMilestones, totalMilestones) {
    safeSet('adaptSummaryText', data.progress_summary || `You've completed ${doneMilestones} of ${totalMilestones} milestones. Keep going!`);

    const adaptGapList = document.getElementById('adaptGapList');
    if (adaptGapList && data.updated_gaps) {
        const whyMap = data.why_explanations || {};
        const howMap = data.how_to_close || {};
        renderGapListInto(adaptGapList, data.updated_gaps, whyMap, howMap);
    }

    const actionsList = document.getElementById('nextActionsList');
    if (actionsList && data.next_actions) {
        actionsList.innerHTML = data.next_actions.slice(0, 3).map((action, i) => `
            <div class="next-action-item">
                <div class="next-action-num">${i + 1}</div>
                <div class="next-action-text">${action}</div>
            </div>
        `).join('');
    }
}

function renderGapListInto(container, skills, whyMap, howMap) {
    const priorityLevels = ['critical','high','high','medium','medium','low'];
    container.innerHTML = skills.slice(0, 5).map((skill, i) => {
        const clean = skill.replace(/^\d+\.\s*/, '').trim();
        const priority = priorityLevels[i] || 'low';
        const rankClass = i < 1 ? 'rank-1' : (i < 3 ? 'rank-2' : 'rank-other');
        const why = whyMap[clean] || `High priority for ${state.profile.profileTargetRole || 'your target role'}`;
        const how = howMap[clean] || `Focus on ${clean} through projects and practice.`;
        return `
        <div class="gap-item" onclick="this.classList.toggle('expanded')">
            <div class="gap-item-rank ${rankClass}">#${i+1}</div>
            <div class="gap-item-body">
                <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:4px">
                    <span class="gap-item-name">${clean}</span>
                    <span class="gap-item-priority priority-${priority}">${priority}</span>
                </div>
                <div class="gap-item-why">${why}</div>
                <div class="gap-item-how"><i class="fa-solid fa-lightbulb" style="color:#facc15;margin-right:6px"></i>${how}</div>
            </div>
            <i class="fa-solid fa-chevron-down" style="color:var(--text-muted);font-size:0.7rem;margin-top:4px"></i>
        </div>`;
    }).join('');
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function showEl(id) {
    const el = document.getElementById(id);
    if (el) el.style.display = '';
}

function hideEl(id) {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
}

function animateNumber(id, from, to, duration) {
    const el = document.getElementById(id);
    if (!el) return;
    const start = Date.now();
    const tick = () => {
        const elapsed = Date.now() - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(from + (to - from) * eased);
        if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
}

function animateLoaderSteps(ids, delay) {
    ids.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.classList.remove('active','done');
            el.querySelector('i').className = 'fa-solid fa-circle';
        }
    });
    ids.forEach((id, i) => {
        setTimeout(() => {
            if (i > 0) {
                const prev = document.getElementById(ids[i-1]);
                if (prev) {
                    prev.classList.remove('active');
                    prev.classList.add('done');
                    prev.querySelector('i').className = 'fa-solid fa-check';
                }
            }
            const el = document.getElementById(id);
            if (el) {
                el.classList.add('active');
                el.querySelector('i').className = 'fa-solid fa-spinner fa-spin';
            }
        }, i * delay);
    });
}
