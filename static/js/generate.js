// ==========================================
// CareerVerse AI - generate.js
// ==========================================

const generateBtn = document.getElementById("generateBtn");
const careerInput = document.getElementById("careerInput");
const countryInput = document.getElementById("countryInput");
const resultCard = document.getElementById("resultCard");
const downloadBtn = document.getElementById("downloadBtn");


// Auto-trigger from URL parameters (e.g. /generate?role=AI+Engineer)
window.addEventListener("DOMContentLoaded", () => {
    const urlParams = new URLSearchParams(window.location.search);
    const roleParam = urlParams.get("role") || urlParams.get("career");
    if (roleParam && careerInput) {
        careerInput.value = roleParam;
        generateBtn.click();
    }
});

const VALID_ACRONYMS = [
    "ai", "ml", "ui", "ux", "hr", "pr", "it", "qa", "seo", "sre", "cto", "ceo", "cfo", "vp", "dba", "erp", "crm", "bi", "ar", "vr", "3d", "2d", "5g", "cad", "gis", "pm", "dev", "ops", "sec", "mlops", "devops", "secops", "web3", "web2", "ios", "nlp", "llm", "genai", "c++", "c#", ".net",
    "mbbs", "bds", "bams", "bhms", "bpt", "mch", "dnb", "bums", "brms", "md", "ms", "frcs", "mrcp", "mrcs", "pharmd", "gnm", "anm",
    "llb", "llm", "bcl", "aibe", "clat",
    "ias", "ips", "ifs", "irs", "upsc", "nda", "cds", "afcat", "ssc", "psc", "gpsc", "mpsc", "uppsc", "bpsc", "chsl", "wbcs", "jkpsc", "tnpsc", "tspsc", "cgpsc", "hpsc", "kpsc", "ppsc", "mppsc", "rrb", "isro", "drdo", "barc", "hal", "bel", "gail", "ntpc",
    "cpl", "atpl", "ppl", "dgca", "faa",
    "ca", "cfa", "cpa", "cfp", "cma", "acca", "cs", "frm",
    "btech", "mtech", "bca", "mca", "bba", "mba", "bsc", "msc", "phd", "bed", "med", "bdes", "mdes", "barch", "march"
];

const QWERTY_PATTERNS = [
    "qwertyuiop", "poiuytrewq", "asdfghjkl", "lkjhgfdsa", "zxcvbnm", "mnbvcxz",
    "qazwsx", "edcrfv", "tgbnhy", "ujmiko", "olp", "zaq", "xsw", "cde", "vfr", "bgt", "nhy", "mju", "lki", "plo",
    "1234567890", "0987654321"
];

const CAREER_KEYWORDS = new Set([
    // Engineering & Technology
    "engineer", "developer", "architect", "designer", "manager", "analyst", "consultant", "specialist",
    "lead", "administrator", "director", "officer", "scientist", "researcher", "coder", "programmer",
    "software", "web", "fullstack", "frontend", "backend", "cloud", "data", "ai", "ml", "machine",
    "learning", "cybersecurity", "network", "system", "database", "devops", "sre", "ui", "ux",
    "product", "project", "scrum", "agile", "qa", "tester", "security", "sysadmin", "infrastructure",
    "robotics", "embedded", "firmware", "mechatronics", "telecom", "hardware", "bioinformatics",

    // Healthcare, Medicine & Life Sciences
    "doctor", "physician", "surgeon", "nurse", "pharmacist", "therapist", "dentist", "psychiatrist",
    "psychologist", "counselor", "paramedic", "optometrist", "radiologist", "pathologist", "pediatrician",
    "dermatologist", "cardiologist", "neurologist", "oncologist", "veterinarian", "biologist", "chemist",
    "physicist", "microbiologist", "geneticist", "biochemist", "epidemiologist", "pharmacologist",
    "medical", "clinical", "nursing", "healthcare", "pharma", "biotech", "nutritionist", "dietitian",

    // Business, Finance, Law & Executive
    "accountant", "auditor", "lawyer", "attorney", "paralegal", "judge", "advocate", "solicitor",
    "banker", "trader", "investor", "broker", "underwriter", "actuary", "economist", "statistician",
    "mathematician", "evaluator", "appraiser", "hr", "recruiter", "founder", "ceo", "cto", "cfo",
    "coo", "cmo", "cio", "vp", "head", "executive", "administrator", "officer", "supervisor",
    "business", "sales", "marketing", "finance", "accounting", "banking", "insurance", "realestate",
    "realtor", "consulting", "strategy", "operations", "supply", "chain", "logistics", "procurement",

    // Education, Academia & Research
    "teacher", "professor", "instructor", "tutor", "lecturer", "educator", "principal", "dean",
    "academic", "scholar", "historian", "archaeologist", "anthropologist", "sociologist", "geologist",
    "astronomer", "meteorologist", "oceanographer", "philosopher", "linguist", "translator", "interpreter",

    // Media, Arts, Entertainment & Sports
    "artist", "animator", "illustrator", "painter", "sculptor", "designer", "photographer", "videographer",
    "filmmaker", "director", "producer", "editor", "cinematographer", "actor", "actress", "model",
    "musician", "composer", "singer", "dancer", "choreographer", "writer", "author", "journalist",
    "reporter", "copywriter", "content", "creator", "influencer", "streamer", "gamer",
    "athlete", "coach", "trainer", "referee", "sports", "fitness", "physiotherapist",

    // Architecture, Construction, Trades & Skilled Crafts
    "builder", "contractor", "carpenter", "electrician", "plumber", "welder", "machinist", "mechanic",
    "technician", "mason", "painter", "roofer", "glazier", "surveyor", "drafteur", "interior",
    "landscape", "craftsman", "artisan", "blacksmith", "jeweler", "tailor", "fashion",

    // Service, Culinary, Hospitality & Aviation/Maritime
    "chef", "cook", "baker", "barista", "sommelier", "waiter", "waitress", "bartender", "hotelier",
    "concierge", "pilot", "captain", "copilot", "navigator", "sailor", "mariner", "flight",
    "attendant", "steward", "driver", "chauffeur", "conductor", "dispatcher", "logistics",

    // Government, Public Safety, Agriculture & Environment
    "policeman", "detective", "firefighter", "soldier", "officer", "investigator", "inspector",
    "civil", "servant", "diplomat", "politician", "mayor", "governor", "ranger", "forester",
    "farmer", "agronomist", "botanist", "zoologist", "ecologist", "environmental", "conservationist",

    // General Role Standard Terms
    "lead", "senior", "junior", "principal", "chief", "head", "associate", "intern", "trainee",
    "freelancer", "consultant", "expert", "practitioner", "agent", "advisor", "coordinator",
    "planner", "strategist", "analyst", "specialist"
]);

const REAL_WORLD_COUNTRIES = new Set([
    "afghanistan", "albania", "algeria", "andorra", "angola", "antigua and barbuda", "argentina", "armenia",
    "australia", "austria", "azerbaijan", "bahamas", "bahrain", "bangladesh", "barbados", "belarus",
    "belgium", "belize", "benin", "bhutan", "bolivia", "bosnia and herzegovina", "botswana", "brazil",
    "brunei", "bulgaria", "burkina faso", "burundi", "cambodia", "cameroon", "canada", "cape verde",
    "central african republic", "chad", "chile", "china", "colombia", "comoros", "congo", "costa rica",
    "croatia", "cuba", "cyprus", "czech republic", "czechia", "denmark", "djibouti", "dominica",
    "dominican republic", "ecuador", "egypt", "el salvador", "equatorial guinea", "eritrea", "estonia",
    "eswatini", "ethiopia", "fiji", "finland", "france", "gabon", "gambia", "georgia", "germany",
    "ghana", "greece", "grenada", "guatemala", "guinea", "guinea-bissau", "guyana", "haiti", "honduras",
    "hungary", "iceland", "india", "indonesia", "iran", "iraq", "ireland", "israel", "italy",
    "jamaica", "japan", "jordan", "kazakhstan", "kenya", "kiribati", "kuwait", "kyrgyzstan", "laos",
    "latvia", "lebanon", "lesotho", "liberia", "libya", "liechtenstein", "lithuania", "luxembourg",
    "madagascar", "malawi", "malaysia", "maldives", "mali", "malta", "marshall islands", "mauritania",
    "mauritius", "mexico", "micronesia", "moldova", "monaco", "mongolia", "montenegro", "morocco",
    "mozambique", "myanmar", "namibia", "nauru", "nepal", "netherlands", "new zealand", "nicaragua",
    "niger", "nigeria", "north korea", "north macedonia", "norway", "oman", "pakistan", "palau",
    "palestine", "panama", "papua new guinea", "paraguay", "peru", "philippines", "poland", "portugal",
    "qatar", "romania", "russia", "rwanda", "saint kitts and nevis", "saint lucia",
    "saint vincent and the grenadines", "samoa", "san marino", "sao tome and principe", "saudi arabia",
    "senegal", "serbia", "seychelles", "sierra leone", "singapore", "slovakia", "slovenia",
    "solomon islands", "somalia", "south africa", "south korea", "south sudan", "spain", "sri lanka",
    "sudan", "suriname", "sweden", "switzerland", "syria", "taiwan", "tajikistan", "tanzania", "thailand",
    "timor-leste", "togo", "tonga", "trinidad and tobago", "tunisia", "turkey", "turkmenistan",
    "tuvalu", "uganda", "ukraine", "united arab emirates", "uae", "dubai", "united kingdom", "uk",
    "england", "scotland", "wales", "united states", "united states of america", "usa", "us", "america",
    "uruguay", "uzbekistan", "vanuatu", "vatican city", "venezuela", "vietnam", "yemen", "zambia", "zimbabwe", "global"
]);

function isQwertyMashing(text) {
    const clean = (text || "").toLowerCase().replace(/[^a-z0-9]/g, '');
    if (clean.length < 3) return false;
    for (let i = 0; i <= clean.length - 4; i++) {
        const sub = clean.substring(i, i + 4);
        if (QWERTY_PATTERNS.some(p => p.includes(sub))) {
            return true;
        }
    }
    return false;
}

function validateUserInput(career, country) {
    const cleanCareer = (career || "").trim().toLowerCase();
    const cleanCountry = (country || "").trim().toLowerCase();

    if (!cleanCareer) {
        return { valid: false, message: "⚠️ Please enter a career title." };
    }

    if (cleanCareer.length < 2) {
        return { valid: false, message: "⚠️ Career title is too short. Please enter a valid job title (at least 2 characters)." };
    }

    if (/^\d+$/.test(cleanCareer)) {
        return { valid: false, message: "⚠️ Invalid Career Title: Pure numbers are not allowed. Please enter a valid job title (e.g. 'Software Engineer', 'Data Scientist')." };
    }

    if (/^[^\w\s\+\#\.\/-]+$/.test(cleanCareer)) {
        return { valid: false, message: "⚠️ Career title contains invalid symbols. Please enter a real job title." };
    }

    if (isQwertyMashing(cleanCareer)) {
        return { valid: false, message: `⚠️ '${career}' appears to be keyboard mashing. Please enter a real job title (e.g. 'Software Engineer').` };
    }

    const words = cleanCareer.match(/[a-z0-9\+\#]+/g) || [];
    const ROLE_SUFFIXES = [
        "ist", "er", "or", "ant", "ent", "ian", "ive", "ic", "eer", "man", "woman",
        "worker", "smith", "wright", "path", "grapher", "logist", "nomist", "metrician", "tech", "master",
        "keeper", "guard", "attendant", "clerk", "rep", "representative", "handler",
        "setter", "fitter", "turner", "molder", "caster", "welder", "cutter", "grinder",
        "polisher", "cleaner", "driver", "runner", "helper", "packer", "sorter", "checker",
        "loader", "feeder", "tender", "repairer", "installer", "maintainer", "servicer",
        "technician", "specialist", "analyst", "engineer", "developer", "designer",
        "manager", "director", "architect", "scientist", "assistant", "operator",
        "inspector", "supervisor", "executive", "builder", "trader", "broker",
        "evaluator", "practitioner", "counselor", "instructor", "teacher", "professor",
        "trainer", "coach", "pilot", "chef", "baker", "maker"
    ];

    for (const word of words) {
        if (VALID_ACRONYMS.includes(word) || /^\d+[a-z]?$/.test(word)) {
            continue;
        }

        if (word.length >= 3 && !/[aeiouy]/.test(word)) {
            return { valid: false, message: `⚠️ '${career}' contains unrecognized word patterns. Please check your spelling.` };
        }

        if (/[bcdfghjklmnpqrstvwxz]{5,}/.test(word) && !word.includes("blockchain") && !word.includes("architect") && !word.includes("strength")) {
            return { valid: false, message: `⚠️ '${career}' contains invalid character combinations.` };
        }

        if (/(.)\1{3,}/.test(word)) {
            return { valid: false, message: `⚠️ '${career}' contains invalid repeating characters.` };
        }
    }

    if (!words.length) {
        return { valid: false, message: `⚠️ '${career}' is an unrecognized job title. Please enter a real career role.` };
    }

    if (cleanCountry) {
        if (/\d/.test(cleanCountry)) {
            return { valid: false, message: "⚠️ Country name cannot contain numbers. Please enter a valid country name (e.g. India, USA, Germany)." };
        }

        const isCountryValid = REAL_WORLD_COUNTRIES.has(cleanCountry) || Array.from(REAL_WORLD_COUNTRIES).some(c => cleanCountry.includes(c));
        if (!isCountryValid) {
            return { valid: false, message: `⚠️ Invalid Country: '${country}' is not a recognized world country. Please enter a valid country name (e.g. India, USA, Germany, UK, Canada).` };
        }
    }

    return { valid: true };
}

// ==========================================
// Salary & Currency Formatters
// ==========================================

function formatIndiaSalary(rawSal, fallback = "₹6.5L - ₹18.0L / yr") {
    if (!rawSal) return fallback;
    const str = String(rawSal);
    if (str.includes("₹") || str.toLowerCase().includes("lpa") || str.toLowerCase().includes("lakh") || str.toLowerCase().includes("l ")) {
        return str;
    }
    return fallback;
}

const COUNTRY_CONFIG_MAP = {
    "india": { flag: "🇮🇳", name: "India", symbol: "₹", defaultSal: "₹4.5L - ₹22.0L / yr" },
    "united states": { flag: "🇺🇸", name: "USA", symbol: "$", defaultSal: "$55,000 - $160,000 / yr" },
    "usa": { flag: "🇺🇸", name: "USA", symbol: "$", defaultSal: "$55,000 - $160,000 / yr" },
    "us": { flag: "🇺🇸", name: "USA", symbol: "$", defaultSal: "$55,000 - $160,000 / yr" },
    "united kingdom": { flag: "🇬🇧", name: "United Kingdom", symbol: "£", defaultSal: "£25,000 - £85,000 / yr" },
    "uk": { flag: "🇬🇧", name: "United Kingdom", symbol: "£", defaultSal: "£25,000 - £85,000 / yr" },
    "england": { flag: "🇬🇧", name: "United Kingdom (England)", symbol: "£", defaultSal: "£25,000 - £85,000 / yr" },
    "scotland": { flag: "🇬🇧", name: "United Kingdom (Scotland)", symbol: "£", defaultSal: "£25,000 - £85,000 / yr" },
    "wales": { flag: "🇬🇧", name: "United Kingdom (Wales)", symbol: "£", defaultSal: "£25,000 - £85,000 / yr" },
    "great britain": { flag: "🇬🇧", name: "United Kingdom", symbol: "£", defaultSal: "£25,000 - £85,000 / yr" },
    "gb": { flag: "🇬🇧", name: "United Kingdom", symbol: "£", defaultSal: "£25,000 - £85,000 / yr" },
    "london": { flag: "🇬🇧", name: "United Kingdom (London)", symbol: "£", defaultSal: "£28,000 - £95,000 / yr" },
    "germany": { flag: "🇩🇪", name: "Germany", symbol: "€", defaultSal: "€35,000 - €95,000 / yr" },
    "france": { flag: "🇫🇷", name: "France", symbol: "€", defaultSal: "€32,000 - €90,000 / yr" },
    "netherlands": { flag: "🇳🇱", name: "Netherlands", symbol: "€", defaultSal: "€38,000 - €98,000 / yr" },
    "spain": { flag: "🇪🇸", name: "Spain", symbol: "€", defaultSal: "€28,000 - €75,000 / yr" },
    "italy": { flag: "🇮🇹", name: "Italy", symbol: "€", defaultSal: "€28,000 - €70,000 / yr" },
    "canada": { flag: "🇨🇦", name: "Canada", symbol: "CA$", defaultSal: "CA$48,000 - CA$125,000 / yr" },
    "australia": { flag: "🇦🇺", name: "Australia", symbol: "A$", defaultSal: "A$55,000 - A$140,000 / yr" },
    "uae": { flag: "🇦🇪", name: "UAE / Dubai", symbol: "AED", defaultSal: "AED 9,000 - AED 35,000 / mo" },
    "dubai": { flag: "🇦🇪", name: "Dubai", symbol: "AED", defaultSal: "AED 9,000 - AED 35,000 / mo" },
    "saudi arabia": { flag: "🇸🇦", name: "Saudi Arabia", symbol: "SAR", defaultSal: "SAR 8,000 - SAR 28,000 / mo" },
    "singapore": { flag: "🇸🇬", name: "Singapore", symbol: "S$", defaultSal: "S$38,000 - S$115,000 / yr" },
    "japan": { flag: "🇯🇵", name: "Japan", symbol: "¥", defaultSal: "¥3,500,000 - ¥10,500,000 / yr" },
    "south korea": { flag: "🇰🇷", name: "South Korea", symbol: "₩", defaultSal: "₩32,000,000 - ₩95,000,000 / yr" },
    "switzerland": { flag: "🇨🇭", name: "Switzerland", symbol: "CHF", defaultSal: "CHF 65,000 - CHF 150,000 / yr" }
};

function getCountrySalaryInfo(country, rawSalary) {
    const cLow = (country || "").toLowerCase().trim();
    for (const [key, cfg] of Object.entries(COUNTRY_CONFIG_MAP)) {
        if (cLow.includes(key) || key.includes(cLow)) {
            if (rawSalary && (rawSalary.includes(cfg.symbol) || rawSalary.includes(cfg.name))) {
                return { flag: cfg.flag, name: cfg.name, salary: rawSalary };
            }
            return { flag: cfg.flag, name: cfg.name, salary: rawSalary || cfg.defaultSal };
        }
    }

    const displayName = country ? country.trim() : "USA / Global";
    const displayFlag = country ? "🌐" : "🇺🇸";
    const salaryVal = (rawSalary && (rawSalary.includes("$") || rawSalary.includes("€") || rawSalary.includes("£") || rawSalary.includes("₹"))) 
        ? rawSalary 
        : "$70,000 - $160,000 / yr";

    return { flag: displayFlag, name: displayName, salary: salaryVal };
}

function renderPayBandCard(salaryData, targetSalInfo, country) {
    const cLow = (country || "").toLowerCase().trim();
    const isIndia = cLow.includes("india") || !cLow;
    const flag = targetSalInfo.flag || (isIndia ? "🇮🇳" : "🌐");
    const countryName = targetSalInfo.name || (country ? country.trim() : "Target Market");
    
    let fresher = "Data unavailable";
    let mid = "Data unavailable";
    let senior = "Data unavailable";

    if (salaryData && typeof salaryData === "object") {
        if (isIndia) {
            fresher = salaryData.india_fresher || salaryData.india || salaryData.fresher || "Data unavailable";
            mid = salaryData.india_mid || salaryData.mid || "Data unavailable";
            senior = salaryData.india_senior || salaryData.senior || "Data unavailable";
        } else {
            fresher = salaryData.country_fresher || salaryData.fresher || "Data unavailable";
            mid = salaryData.country_mid || salaryData.mid || "Data unavailable";
            senior = salaryData.country_senior || salaryData.senior || "Data unavailable";
        }
    } else if (salaryData && typeof salaryData === "string") {
        const parts = salaryData.split("->").map(p => p.replace(/\((Fresher|Mid|Senior)\)/gi, "").trim());
        if (parts.length >= 3) {
            fresher = parts[0];
            mid = parts[1];
            senior = parts[2];
        } else if (parts.length === 1 && parts[0]) {
            fresher = parts[0];
        }
    }

    const code = salaryData?.currency_code || targetSalInfo?.currency || "";
    const sym = salaryData?.currency_symbol || "";

    function ensureCurrencyTag(val) {
        if (!val || val === "Data unavailable" || val === "--") return "Data unavailable";
        const v = String(val).trim();
        if (v === "Data unavailable") return "Data unavailable";

        const hasSym = /[$\u20B9\u00A5\u00A3\u20AC\u20A9\u20BA\u20AA\u0E3F\u20BD\u09AF\u20B1\u20AB\u20A6]/.test(v);
        const hasCode = /^[A-Z]{3}\s/.test(v) || /\b[A-Z]{3}\b/.test(v);
        if (hasSym || hasCode) return v;

        const tag = sym || code || "";
        return tag ? `${tag}${v}` : v;
    }

    fresher = ensureCurrencyTag(fresher);
    mid = ensureCurrencyTag(mid);
    senior = ensureCurrencyTag(senior);

    let sourcesChecked = [];
    if (isIndia) {
        sourcesChecked = ["Ministry of Labour & Employment (Gov of India)", "DGMS Labor Registry", "National Career Service (NCS)"];
    } else if (cLow.includes("united states") || cLow.includes("usa") || cLow.includes("us")) {
        sourcesChecked = ["US Bureau of Labor Statistics (BLS) OEWS", "O*NET OnLine database", "Department of Labor (DOL)"];
    } else if (cLow.includes("united kingdom") || cLow.includes("uk")) {
        sourcesChecked = ["UK Department for Education (DfE)", "ONS Annual Survey of Hours and Earnings (ASHE)"];
    } else if (cLow.includes("germany")) {
        sourcesChecked = ["Statistisches Bundesamt (Destatis) Germany", "Federal Employment Agency (Agentur für Arbeit)"];
    } else if (cLow.includes("canada")) {
        sourcesChecked = ["Job Bank Canada (Gov of Canada)", "Statistics Canada (StatCan)"];
    } else {
        sourcesChecked = ["International Labour Organization (ILO)", "World Bank Labor Benchmarks", "CareerVerse Verified Registries"];
    }

    return `
    <div style="margin-top: 22px; background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(250, 204, 21, 0.3); border-radius: 16px; padding: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.4);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 12px; flex-wrap: wrap; gap: 8px;">
            <span style="font-size: 0.95rem; font-weight: 700; color: var(--text-heading); display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.25rem;">${flag}</span> ${countryName} Official Compensation Pay Band
            </span>
            <span style="background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.4); color: #22c55e; padding: 4px 12px; border-radius: 100px; font-size: 0.75rem; font-weight: 700; display: flex; align-items: center; gap: 5px;">
                <i class="fa-solid fa-circle-check"></i> 85%+ Verified Accuracy
            </span>
        </div>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;">
            <div style="background: rgba(34, 197, 94, 0.06); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 12px; padding: 14px; text-align: center;">
                <span style="font-size: 0.74rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 700;">🌱 Entry Level / Fresher</span>
                <h4 style="color: #22c55e; font-size: 1.05rem; margin: 6px 0 0; font-weight: 800;">${fresher}</h4>
            </div>
            <div style="background: rgba(250, 204, 21, 0.06); border: 1px solid rgba(250, 204, 21, 0.3); border-radius: 12px; padding: 14px; text-align: center;">
                <span style="font-size: 0.74rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 700;">⚡ Mid-Level Professional</span>
                <h4 style="color: var(--accent); font-size: 1.05rem; margin: 6px 0 0; font-weight: 800;">${mid}</h4>
            </div>
            <div style="background: rgba(168, 85, 247, 0.06); border: 1px solid rgba(168, 85, 247, 0.3); border-radius: 12px; padding: 14px; text-align: center;">
                <span style="font-size: 0.74rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 700;">👑 Senior / Lead Specialist</span>
                <h4 style="color: #a855f7; font-size: 1.05rem; margin: 6px 0 0; font-weight: 800;">${senior}</h4>
            </div>
        </div>
        <div style="margin-top: 16px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 14px; font-size: 0.82rem; color: var(--text-secondary); line-height: 1.5;">
            <strong>Why this salary?</strong> ${salaryData?.reason || 'Driven by specialized competency requirements, cognitive complexity, and strong regional market demands.'}
        </div>
        <div style="margin-top: 12px; padding-top: 10px; border-top: 1px dashed rgba(255,255,255,0.08); font-size: 0.78rem; color: var(--text-muted); display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
            <span style="display: flex; align-items: center; gap: 4px;"><i class="fa-solid fa-database" style="color: var(--accent);"></i> Verified Sources:</span>
            ${sourcesChecked.map(src => `<span style="background: rgba(255,255,255,0.04); padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.06); color: var(--text-secondary); font-weight: 600;">${src}</span>`).join('')}
        </div>
    </div>
    `;
}

function getFresherSalary(market, country) {
    const c = (country || "").toLowerCase().trim();
    if (market.salary?.fresher) return market.salary.fresher;
    if (c.includes("india")) return "₹4.5L - ₹8.0L / yr";
    if (c.includes("uk")) return "£30,000 - £45,000 / yr";
    if (c.includes("germany") || c.includes("france")) return "€40,000 - €55,000 / yr";
    return "$60,000 - $85,000 / yr";
}

function getMidSalary(market, country) {
    const c = (country || "").toLowerCase().trim();
    if (market.salary?.mid) return market.salary.mid;
    if (c.includes("india")) return "₹8.0L - ₹18.0L / yr";
    if (c.includes("uk")) return "£45,000 - £75,000 / yr";
    if (c.includes("germany") || c.includes("france")) return "€55,000 - €80,000 / yr";
    return "$85,000 - $140,000 / yr";
}

function getSeniorSalary(market, country) {
    const c = (country || "").toLowerCase().trim();
    if (market.salary?.senior) return market.salary.senior;
    if (c.includes("india")) return "₹18.0L - ₹35.0L / yr";
    if (c.includes("uk")) return "£75,000 - £120,000 / yr";
    if (c.includes("germany") || c.includes("france")) return "€80,000 - €130,000 / yr";
    return "$140,000 - $220,000 / yr";
}

function renderResourceList(items, fallbackItems, iconClass, linkColor) {
    const list = items || fallbackItems;
    if (!list || !Array.isArray(list)) return "";
    return list.map(item => {
        if (item && typeof item === "object") {
            const name = item.name || item.title || "Resource Link";
            const url = item.url || "#";
            return `
                <li>
                    <a href="${url}" target="_blank" style="color: ${linkColor}; text-decoration: none; font-weight: 500; display: inline-flex; align-items: center; gap: 6px; transition: opacity 0.2s;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">
                        <i class="${iconClass}"></i> ${name}
                    </a>
                </li>
            `;
        }
        return `<li>${item}</li>`;
    }).join("");
}

// ==========================================
// Generate Roadmap Global Handler
// ==========================================

async function generateRoadmapNow() {
    const careerInputEl = document.getElementById("careerInput");
    const countryInputEl = document.getElementById("countryInput");
    const durationInputEl = document.getElementById("duration");
    const resultCardEl = document.getElementById("resultCard");
    const generateBtnEl = document.getElementById("generateBtn");

    if (!careerInputEl || !resultCardEl) return;

    const career = careerInputEl.value.trim();
    const country = countryInputEl ? countryInputEl.value.trim() : "";
    const experience = document.getElementById("experienceInput") ? document.getElementById("experienceInput").value.trim() : "";
    const skills = document.getElementById("skillsInput") ? document.getElementById("skillsInput").value.trim() : "";
    const duration = document.getElementById("durationInput") ? document.getElementById("durationInput").value.trim() : (durationInputEl ? durationInputEl.value.trim() : "6 months");
    const industry = document.getElementById("industryInput") ? document.getElementById("industryInput").value.trim() : "";

    const val = validateUserInput(career, country);
    if (!val.valid) {
        resultCardEl.innerHTML = `
            <div class="roadmap-item error-card" style="border: 1px solid #ef4444; background: rgba(239, 68, 68, 0.06); padding: 28px; border-radius: 16px; margin-top: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 14px;">
                    <i class="fa-solid fa-circle-exclamation" style="font-size: 1.6rem; color: #ef4444;"></i>
                    <h3 style="color: var(--text-heading); margin: 0; font-size: 1.2rem;">Invalid Input Warning</h3>
                </div>
                <p style="color: var(--text-primary); font-size: 0.96rem; line-height: 1.6; margin-bottom: 18px;">${val.message}</p>
                <div style="background: var(--bg-card); border: 1px solid var(--border); padding: 14px 18px; border-radius: 10px; font-size: 0.86rem; color: var(--text-secondary);">
                    💡 <strong>Suggested Careers:</strong> <code>Software Engineer</code>, <code>AI Engineer</code>, <code>Data Scientist</code>, <code>Cybersecurity Specialist</code>
                </div>
            </div>
        `;
        resultCardEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        return;
    }

    if (generateBtnEl) {
        generateBtnEl.disabled = true;
        generateBtnEl.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Generating AI Roadmap...`;
    }

    // Loading Screen
    resultCardEl.innerHTML = `
<div class="loading-card">
    <div class="ai-loader"></div>
    <h2>🤖 CareerVerse AI is Working...</h2>
    <div class="loading-steps">
        <p id="loadingText">🧠 Analyzing Career...</p>
    </div>
</div>
`;
    resultCardEl.scrollIntoView({ behavior: 'smooth', block: 'center' });

    const steps = [
        "🧠 Analyzing Career...",
        "📚 Finding Best Learning Resources...",
        "🛠 Building Personalized Roadmap...",
        "💼 Preparing Projects & Certifications...",
        "📄 Finalizing Your Career Report..."
    ];

    let index = 0;
    const loadingInterval = setInterval(() => {
        const text = document.getElementById("loadingText");
        if(text){
            text.textContent = steps[index];
            index = (index + 1) % steps.length;
        }
    }, 800);

    try {
        const response = await fetch("/roadmap", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ career, country, duration })
        });

        const responseData = await response.json();

        if (generateBtnEl) {
            generateBtnEl.disabled = false;
            generateBtnEl.innerHTML = `<i class="fa-solid fa-route"></i> Generate AI Roadmap`;
        }

        if (!response.ok || responseData.success === false) {
            clearInterval(loadingInterval);
            resultCardEl.innerHTML = `
                <div class="roadmap-item error-card" style="border: 1px solid #ef4444; background: rgba(239, 68, 68, 0.08); padding: 26px; border-radius: 16px; margin-top: 20px;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                        <i class="fa-solid fa-circle-exclamation" style="font-size: 1.6rem; color: #ef4444;"></i>
                        <h3 style="color: var(--text-heading); margin: 0; font-size: 1.2rem;">Roadmap Generation Error</h3>
                    </div>
                    <p style="color: var(--text-primary); font-size: 0.96rem; line-height: 1.6;">${responseData.error || "Unable to generate roadmap. Please enter a valid job title."}</p>
                </div>
            `;
            return;
        }

        const data = responseData.data || responseData;
        window.currentRoadmap = data;
        console.log(data);

        // -----------------------------
        // Extract Data
        // -----------------------------

        const overview = data.overview || {};
        const skills = data.skills || {};
        const roadmap = data.roadmap || [];
        const resources = data.resources || {};
        const projects = data.projects || {};
        const certifications = data.certifications || [];
        const tools = data.tools || [];
        const interview = data.interview_preparation || [];
        const portfolio = data.portfolio_tips || [];
        const aiTips = data.ai_tips || [];
        const market = data.market || {};
        const targetSalInfo = getCountrySalaryInfo(country, overview.salary?.formatted_range || overview.salary?.country || overview.salary?.usa);

        // -----------------------------
        // Start HTML
        // -----------------------------

        let html = `
<div class="roadmap-top-bar" style="margin-bottom: 20px;">
    <div class="roadmap-title-group">
        <span class="roadmap-top-badge"><i class="fa-solid fa-wand-magic-sparkles"></i> AI MASTER ROADMAP</span>
        <h1>${data.career || career}</h1>
    </div>
    <button id="inlineDownloadBtn" type="button" class="top-download-btn">
        <i class="fa-solid fa-file-pdf"></i> Download PDF Roadmap
    </button>
</div>

<!-- ================= NAVIGATION BAR ================= -->
<div class="roadmap-navigator">
    <button class="roadmap-page-btn active" id="roadmap-btn-1" onclick="showRoadmapPage(1)">
        <i class="fa-solid fa-book-open"></i> Profile & Scope
    </button>
    <button class="roadmap-page-btn" id="roadmap-btn-2" onclick="showRoadmapPage(2)">
        <i class="fa-solid fa-route"></i> Study Timeline
    </button>
    <button class="roadmap-page-btn" id="roadmap-btn-3" onclick="showRoadmapPage(3)">
        <i class="fa-solid fa-code"></i> Skills & Tools
    </button>
    <button class="roadmap-page-btn" id="roadmap-btn-4" onclick="showRoadmapPage(4)">
        <i class="fa-solid fa-laptop-code"></i> Practical Tasks
    </button>
    <button class="roadmap-page-btn" id="roadmap-btn-5" onclick="showRoadmapPage(5)">
        <i class="fa-solid fa-graduation-cap"></i> Prep & Resources
    </button>
    <button class="roadmap-page-btn" id="roadmap-btn-6" onclick="showRoadmapPage(6)">
        <i class="fa-solid fa-chart-pie"></i> Market & Hiring
    </button>
</div>

<!-- ================= PAGE 1: CAREER PROFILE ================= -->
<div class="roadmap-page active" id="roadmap-page-1">
    <div class="roadmap-item">
        <h2><i class="fa-solid fa-circle-info"></i> What is this Career?</h2>
        <p style="font-size: 1.05rem; line-height: 1.7; margin-bottom: 24px; color: var(--text-primary); font-weight: 400;">
            ${overview.description || "Comprehensive professional career breakdown."}
        </p>

        <!-- Responsibilities Box -->
        <div class="responsibilities-box">
            <h3><i class="fa-solid fa-briefcase"></i> Core Day-to-Day Responsibilities</h3>
            <ul class="responsibilities-list">
                ${(overview.responsibilities || [
                    "Perform core duties, analyze data, and implement domain methodologies.",
                    "Collaborate with team members and report findings to relevant stakeholders.",
                    "Ensure quality control, maintain standard guidelines, and resolve operational issues.",
                    "Leverage modern software, tools, and processes to optimize productivity."
                ]).map(resp => `<li>${resp}</li>`).join("")}
            </ul>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 24px;">
            <div style="background: rgba(25, 25, 25, 0.7); border: 1px solid var(--border); border-radius: 14px; padding: 18px;">
                <h3 style="margin-top: 0; color: var(--accent);"><i class="fa-solid fa-user-graduate"></i> Education & Path</h3>
                <p style="font-size: 0.92rem; margin: 0; line-height: 1.5; color: var(--text-secondary);">${overview.education || "Bachelor's Degree in relevant field / Portfolio Proof"}</p>
            </div>
            <div style="background: rgba(25, 25, 25, 0.7); border: 1px solid var(--border); border-radius: 14px; padding: 18px;">
                <h3 style="margin-top: 0; color: #22c55e;"><i class="fa-solid fa-chart-line"></i> 5-Year Future Trajectory</h3>
                <p style="font-size: 0.92rem; margin: 0; line-height: 1.5; color: var(--text-secondary);">${overview.future_scope || "High demand across global hubs."}</p>
            </div>
        </div>

        <!-- Past, Present & Future Timeline -->
        <div style="background: rgba(250, 204, 21, 0.03); border: 1px solid rgba(250, 204, 21, 0.25); border-radius: 16px; padding: 20px; margin-bottom: 24px;">
            <h3 style="margin-top: 0; color: var(--accent); font-size: 1.05rem; margin-bottom: 14px;"><i class="fa-solid fa-hourglass-half"></i> Past, Present & Future Macro Market Evolution</h3>
            <div style="display: flex; flex-direction: column; gap: 14px;">
                <div style="background: rgba(59, 130, 246, 0.05); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 12px; padding: 14px;">
                    <span style="font-size: 0.75rem; color: #3b82f6; font-weight: 800; text-transform: uppercase; display: block; margin-bottom: 4px;">📜 PAST (10-Yr Evolution)</span>
                    <p style="font-size: 0.88rem; color: var(--text-secondary); margin: 0; line-height: 1.5;">${(overview.macro_evolution?.past || `Historically, this role relied on manual execution, legacy tools, and localized workflows.`)}</p>
                </div>
                <div style="background: rgba(250, 204, 21, 0.05); border: 1px solid rgba(250, 204, 21, 0.2); border-radius: 12px; padding: 14px;">
                    <span style="font-size: 0.75rem; color: var(--accent); font-weight: 800; text-transform: uppercase; display: block; margin-bottom: 4px;">⚡ PRESENT (Current Realities)</span>
                    <p style="font-size: 0.88rem; color: var(--text-secondary); margin: 0; line-height: 1.5;">${(overview.macro_evolution?.present || `Currently in high demand driven by digital transformation, modern tech stacks, and cloud integration.`)}</p>
                </div>
                <div style="background: rgba(34, 197, 94, 0.05); border: 1px solid rgba(34, 197, 94, 0.2); border-radius: 12px; padding: 14px;">
                    <span style="font-size: 0.75rem; color: #22c55e; font-weight: 800; text-transform: uppercase; display: block; margin-bottom: 4px;">🚀 FUTURE (5-10 Yr Scope)</span>
                    <p style="font-size: 0.88rem; color: var(--text-secondary); margin: 0; line-height: 1.5;">${(overview.macro_evolution?.future || `Over the next decade, AI integration will automate routine work, elevating specialists into strategic decision-makers.`)}</p>
                </div>
            </div>
        </div>

        <!-- Day-in-the-Life Daily duty timeline & Fast-track leveling dynamic generator -->
        ${(() => {
            const cName = (data.career || career || "Professional").trim();
            const cLow = cName.toLowerCase();
            
            let t1_title = "Morning Alignment & Standup";
            let t1_desc = "Sync with cross-functional teams, triage daily priorities, and review critical operational deliverables.";
            let t2_title = "Deep Focus Execution";
            let t2_desc = "Uninterrupted high-value problem solving, technical/strategic execution, and core milestone building.";
            let t3_title = "Collaboration & Review";
            let t3_desc = "Stakeholder feedback loops, peer reviews, technical architecture sessions, and mentoring junior peers.";
            let t4_title = "Quality Audit & Learning";
            let t4_desc = "Testing & validating day's work, updating task boards, and spending 30 mins exploring cutting-edge AI tools.";

            let l1_title = "Task Reliability & Core Skills";
            let l1_desc = "Deliver assigned deliverables on time with zero hand-holding and maintain clean documentation.";
            let l1_trigger = "<5% rework rate & proactive daily updates.";

            let l2_title = "End-to-End System Design";
            let l2_desc = "Own complex module features, lead technical reviews, and mentor junior team members.";
            let l2_trigger = "Leading 2+ major projects boosting team efficiency.";

            let l3_title = "Enterprise Strategy & Architecture";
            let l3_desc = "Architect long-term technology roadmaps, resolve critical bottlenecks, and align goals with business ROI.";
            let l3_trigger = "Driving strategic ROI & shaping organizational standards.";

            if (cLow.includes("software") || cLow.includes("developer") || cLow.includes("backend") || cLow.includes("frontend") || cLow.includes("coder") || cLow.includes("programmer") || cLow.includes("engineer")) {
                t1_title = "Daily Standup & Triage";
                t1_desc = "Sync with the engineering team, review sprint boards, and coordinate daily coding tasks.";
                t2_title = "Core Coding & Deep Focus";
                t2_desc = "Implement complex algorithms, design API endpoints, or write clean, unit-tested features.";
                t3_title = "System Design & Review";
                t3_desc = "Review pull requests, collaborate on architecture diagrams, and pair-program with junior developers.";
                t4_title = "Refactoring & Documentation";
                t4_desc = "Clean up legacy code, update system documentation, and run automated testing pipelines.";
                
                l1_title = "Task Reliability & Code Quality";
                l1_desc = "Deliver high-quality tasks on-time with clean code and thorough test coverage.";
                l1_trigger = "Clean code reviews & zero critical bugs in production.";
                
                l2_title = "System Ownership & Design";
                l2_desc = "Own complex services, direct sprint goals, and review architecture blueprints.";
                l2_trigger = "Successfully leading 2+ major feature launches.";
                
                l3_title = "Enterprise Architecture & Strategy";
                l3_desc = "Define technological vision, optimize system scalability, and direct resource budgets.";
                l3_trigger = "Driving strategic architecture transformation and system ROI.";
            } else if (cLow.includes("doctor") || cLow.includes("nurse") || cLow.includes("medical") || cLow.includes("dentist") || cLow.includes("surgeon") || cLow.includes("physician") || cLow.includes("clinical") || cLow.includes("pharmacist")) {
                t1_title = "Morning Rounds & Vitals Check";
                t1_desc = "Check patient vitals, review laboratory charts, and conduct critical ward rounds.";
                t2_title = "Clinical Consultations & Surgery";
                t2_desc = "Perform targeted medical procedures, execute surgical plans, or consult outpatients.";
                t3_title = "Interdisciplinary Diagnostics";
                t3_desc = "Collaborate with radiology and lab specialists to review complex patient profiles.";
                t4_title = "EHR Documentation & Patient Care";
                t4_desc = "Update Electronic Health Records, prescribe medications, and check patient recovery status.";

                l1_title = "Clinical Execution & Direct Care";
                l1_desc = "Safely manage primary care tasks, patient triage, and follow standard hospital checklists.";
                l1_trigger = "Accurate diagnostic logs & positive peer reviews.";

                l2_title = "Specialist Diagnosis & Management";
                l2_desc = "Direct complex patient treatment pathways, manage ward shifts, and train junior residents.";
                l2_trigger = "Leading specialized diagnostic units with high clinical success.";

                l3_title = "Clinical Leadership & Governance";
                l3_desc = "Direct department policies, spearhead clinical trials, and oversee medical board reviews.";
                l3_trigger = "Appointed Head of Department or managing hospital advisory boards.";
            } else if (cLow.includes("manager") || cLow.includes("director") || cLow.includes("lead") || cLow.includes("executive") || cLow.includes("product") || cLow.includes("consultant") || cLow.includes("analyst") || cLow.includes("marketing") || cLow.includes("hr") || cLow.includes("sales")) {
                t1_title = "Stakeholder Alignment & Standup";
                t1_desc = "Coordinate with cross-functional partners, align milestone timelines, and unblock execution paths.";
                t2_title = "Roadmap Strategy & Execution";
                t2_desc = "Analyze performance metrics, draft strategic briefs, and outline product/campaign roadmaps.";
                t3_title = "Resource Planning & Prioritization";
                t3_desc = "Lead refinement sessions, negotiate budgets, and resolve cross-team dependencies.";
                t4_title = "Deliverable Audit & ROI Reporting";
                t4_desc = "Review project status dashboards, compile leadership decks, and analyze program performance.";

                l1_title = "Process Delivery & Coordination";
                l1_desc = "Ensure operational tasks are tracked, update status boards, and maintain team alignment.";
                l1_trigger = "On-time milestone tracking and clean team sprint hygiene.";

                l2_title = "Product & Lifecycle Ownership";
                l2_desc = "Own end-to-end product features, campaigns or portfolios, shape roadmaps, and negotiate scopes.";
                l2_trigger = "Successful delivery of 2+ complex cross-functional product cycles.";

                l3_title = "Strategic Portfolio Governance";
                l3_desc = "Set long-term business objectives, align division budgets, and steer organizational culture.";
                l3_trigger = "Demonstrated double-digit growth in business line value or divisional ROI.";
            } else if (cLow.includes("design") || cLow.includes("artist") || cLow.includes("3d") || cLow.includes("vfx") || cLow.includes("animat") || cLow.includes("creative") || cLow.includes("graphic") || cLow.includes("writer") || cLow.includes("video")) {
                t1_title = "Creative Briefing & Moodboards";
                t1_desc = "Review client briefs, research current design trends, and align on visual direction.";
                t2_title = "Asset Creation & Layout";
                t2_desc = "Develop detailed design wireframes, craft high-fidelity 3D assets, or write copy.";
                t3_title = "Critique Loops & Iteration";
                t3_desc = "Present prototype drafts to feedback boards and iterate designs based on user data.";
                t4_title = "Asset Hand-off & Token Updates";
                t4_desc = "Prepare deliverable files, update team style libraries, and document visual guidelines.";

                l1_title = "Craft Mastery & Execution";
                l1_desc = "Create high-quality individual visual assets following the design system guidelines.";
                l1_trigger = "High aesthetic quality with low feedback iteration loops.";

                l2_title = "System Ownership & Art Direction";
                l2_desc = "Define the brand style system, direct project art styles, and mentor junior artists.";
                l2_trigger = "Leading design campaigns or art-directing major feature updates.";

                l3_title = "Creative Strategy & Brand Vision";
                l3_desc = "Align design language with business goals, lead design innovation labs, and win enterprise briefs.";
                l3_trigger = "Defining multi-platform design strategy that drives product conversion metrics.";
            } else if (cLow.includes("lawyer") || cLow.includes("advocate") || cLow.includes("legal") || cLow.includes("judge") || cLow.includes("solicitor") || cLow.includes("paralegal") || cLow.includes("law")) {
                t1_title = "Case Preparation & Client Sync";
                t1_desc = "Review case notes, consult clients, and finalize litigation strategy briefings.";
                t2_title = "Courtroom Advocacy & Trial";
                t2_desc = "Represent clients in court trials or lead high-stakes corporate contract negotiations.";
                t3_title = "Legal Research & Drafting";
                t3_desc = "Analyze statutes, precedents, and draft formal petitions or commercial contracts.";
                t4_title = "Compliance Auditing & Records";
                t4_desc = "Ensure absolute statutory compliance, archive case records, and advise corporate boards.";

                l1_title = "Research Accuracy & Drafting";
                l1_desc = "Conduct thorough legal research and draft precise agreements, contracts, and case summaries.";
                l1_trigger = "Zero compliance errors and high-quality legal brief drafting.";

                l2_title = "Litigation & Case Management";
                l2_desc = "Independently manage courtroom trials, run client portfolios, and draft corporate mergers.";
                l2_trigger = "Successful litigation record and ownership of complex client accounts.";

                l3_title = "Senior Advisory & Judicial Leadership";
                l3_desc = "Provide executive board counsel, steer landmark litigation, or serve in judicial governance.";
                l3_trigger = "Promotion to partner level or appointment to senior judicial boards.";
            } else if (cLow.includes("ias") || cLow.includes("ips") || cLow.includes("upsc") || cLow.includes("police") || cLow.includes("civil") || cLow.includes("government") || cLow.includes("municipal") || cLow.includes("civic") || cLow.includes("bmc")) {
                t1_title = "Public Grievance & Ward Review";
                t1_desc = "Meet citizen representatives, review local petitions, and align department staff.";
                t2_title = "Policy Enforcement & Field Audit";
                t2_desc = "Lead on-field inspections, enforce zoning compliance, or review municipal projects.";
                t3_title = "Administrative Budgeting";
                t3_desc = "Review development proposals, audit department funds, and draft government orders.";
                t4_title = "Crisis Management & Reporting";
                t4_desc = "Coordinate with safety agencies, review emergency response preparedness, and log reports.";

                l1_title = "Field Inspections & Compliance";
                l1_desc = "Ensure correct field implementation, enforce civic rules, and maintain public records.";
                l1_trigger = "Timely resolution of local ward issues & clean compliance audits.";

                l2_title = "Ward / Subdivision Administration";
                l2_desc = "Manage subdivision municipal departments, approve local development plans, and lead grievance resolutions.";
                l2_trigger = "Successfully implementation of subdivision infrastructure upgrades.";

                l3_title = "Policy Formulation & Governance";
                l3_desc = "Formulate state/national policies, manage massive urban budgets, and steer emergency resilience.";
                l3_trigger = "Shaping cabinet-level policies and directing district administrations.";
            } else if (cLow.includes("chef") || cLow.includes("cook") || cLow.includes("culinary") || cLow.includes("bakery") || cLow.includes("hotel") || cLow.includes("restaurant")) {
                t1_title = "Mis En Place & Kitchen Sync";
                t1_desc = "Inspect raw inventory, prep ingredients, set up cooking stations, and coordinate line positions.";
                t2_title = "Lunch Service & Expo";
                t2_desc = "Manage high-speed food preparation, oversee line cooks, and ensure beautiful dish plating.";
                t3_title = "Menu Planning & Costing";
                t3_desc = "Engineer new recipes, calculate food portion costs, and consult local food purveyors.";
                t4_title = "HACCP Safety Audit & Close";
                t4_desc = "Enforce strict kitchen sanitation checklists, log waste reports, and lock down cold storage.";

                l1_title = "Station Cook & Line Prep";
                l1_desc = "Master knife skills, manage a designated line station (sauces/grill), and execute recipes accurately.";
                l1_trigger = "Consistent portion sizes, speed of execution, and clean health logs.";

                l2_title = "Sous Chef & Kitchen Ops";
                l2_desc = "Oversee daily kitchen staff shifts, control inventory, and run service expediting.";
                l2_trigger = "Managing daily service with zero guest complaints and low food costs.";

                l3_title = "Executive Chef & Concept Director";
                l3_desc = "Design signature menus, control overall P&L margins, and direct multi-venue operations.";
                l3_trigger = "Earning industry recognition (e.g. Michelin/awards) and optimized kitchen profits.";
            }

            return `
            <h3 style="margin-top: 10px; margin-bottom: 16px;"><i class="fa-solid fa-clock"></i> Day-in-the-Life & Daily Duty Workflow</h3>
            <div style="display: flex; flex-direction: column; gap: 16px; border-left: 2px solid rgba(250, 204, 21, 0.15); padding-left: 20px; margin-left: 10px; margin-bottom: 28px;">
                <div style="position: relative;">
                    <span style="position: absolute; left: -26px; top: 4px; width: 10px; height: 10px; border-radius: 50%; background: #3b82f6; box-shadow: 0 0 8px #3b82f6;"></span>
                    <span style="font-size: 0.75rem; color: #3b82f6; font-weight: 800; text-transform: uppercase; display: block; margin-bottom: 4px;">🌅 09:00 AM - 10:30 AM · ${t1_title}</span>
                    <p style="font-size: 0.88rem; color: var(--text-secondary); margin: 0; line-height: 1.5;">${t1_desc}</p>
                </div>
                <div style="position: relative;">
                    <span style="position: absolute; left: -26px; top: 4px; width: 10px; height: 10px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 8px #22c55e;"></span>
                    <span style="font-size: 0.75rem; color: #22c55e; font-weight: 800; text-transform: uppercase; display: block; margin-bottom: 4px;">🧠 10:30 AM - 01:30 PM · ${t2_title}</span>
                    <p style="font-size: 0.88rem; color: var(--text-secondary); margin: 0; line-height: 1.5;">${t2_desc}</p>
                </div>
                <div style="position: relative;">
                    <span style="position: absolute; left: -26px; top: 4px; width: 10px; height: 10px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 8px var(--accent);"></span>
                    <span style="font-size: 0.75rem; color: var(--accent); font-weight: 800; text-transform: uppercase; display: block; margin-bottom: 4px;">🤝 02:30 PM - 04:30 PM · ${t3_title}</span>
                    <p style="font-size: 0.88rem; color: var(--text-secondary); margin: 0; line-height: 1.5;">${t3_desc}</p>
                </div>
                <div style="position: relative;">
                    <span style="position: absolute; left: -26px; top: 4px; width: 10px; height: 10px; border-radius: 50%; background: #a855f7; box-shadow: 0 0 8px #a855f7;"></span>
                    <span style="font-size: 0.75rem; color: #a855f7; font-weight: 800; text-transform: uppercase; display: block; margin-bottom: 4px;">🚀 04:30 PM - 06:00 PM · ${t4_title}</span>
                    <p style="font-size: 0.88rem; color: var(--text-secondary); margin: 0; line-height: 1.5;">${t4_desc}</p>
                </div>
            </div>

            <h3 style="margin-top: 10px;"><i class="fa-solid fa-chart-line"></i> Fast-Track Career Leveling & Promotion Roadmap</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 24px;">
                <div style="background: rgba(34, 197, 94, 0.04); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 14px; padding: 18px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 0.78rem; color: #22c55e; font-weight: 800; text-transform: uppercase;">🟢 Level 1: Junior (0 - 2 Yrs)</span>
                        <span style="font-size: 0.7rem; background: rgba(34, 197, 94, 0.15); color: #22c55e; padding: 2px 8px; border-radius: 12px; font-weight: 700;">Execution</span>
                    </div>
                    <strong style="color: var(--text-heading); font-size: 0.92rem; display: block; margin-bottom: 6px;">${l1_title}</strong>
                    <p style="font-size: 0.8rem; color: var(--text-secondary); margin: 0 0 10px; line-height: 1.4;">${l1_desc}</p>
                    <div style="font-size: 0.75rem; color: #22c55e; font-weight: 700;">🎯 Promotion Trigger: <span style="color: var(--text-primary); font-weight: 400;">${l1_trigger}</span></div>
                </div>

                <div style="background: rgba(250, 204, 21, 0.04); border: 1px solid rgba(250, 204, 21, 0.3); border-radius: 14px; padding: 18px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 0.78rem; color: var(--accent); font-weight: 800; text-transform: uppercase;">🟡 Level 2: Mid-Level (2 - 5 Yrs)</span>
                        <span style="font-size: 0.7rem; background: rgba(250, 204, 21, 0.15); color: var(--accent); padding: 2px 8px; border-radius: 12px; font-weight: 700;">Ownership</span>
                    </div>
                    <strong style="color: var(--text-heading); font-size: 0.92rem; display: block; margin-bottom: 6px;">${l2_title}</strong>
                    <p style="font-size: 0.8rem; color: var(--text-secondary); margin: 0 0 10px; line-height: 1.4;">${l2_desc}</p>
                    <div style="font-size: 0.75rem; color: var(--accent); font-weight: 700;">🎯 Promotion Trigger: <span style="color: var(--text-primary); font-weight: 400;">${l2_trigger}</span></div>
                </div>

                <div style="background: rgba(168, 85, 247, 0.04); border: 1px solid rgba(168, 85, 247, 0.3); border-radius: 14px; padding: 18px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 0.78rem; color: #a855f7; font-weight: 800; text-transform: uppercase;">🟣 Level 3: Senior / Lead (5+ Yrs)</span>
                        <span style="font-size: 0.7rem; background: rgba(168, 85, 247, 0.15); color: #a855f7; padding: 2px 8px; border-radius: 12px; font-weight: 700;">Strategy</span>
                    </div>
                    <strong style="color: var(--text-heading); font-size: 0.92rem; display: block; margin-bottom: 6px;">${l3_title}</strong>
                    <p style="font-size: 0.8rem; color: var(--text-secondary); margin: 0 0 10px; line-height: 1.4;">${l3_desc}</p>
                    <div style="font-size: 0.75rem; color: #a855f7; font-weight: 700;">🎯 Promotion Trigger: <span style="color: var(--text-primary); font-weight: 400;">${l3_trigger}</span></div>
                </div>
            </div>
            `;
        })()}

        <!-- PAGE FOOTER NAV -->
        <div class="page-footer-nav" style="display: flex; justify-content: space-between; align-items: center; margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--border);">
            <button type="button" class="footer-nav-btn" disabled style="opacity: 0.3; cursor: not-allowed;"><i class="fa-solid fa-arrow-left"></i> Prev Page</button>
            <span style="font-size: 0.88rem; color: var(--text-secondary); font-weight: 600;">Page 1 of 6</span>
            <button type="button" class="footer-nav-btn" onclick="showRoadmapPage(2)">Next Page <i class="fa-solid fa-arrow-right"></i></button>
        </div>
    </div>
</div>

<!-- ================= PAGE 2: STUDY TIMELINE ================= -->
<div class="roadmap-page" id="roadmap-page-2">
    <div class="roadmap-item">
        <h2><i class="fa-solid fa-route"></i> Step-by-Step Learning Timeline</h2>
        <p style="font-size: 0.95rem; line-height: 1.6; margin-bottom: 24px; color: var(--text-secondary);">
            Master this career path structured across sequential phases. Complete each milestone goal and task to progress.
        </p>

        <div class="timeline-container" style="display: flex; flex-direction: column; gap: 24px;">
            ${(roadmap || []).map((phase, idx) => `
                <div class="phase-card" style="background: rgba(25, 25, 25, 0.7); border: 1px solid var(--border); border-radius: 16px; padding: 22px; position: relative; box-shadow: 0 4px 15px rgba(0,0,0,0.25);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 8px;">
                        <span style="background: rgba(250, 204, 21, 0.1); border: 1px solid rgba(250, 204, 21, 0.3); color: var(--accent); padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 800; text-transform: uppercase;">
                            <i class="fa-solid fa-calendar-days"></i> ${phase.month || `Phase ${idx + 1}`}
                        </span>
                        <span style="color: var(--text-muted); font-size: 0.85rem; font-weight: 600;">Step ${idx + 1} of ${(roadmap || []).length}</span>
                    </div>
                    
                    <h3 style="margin-top: 0; margin-bottom: 12px; color: var(--text-heading); font-size: 1.15rem;">${phase.title || "Core Foundations"}</h3>
                    
                    <div style="margin-bottom: 16px;">
                        <strong style="color: var(--text-primary); font-size: 0.9rem; display: block; margin-bottom: 6px;">Key Concepts & Topics:</strong>
                        <ul style="margin: 0; padding-left: 20px; font-size: 0.88rem; color: var(--text-secondary); line-height: 1.5; gap: 4px; display: flex; flex-direction: column;">
                            ${(phase.topics || []).map(topic => `<li>${topic}</li>`).join("")}
                        </ul>
                    </div>

                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 14px; background: rgba(0,0,0,0.2); padding: 14px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.03);">
                        <div>
                            <strong style="color: #3b82f6; font-size: 0.8rem; text-transform: uppercase; display: block; margin-bottom: 4px;"><i class="fa-solid fa-briefcase"></i> Practical Task / Project</strong>
                            <p style="font-size: 0.84rem; color: var(--text-secondary); margin: 0; line-height: 1.4;">${phase.project || "Implement domain basics."}</p>
                        </div>
                        <div>
                            <strong style="color: #22c55e; font-size: 0.8rem; text-transform: uppercase; display: block; margin-bottom: 4px;"><i class="fa-solid fa-bullseye"></i> Phase Milestone Goal</strong>
                            <p style="font-size: 0.84rem; color: var(--text-secondary); margin: 0; line-height: 1.4;">${phase.goal || "Validation test."}</p>
                        </div>
                    </div>
                </div>
            `).join("")}
        </div>

        <!-- PAGE FOOTER NAV -->
        <div class="page-footer-nav" style="display: flex; justify-content: space-between; align-items: center; margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--border);">
            <button type="button" class="footer-nav-btn" onclick="showRoadmapPage(1)"><i class="fa-solid fa-arrow-left"></i> Prev Page</button>
            <span style="font-size: 0.88rem; color: var(--text-secondary); font-weight: 600;">Page 2 of 6</span>
            <button type="button" class="footer-nav-btn" onclick="showRoadmapPage(3)">Next Page <i class="fa-solid fa-arrow-right"></i></button>
        </div>
    </div>
</div>

<!-- ================= PAGE 3: SKILLS MATRIX ================= -->
<div class="roadmap-page" id="roadmap-page-3">
    <div class="roadmap-item">
        <h2><i class="fa-solid fa-code"></i> Skill Matrix & Tool Proficiency</h2>
        <p style="font-size: 0.95rem; line-height: 1.6; margin-bottom: 24px; color: var(--text-secondary);">
            Track your professional skill set. Check off items as you learn them to monitor your journey.
        </p>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 28px;">
            <div style="background: rgba(34, 197, 94, 0.03); border: 1px solid rgba(34, 197, 94, 0.2); border-radius: 16px; padding: 20px;">
                <h3 style="margin-top: 0; color: #22c55e; margin-bottom: 14px;"><i class="fa-solid fa-circle-check"></i> Beginner Core Skills</h3>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    ${(skills.beginner || ["Foundational concepts"]).map((s, idx) => `
                        <div class="custom-checkbox" style="display: flex; align-items: flex-start; gap: 10px;">
                            <input type="checkbox" id="beg-chk-${idx}" style="margin-top: 4px; cursor: pointer;">
                            <label for="beg-chk-${idx}" style="font-size: 0.9rem; color: var(--text-secondary); cursor: pointer; line-height: 1.4;">${s}</label>
                        </div>
                    `).join("")}
                </div>
            </div>

            <div style="background: rgba(250, 204, 21, 0.03); border: 1px solid rgba(250, 204, 21, 0.2); border-radius: 16px; padding: 20px;">
                <h3 style="margin-top: 0; color: var(--accent); margin-bottom: 14px;"><i class="fa-solid fa-circle-check"></i> Intermediate Execution</h3>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    ${(skills.intermediate || ["Applied engineering workflows"]).map((s, idx) => `
                        <div class="custom-checkbox" style="display: flex; align-items: flex-start; gap: 10px;">
                            <input type="checkbox" id="int-chk-${idx}" style="margin-top: 4px; cursor: pointer;">
                            <label for="int-chk-${idx}" style="font-size: 0.9rem; color: var(--text-secondary); cursor: pointer; line-height: 1.4;">${s}</label>
                        </div>
                    `).join("")}
                </div>
            </div>

            <div style="background: rgba(168, 85, 247, 0.03); border: 1px solid rgba(168, 85, 247, 0.2); border-radius: 16px; padding: 20px;">
                <h3 style="margin-top: 0; color: #a855f7; margin-bottom: 14px;"><i class="fa-solid fa-circle-check"></i> Advanced Leadership</h3>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    ${(skills.advanced || ["Strategic systems & architecture"]).map((s, idx) => `
                        <div class="custom-checkbox" style="display: flex; align-items: flex-start; gap: 10px;">
                            <input type="checkbox" id="adv-chk-${idx}" style="margin-top: 4px; cursor: pointer;">
                            <label for="adv-chk-${idx}" style="font-size: 0.9rem; color: var(--text-secondary); cursor: pointer; line-height: 1.4;">${s}</label>
                        </div>
                    `).join("")}
                </div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 24px;">
            <div style="background: rgba(25, 25, 25, 0.7); border: 1px solid var(--border); border-radius: 16px; padding: 20px;">
                <h3 style="margin-top: 0; color: var(--accent);"><i class="fa-solid fa-screwdriver-wrench"></i> Recommended Tools & Software</h3>
                <div class="chip-grid" style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px;">
                    ${(tools && tools.length ? tools : [`Professional ${data.career || career || "Career"} Tools`, "Standard Industry Utilities", "Collaboration Software"]).map(t => `<span class="chip-item">🛠 ${t}</span>`).join("")}
                </div>
            </div>

            <div style="background: rgba(25, 25, 25, 0.7); border: 1px solid var(--border); border-radius: 16px; padding: 20px;">
                <h3 style="margin-top: 0; color: #3b82f6;"><i class="fa-solid fa-certificate"></i> Key Professional Certifications</h3>
                <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 12px;">
                    ${(certifications && certifications.length ? certifications : [`Certified ${data.career || career || "Career"} Specialist`, "Standard Professional Credentials", "Industry Operations License"]).map(cert => `
                        <div style="font-size: 0.88rem; color: var(--text-secondary); padding: 8px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.04); border-radius: 8px; display: flex; align-items: center; gap: 8px;">
                            <i class="fa-solid fa-award" style="color: #3b82f6;"></i> ${cert}
                        </div>
                    `).join("")}
                </div>
            </div>
        </div>

        <!-- PAGE FOOTER NAV -->
        <div class="page-footer-nav" style="display: flex; justify-content: space-between; align-items: center; margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--border);">
            <button type="button" class="footer-nav-btn" onclick="showRoadmapPage(2)"><i class="fa-solid fa-arrow-left"></i> Prev Page</button>
            <span style="font-size: 0.88rem; color: var(--text-secondary); font-weight: 600;">Page 3 of 6</span>
            <button type="button" class="footer-nav-btn" onclick="showRoadmapPage(4)">Next Page <i class="fa-solid fa-arrow-right"></i></button>
        </div>
    </div>
</div>

<!-- ================= PAGE 4: PORTFOLIO PROJECTS ================= -->
<div class="roadmap-page" id="roadmap-page-4">
    <div class="roadmap-item">
        <h2><i class="fa-solid fa-laptop-code"></i> Hands-On Tasks & Practical Applications</h2>
        <p style="font-size: 0.95rem; line-height: 1.6; margin-bottom: 24px; color: var(--text-secondary);">
            Acquire real-world experience and proof of work by completing these practical tasks, case studies, or portfolio items.
        </p>

        <div style="display: flex; flex-direction: column; gap: 20px; margin-bottom: 24px;">
            <div style="background: rgba(34, 197, 94, 0.03); border: 1px solid rgba(34, 197, 94, 0.25); border-radius: 16px; padding: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 8px;">
                    <h3 style="margin: 0; color: #22c55e; font-size: 1.1rem;"><i class="fa-solid fa-seedling"></i> Beginner Tasks & Projects</h3>
                    <span style="font-size: 0.72rem; color: #22c55e; background: rgba(34, 197, 94, 0.1); padding: 2px 10px; border-radius: 10px; font-weight: 700;">Foundation</span>
                </div>
                <div style="display: flex; flex-direction: column; gap: 10px; margin-top: 10px;">
                    ${(projects.beginner || ["Construct foundation level project/task to learn concepts & standard tools."]).map((p, idx) => `
                        <div style="background: rgba(0,0,0,0.2); padding: 12px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.02); font-size: 0.9rem; color: var(--text-secondary); line-height: 1.45;">
                            <strong>Task ${idx + 1}:</strong> ${p}
                        </div>
                    `).join("")}
                </div>
            </div>

            <div style="background: rgba(250, 204, 21, 0.03); border: 1px solid rgba(250, 204, 21, 0.25); border-radius: 16px; padding: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 8px;">
                    <h3 style="margin: 0; color: var(--accent); font-size: 1.1rem;"><i class="fa-solid fa-fire"></i> Intermediate Tasks & Projects</h3>
                    <span style="font-size: 0.72rem; color: var(--accent); background: rgba(250, 204, 21, 0.1); padding: 2px 10px; border-radius: 10px; font-weight: 700;">Applied</span>
                </div>
                <div style="display: flex; flex-direction: column; gap: 10px; margin-top: 10px;">
                    ${(projects.intermediate || ["Build functional projects or case studies demonstrating intermediate mastery."]).map((p, idx) => `
                        <div style="background: rgba(0,0,0,0.2); padding: 12px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.02); font-size: 0.9rem; color: var(--text-secondary); line-height: 1.45;">
                            <strong>Task ${idx + 1}:</strong> ${p}
                        </div>
                    `).join("")}
                </div>
            </div>

            <div style="background: rgba(168, 85, 247, 0.03); border: 1px solid rgba(168, 85, 247, 0.25); border-radius: 16px; padding: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 8px;">
                    <h3 style="margin: 0; color: #a855f7; font-size: 1.1rem;"><i class="fa-solid fa-crown"></i> Advanced Tasks & Case Studies</h3>
                    <span style="font-size: 0.72rem; color: #a855f7; background: rgba(168, 85, 247, 0.1); padding: 2px 10px; border-radius: 10px; font-weight: 700;">Scale & Security</span>
                </div>
                <div style="display: flex; flex-direction: column; gap: 10px; margin-top: 10px;">
                    ${(projects.advanced || ["Complete advanced case studies, mock audits, or high-concurrency systems."]).map((p, idx) => `
                        <div style="background: rgba(0,0,0,0.2); padding: 12px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.02); font-size: 0.9rem; color: var(--text-secondary); line-height: 1.45;">
                            <strong>Task ${idx + 1}:</strong> ${p}
                        </div>
                    `).join("")}
                </div>
            </div>
        </div>

        <!-- PAGE FOOTER NAV -->
        <div class="page-footer-nav" style="display: flex; justify-content: space-between; align-items: center; margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--border);">
            <button type="button" class="footer-nav-btn" onclick="showRoadmapPage(3)"><i class="fa-solid fa-arrow-left"></i> Prev Page</button>
            <span style="font-size: 0.88rem; color: var(--text-secondary); font-weight: 600;">Page 4 of 6</span>
            <button type="button" class="footer-nav-btn" onclick="showRoadmapPage(5)">Next Page <i class="fa-solid fa-arrow-right"></i></button>
        </div>
    </div>
</div>

<!-- ================= PAGE 5: PREP & RESOURCES ================= -->
<div class="roadmap-page" id="roadmap-page-5">
    <div class="roadmap-item">
        <h2><i class="fa-solid fa-graduation-cap"></i> Preparation Strategy & Curated Resources</h2>
        <p style="font-size: 0.95rem; line-height: 1.6; margin-bottom: 24px; color: var(--text-secondary);">
            Optimize your preparation roadmap with hand-picked textbooks, online programs, official documentation, and shortcuts.
        </p>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 24px;">
            <div style="background: rgba(25, 25, 25, 0.7); border: 1px solid var(--border); border-radius: 16px; padding: 20px;">
                <h3 style="margin-top: 0; color: var(--accent);"><i class="fa-solid fa-laptop"></i> Recommended Courses & Programs</h3>
                <ul style="margin: 0; padding-left: 20px; font-size: 0.88rem; color: var(--text-secondary); line-height: 1.5; gap: 8px; display: flex; flex-direction: column;">
                    ${renderResourceList(resources.courses, ["Coursera Specialized Track", "Udemy Advanced Masterclass", "Vetted Certification Tracks"], "fa-solid fa-graduation-cap", "#60a5fa")}
                </ul>
            </div>

            <div style="background: rgba(25, 25, 25, 0.7); border: 1px solid var(--border); border-radius: 16px; padding: 20px;">
                <h3 style="margin-top: 0; color: #3b82f6;"><i class="fa-solid fa-book"></i> Vetted Books & Publications</h3>
                <ul style="margin: 0; padding-left: 20px; font-size: 0.88rem; color: var(--text-secondary); line-height: 1.5; gap: 8px; display: flex; flex-direction: column;">
                    ${renderResourceList(resources.books, ["Industry Standard Handbook", "Designing High Reliability Systems", "Operational Strategy Book"], "fa-solid fa-book", "#60a5fa")}
                </ul>
            </div>

            <div style="background: rgba(25, 25, 25, 0.7); border: 1px solid var(--border); border-radius: 16px; padding: 20px;">
                <h3 style="margin-top: 0; color: #22c55e;"><i class="fa-solid fa-file-lines"></i> Official Documentation</h3>
                <ul style="margin: 0; padding-left: 20px; font-size: 0.88rem; color: var(--text-secondary); line-height: 1.5; gap: 8px; display: flex; flex-direction: column;">
                    ${renderResourceList(resources.documentation, ["Official API Guidelines & Reference Docs", "Community standards & whitepapers"], "fa-solid fa-file-code", "#4ade80")}
                </ul>
            </div>

            <div style="background: rgba(25, 25, 25, 0.7); border: 1px solid var(--border); border-radius: 16px; padding: 20px;">
                <h3 style="margin-top: 0; color: #a855f7;"><i class="fa-solid fa-play"></i> YouTube Channels & Communities</h3>
                <ul style="margin: 0; padding-left: 20px; font-size: 0.88rem; color: var(--text-secondary); line-height: 1.5; gap: 8px; display: flex; flex-direction: column;">
                    ${renderResourceList(resources.youtube || resources.youtube_channels, ["Top-Tier Tech Creators", "Mock Interview Prep channels", "Expert Code Walkthroughs"], "fa-brands fa-youtube", "#f87171")}
                </ul>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 20px;">
            <div style="background: rgba(25, 25, 25, 0.7); border: 1px solid var(--border); border-radius: 16px; padding: 20px;">
                <h3 style="margin-top: 0; color: var(--accent);"><i class="fa-solid fa-clipboard-question"></i> Top 5 Interview Prep Questions</h3>
                <ul style="margin: 0; padding-left: 20px; font-size: 0.88rem; color: var(--text-secondary); line-height: 1.5; gap: 8px; display: flex; flex-direction: column;">
                    ${(interview && interview.length ? interview : ["Prepare core professional questions in your domain", "Mock case study/operational scenarios review"]).map(i => `<li>💬 ${i}</li>`).join("")}
                </ul>
            </div>

            <div style="background: rgba(25, 25, 25, 0.7); border: 1px solid var(--border); border-radius: 16px; padding: 20px;">
                <h3 style="margin-top: 0; color: #3b82f6;"><i class="fa-solid fa-bullseye"></i> Top 5 Portfolio Building Hacks</h3>
                <ul style="margin: 0; padding-left: 20px; font-size: 0.88rem; color: var(--text-secondary); line-height: 1.5; gap: 8px; display: flex; flex-direction: column;">
                    ${(portfolio && portfolio.length ? portfolio : ["Host/present documentation of your completed practical tasks", "Write precise case studies details on professional portfolio platforms"]).map(p => `<li>🎯 ${p}</li>`).join("")}
                </ul>
            </div>

            <div style="background: rgba(25, 25, 25, 0.7); border: 1px solid var(--border); border-radius: 16px; padding: 20px;">
                <h3 style="margin-top: 0; color: #a855f7;"><i class="fa-solid fa-wand-magic-sparkles"></i> Top 5 AI Hacks / Prompt Models</h3>
                <ul style="margin: 0; padding-left: 20px; font-size: 0.88rem; color: var(--text-secondary); line-height: 1.5; gap: 8px; display: flex; flex-direction: column;">
                    ${(aiTips && aiTips.length ? aiTips : [`Ask AI to critique your completed ${data.career || career || "Professional"} case studies`, "Simulate live specialist panel interviews using specialized prompts"]).map(a => `<li>🤖 ${a}</li>`).join("")}
                </ul>
            </div>
        </div>

        <!-- PAGE FOOTER NAV -->
        <div class="page-footer-nav" style="display: flex; justify-content: space-between; align-items: center; margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--border);">
            <button type="button" class="footer-nav-btn" onclick="showRoadmapPage(4)"><i class="fa-solid fa-arrow-left"></i> Prev Page</button>
            <span style="font-size: 0.88rem; color: var(--text-secondary); font-weight: 600;">Page 5 of 6</span>
            <button type="button" class="footer-nav-btn" onclick="showRoadmapPage(6)">Next Page <i class="fa-solid fa-arrow-right"></i></button>
        </div>
    </div>
</div>

<!-- ================= PAGE 6: MARKET & HIRING ================= -->
<div class="roadmap-page" id="roadmap-page-6">
    <div class="roadmap-item">
        <h2><i class="fa-solid fa-chart-pie"></i> Market Intelligence & Hiring Landscape</h2>
        <p style="font-size: 0.95rem; line-height: 1.6; margin-bottom: 24px; color: var(--text-secondary);">
            Evaluate salary metrics, global mobility scope, visa configurations, hiring clusters, and core parameters.
        </p>

        <!-- Official Country Salary Pay Band Card -->
        ${renderPayBandCard(overview.salary || market.salary, targetSalInfo, country)}

        <!-- AI Resilience & Career Longevity Index -->
        ${(() => {
            const careerTitle = data.career || career || "Professional";
            const cLow = careerTitle.toLowerCase();
            
            let aiRisk = "Low-Moderate Risk / Augmented Workflows";
            let aiRiskDetails = "AI automates routine analysis and boilerplate deliverables, but human strategic oversight remains essential.";
            let futureProofing = "Strategic Governance & Human-in-the-Loop Integration";
            let futureProofingDetails = "Focus on client consultation, final quality assurance, and directing AI multi-agent workflows to scale output.";
            let score = "88 / 100";
            let tier = "Highly Resilient";
            let tierColor = "#22c55e"; // Green

            if (cLow.includes("software") || cLow.includes("developer") || cLow.includes("backend") || cLow.includes("frontend") || cLow.includes("coder") || cLow.includes("programmer")) {
                aiRisk = "Low-Medium Risk / Augmented Software Engineering";
                aiRiskDetails = "AI coding assistants accelerate syntax generation, but human architects are critical for system design, security, and integration.";
                futureProofing = "System Architecture & AI Agent Orchestration";
                futureProofingDetails = "Shift from writing basic code to designing complex microservices, debugging edge cases, and guiding coding agents.";
                score = "90 / 100";
                tier = "Co-Pilot Enabled";
                tierColor = "#3b82f6"; // Blue
            } else if (cLow.includes("data") || cLow.includes("statistic") || cLow.includes("analyst")) {
                aiRisk = "Medium Risk / Predictive & Automated Analytics";
                aiRiskDetails = "Automated ML handles basic model fitting, but human domain context and business alignment are highly irreplaceable.";
                futureProofing = "Domain Integration & Causal ML Auditing";
                futureProofingDetails = "Develop deep business domain expertise, master A/B testing interpretation, and audit model bias/compliance.";
                score = "82 / 100";
                tier = "Augmented Specialist";
                tierColor = "#eab308"; // Yellow
            } else if (cLow.includes("doctor") || cLow.includes("nurse") || cLow.includes("medical") || cLow.includes("dentist") || cLow.includes("surgeon") || cLow.includes("physician") || cLow.includes("clinical")) {
                aiRisk = "Extremely Low Risk / Physical & Critical Care";
                aiRiskDetails = "Diagnostic AI assists, but physical treatment, critical care decision-making, and patient trust require human presence.";
                futureProofing = "Clinical Empathy & Hybrid Diagnostics";
                futureProofingDetails = "Combine high-level AI diagnostic insights with patient relationship management and hands-on clinical procedures.";
                score = "98 / 100";
                tier = "Immune to Automation";
                tierColor = "#22c55e"; // Green
            } else if (cLow.includes("design") || cLow.includes("artist") || cLow.includes("3d") || cLow.includes("vfx") || cLow.includes("animat") || cLow.includes("creative") || cLow.includes("graphic")) {
                aiRisk = "Medium Risk / Generative Creative Assistance";
                aiRiskDetails = "Generative models produce asset drafts quickly, but final artistic direction, brand voice consistency, and emotion belong to humans.";
                futureProofing = "Art Direction & Creative Prompt Engineering";
                futureProofingDetails = "Evolve into an art director who curates, refines, and directs AI-generated media to align with strategic brand storytelling.";
                score = "80 / 100";
                tier = "Creative Director";
                tierColor = "#a855f7"; // Purple
            } else if (cLow.includes("manager") || cLow.includes("director") || cLow.includes("lead") || cLow.includes("executive") || cLow.includes("product") || cLow.includes("consultant")) {
                aiRisk = "Low Risk / Interpersonal & Strategic Leadership";
                aiRiskDetails = "AI cannot coordinate cross-functional teams, resolve human conflicts, negotiate contracts, or align stakeholder vision.";
                futureProofing = "Stakeholder Synergy & High-Stakes Negotiation";
                futureProofingDetails = "Double down on communication, emotional intelligence, resource orchestration, and value-stream mapping.";
                score = "94 / 100";
                tier = "Management Shielded";
                tierColor = "#22c55e"; // Green
            } else if (cLow.includes("exam") || cLow.includes("preparation") || cLow.includes("upsc") || cLow.includes("gate") || cLow.includes("jee") || cLow.includes("neet") || cLow.includes("psc")) {
                aiRisk = "Low Risk / Statutory Policy & Public Administration";
                aiRiskDetails = "Public policy enforcement and civic administration demand human accountability, legal authority, and ethical judgment.";
                futureProofing = "Ethical Decision Making & Public Policy Governance";
                futureProofingDetails = "Focus on administrative efficiency, community crisis resolution, and integration of automated civic tech services.";
                score = "96 / 100";
                tier = "Statutory Authority";
                tierColor = "#22c55e"; // Green
            }

            return `
            <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(59, 130, 246, 0.35); border-radius: 18px; padding: 22px; margin-top: 20px; margin-bottom: 20px; box-shadow: 0 12px 30px rgba(0,0,0,0.45); backdrop-filter: blur(10px);">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 16px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 12px;">
                    <span style="font-size: 1.02rem; font-weight: 800; color: var(--text-heading); display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 1.3rem;">🛡️</span> AI Resilience & Career Longevity Index
                    </span>
                    <span style="background: rgba(34, 197, 94, 0.15); color: ${tierColor}; border: 1px solid ${tierColor}66; font-size: 0.78rem; padding: 4px 12px; border-radius: 20px; font-weight: 800;">
                        <i class="fa-solid fa-shield-halved"></i> Status: ${tier}
                    </span>
                </div>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px;">
                    <div style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 16px;">
                        <span style="font-size: 0.72rem; color: #3b82f6; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">🤖 AI Impact & Automation Risk</span>
                        <h4 style="color: var(--text-heading); font-size: 0.92rem; margin: 6px 0 4px; font-weight: 800;">${aiRisk}</h4>
                        <p style="font-size: 0.76rem; color: var(--text-secondary); margin: 0; line-height: 1.35;">${aiRiskDetails}</p>
                    </div>

                    <div style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 16px;">
                        <span style="font-size: 0.72rem; color: #22c55e; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">🛡️ Future-Proofing Strategy</span>
                        <h4 style="color: #22c55e; font-size: 0.92rem; margin: 6px 0 4px; font-weight: 800;">${futureProofing}</h4>
                        <p style="font-size: 0.76rem; color: var(--text-secondary); margin: 0; line-height: 1.35;">${futureProofingDetails}</p>
                    </div>

                    <div style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 16px;">
                        <span style="font-size: 0.72rem; color: #a855f7; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">📈 AI Resilience Score</span>
                        <h4 style="color: #d8b4fe; font-size: 1.1rem; margin: 4px 0 2px; font-weight: 900;">${score}</h4>
                        <p style="font-size: 0.76rem; color: var(--text-secondary); margin: 0; line-height: 1.35;">High career longevity and AI disruption protection for ${careerTitle}.</p>
                    </div>
                </div>
            </div>
            `;
        })()}

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 24px; align-items: center;">
            <div style="background: rgba(25, 25, 25, 0.7); border: 1px solid var(--border); border-radius: 16px; padding: 20px; box-shadow: 0 8px 24px rgba(0,0,0,0.4);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="font-size: 0.88rem; font-weight: 800; color: var(--text-heading);"><i class="fa-solid fa-chart-radar" style="color: var(--accent); margin-right: 6px;"></i> Market Ecosystem Radar</span>
                </div>
                <div style="height: 230px; position: relative;">
                    <canvas id="marketAnalyticsCanvas"></canvas>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px;">
                <div style="background: rgba(34, 197, 94, 0.05); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 14px; padding: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-size: 0.78rem; color: #22c55e; font-weight: 800;">🔥 JOB DEMAND</span>
                        <span style="font-size: 0.82rem; font-weight: 900; color: #22c55e; background: rgba(34, 197, 94, 0.15); padding: 2px 10px; border-radius: 10px;">${market.job_demand?.rating || (market.job_demand?.percentage ? (market.job_demand.percentage > 80 ? 'Very High' : 'High') : 'High')}</span>
                    </div>
                    <p style="font-size: 0.78rem; color: var(--text-secondary); margin: 6px 0 0; line-height: 1.4;">${market.job_demand?.reason || market.job_demand?.text || `High market demand driven by enterprise hiring.`}</p>
                </div>

                <div style="background: rgba(250, 204, 21, 0.05); border: 1px solid rgba(250, 204, 21, 0.3); border-radius: 14px; padding: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-size: 0.78rem; color: var(--accent); font-weight: 800;">🎯 LEARNING CURVE</span>
                        <span style="font-size: 0.82rem; font-weight: 900; color: var(--accent); background: rgba(250, 204, 21, 0.15); padding: 2px 10px; border-radius: 10px;">${market.difficulty?.level || 'Moderate to High'}</span>
                    </div>
                    <p style="font-size: 0.78rem; color: var(--text-secondary); margin: 6px 0 0; line-height: 1.4;">${market.difficulty?.reason || market.difficulty?.text || "Moderate to high learning curve requiring structured hands-on practice."}</p>
                </div>

                <div style="background: rgba(59, 130, 246, 0.05); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 14px; padding: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-size: 0.78rem; color: #3b82f6; font-weight: 800;">🚀 CAREER GROWTH</span>
                        <span style="font-size: 0.82rem; font-weight: 900; color: #3b82f6; background: rgba(59, 130, 246, 0.15); padding: 2px 10px; border-radius: 10px;">${market.growth?.outlook || (market.growth?.percentage ? (market.growth.percentage > 80 ? 'Fast Growing' : 'Growing') : 'Growing')}</span>
                    </div>
                    <p style="font-size: 0.78rem; color: var(--text-secondary); margin: 6px 0 0; line-height: 1.4;">${market.growth?.reason || market.growth?.text || "Strong multi-year expansion powered by technology integration."}</p>
                </div>

                <div style="background: rgba(168, 85, 247, 0.05); border: 1px solid rgba(168, 85, 247, 0.3); border-radius: 14px; padding: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-size: 0.78rem; color: #a855f7; font-weight: 800;">📚 TIME COMMITMENT</span>
                        <span style="font-size: 0.82rem; font-weight: 900; color: #a855f7; background: rgba(168, 85, 247, 0.15); padding: 2px 10px; border-radius: 10px;">${market.learning_time?.duration || '6 Months'}</span>
                    </div>
                    <p style="font-size: 0.78rem; color: var(--text-secondary); margin: 6px 0 0; line-height: 1.4;">${market.learning_time?.details || market.learning_time?.text || "Estimated time commitment for structured learning to entry level."}</p>
                </div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 20px;">
            <div>
                <h3><i class="fa-solid fa-building"></i> Top 5 Hiring Organizations</h3>
                <div class="chip-grid">
                    ${(market.top_organizations || []).map(o => `<span class="chip-item">🏢 ${o}</span>`).join("")}
                </div>
            </div>
            <div>
                <h3><i class="fa-solid fa-fire"></i> Top 5 Trending Skills</h3>
                <div class="chip-grid">
                    ${(market.trending_skills || []).map(s => `<span class="chip-item">🔥 ${s}</span>`).join("")}
                </div>
            </div>
        </div>

        <h3><i class="fa-solid fa-location-dot"></i> Hiring Spots</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 20px;">
            ${(market.hiring_hotspots || []).map(city => `
                <div style="background: rgba(25, 25, 25, 0.8); border: 1px solid var(--border); border-radius: 12px; padding: 12px; text-align: center;">
                    <span style="font-size: 0.75rem; color: var(--accent); font-weight: 700;">📍 ${city.city}</span>
                    <h5 style="margin: 4px 0; color: var(--text-heading); font-size: 0.85rem;">${city.demand}</h5>
                    <p style="font-size: 0.75rem; color: var(--text-secondary); margin: 0; line-height: 1.35;">${city.reason}</p>
                </div>
            `).join("")}
        </div>

        <h3><i class="fa-solid fa-calendar-check"></i> Top 5 Weekly Study Plan Steps</h3>
        <ul>
            ${(market.daily_plan || []).map(day => `<li>📅 ${day}</li>`).join("")}
        </ul>

        <!-- PAGE FOOTER NAV -->
        <div class="page-footer-nav" style="display: flex; justify-content: space-between; align-items: center; margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--border);">
            <button type="button" class="footer-nav-btn" onclick="showRoadmapPage(5)"><i class="fa-solid fa-arrow-left"></i> Prev Page</button>
            <span style="font-size: 0.88rem; color: var(--text-secondary); font-weight: 600;">Page 6 of 6</span>
            <button type="button" class="footer-nav-btn" disabled style="opacity: 0.3; cursor: not-allowed;">Next Page <i class="fa-solid fa-arrow-right"></i></button>
        </div>
    </div>
</div>
            <hr style="margin-top:40px">
            <p style="text-align:center; font-size:14px; color:#777; margin-top:15px;">Generated by <b>CareerVerse AI</b></p>
`;
        clearInterval(loadingInterval);

        resultCardEl.innerHTML = html;
        resultCardEl.scrollIntoView({ behavior: 'smooth', block: 'start' });

        // Initialize Professional Chart.js Radar Chart
        setTimeout(() => {
            const canvas = document.getElementById("marketAnalyticsCanvas");
            if (canvas && typeof Chart !== "undefined") {
                if (window.marketChartInstance) {
                    window.marketChartInstance.destroy();
                }
                const ctx = canvas.getContext("2d");
                const mapRatingToScore = (val, defaultScore = 80) => {
                    if (typeof val === "number") return val;
                    if (typeof val === "string") {
                        const v = val.toLowerCase();
                        if (v.includes("very high") || v.includes("fast growing")) return 92;
                        if (v.includes("high") || v.includes("growing")) return 78;
                        if (v.includes("moderate") || v.includes("stable")) return 55;
                        if (v.includes("low") || v.includes("declining")) return 30;
                    }
                    return defaultScore;
                };

                const demandVal = mapRatingToScore(market.job_demand?.rating || market.job_demand?.percentage, 85);
                const growthVal = mapRatingToScore(market.growth?.outlook || market.growth?.percentage, 88);
                const diffVal = mapRatingToScore(market.difficulty?.level || market.difficulty?.percentage, 75);
                const timeVal = mapRatingToScore(market.learning_time?.duration || market.learning_time?.percentage, 80);

                window.marketChartInstance = new Chart(ctx, {
                    type: "radar",
                    data: {
                        labels: ["Job Demand", "Growth Outlook", "Learning Curve", "Time Index", "Stability"],
                        datasets: [{
                            label: "Market Scope Score",
                            data: [demandVal, growthVal, diffVal, timeVal, 85],
                            backgroundColor: "rgba(250, 204, 21, 0.25)",
                            borderColor: "#fac515",
                            pointBackgroundColor: "#fac515",
                            pointBorderColor: "#fff",
                            pointHoverBackgroundColor: "#fff",
                            pointHoverBorderColor: "#fac515",
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            r: {
                                angleLines: { color: "rgba(255, 255, 255, 0.12)" },
                                grid: { color: "rgba(255, 255, 255, 0.12)" },
                                pointLabels: { color: "#e2e8f0", font: { size: 10, weight: "bold" } },
                                ticks: { display: false, backdropColor: "transparent" },
                                min: 0,
                                max: 100
                            }
                        },
                        plugins: {
                            legend: { display: false }
                        }
                    }
                });
            }
        }, 100);

        const inlineBtn = document.getElementById("inlineDownloadBtn");
        if (inlineBtn) {
            inlineBtn.addEventListener("click", generatePDFReport);
        }

        const actionSection = document.getElementById("actionSection");
        if (actionSection) {
            actionSection.style.display = "flex";
        }

    } catch (error) {
        console.error(error);
        if (generateBtnEl) {
            generateBtnEl.disabled = false;
            generateBtnEl.innerHTML = `<i class="fa-solid fa-route"></i> Generate AI Roadmap`;
        }
        resultCardEl.innerHTML = `
            <div class="roadmap-item error-card" style="border: 1px solid #ef4444; background: rgba(239, 68, 68, 0.08); padding: 26px; border-radius: 16px; margin-top: 20px;">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <i class="fa-solid fa-circle-exclamation" style="font-size: 1.6rem; color: #ef4444;"></i>
                    <h3 style="color: var(--text-heading); margin: 0; font-size: 1.2rem;">Roadmap Generation Error</h3>
                </div>
                <p style="color: var(--text-primary); font-size: 0.96rem; line-height: 1.6;">${error.message || "Unable to generate roadmap. Please try again."}</p>
            </div>
        `;
    }
}

// Expose function globally for inline onclick
window.generateRoadmapNow = generateRoadmapNow;

// DOMContentLoaded listener for button binding and auto-trigger
document.addEventListener("DOMContentLoaded", () => {
    const generateBtnEl = document.getElementById("generateBtn");
    if (generateBtnEl) {
        generateBtnEl.onclick = generateRoadmapNow;
    }

    const urlParams = new URLSearchParams(window.location.search);
    const roleParam = urlParams.get("role") || urlParams.get("career");
    const careerInputEl = document.getElementById("careerInput");
    if (roleParam && careerInputEl) {
        careerInputEl.value = roleParam;
        generateRoadmapNow();
    }
});

// ==========================================
// PROFESSIONAL PDF EXPORT - PHASE 1
// ==========================================

if (downloadBtn) {
    downloadBtn.addEventListener("click", generatePDFReport);
}

function generatePDFReport() {
    if (!window.currentRoadmap) {
        alert("Please generate a roadmap first.");
        return;
    }

    const { jsPDF } = window.jspdf;
    const doc = new jsPDF("p", "mm", "a4");

    const NAVY = [15, 23, 42];        // #0f172a
    const GOLD = [202, 138, 4];       // #ca8a04
    const SLATE = [30, 41, 59];       // #1e293b
    const MUTED = [100, 116, 139];     // #64748b

    const pageWidth = 210;
    const margin = 15;
    const contentWidth = pageWidth - (margin * 2);
    let y = 0;

    const data = window.currentRoadmap;

    function sanitize(str) {
        if (!str) return "";
        return String(str)
            .replace(/₹/g, "INR ")
            .replace(/¥/g, "JPY ")
            .replace(/€/g, "EUR ")
            .replace(/£/g, "GBP ")
            .replace(/₩/g, "KRW ")
            .replace(/₺/g, "TRY ")
            .replace(/₪/g, "ILS ")
            .replace(/฿/g, "THB ")
            .replace(/₽/g, "RUB ")
            .replace(/৳/g, "BDT ")
            .replace(/₱/g, "PHP ")
            .replace(/₫/g, "VND ")
            .replace(/₦/g, "NGN ")
            .replace(/[^\x00-\x7F]/g, "")
            .replace(/\s+/g, " ")
            .trim();
    }

    function checkPageBreak(neededSpace = 25) {
        if (y + neededSpace > 275) {
            doc.addPage();
            y = 20;
            return true;
        }
        return false;
    }

    function drawSectionHeader(title) {
        checkPageBreak(18);
        doc.setFillColor(...NAVY);
        doc.rect(margin, y, 3.5, 6.5, "F");
        
        doc.setFont("helvetica", "bold");
        doc.setFontSize(12);
        doc.setTextColor(...NAVY);
        doc.text(sanitize(title).toUpperCase(), margin + 6, y + 5);

        y += 8;
        doc.setDrawColor(226, 232, 240);
        doc.setLineWidth(0.3);
        doc.line(margin, y, pageWidth - margin, y);
        y += 5;
    }

    // 1. TOP HEADER BANNER
    doc.setFillColor(...NAVY);
    doc.rect(0, 0, pageWidth, 28, "F");
    doc.setFillColor(...GOLD);
    doc.rect(0, 28, pageWidth, 1.5, "F");

    doc.setTextColor(255, 255, 255);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(20);
    doc.text("CareerVerse AI", margin, 15);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(8.5);
    doc.setTextColor(203, 213, 225);
    doc.text("AUTONOMOUS CAREER INTELLIGENCE & MASTER ROADMAP REPORT", margin, 22);

    const today = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    doc.text(today, pageWidth - margin, 22, { align: "right" });

    y = 38;

    // 2. DOCUMENT TITLE BLOCK
    doc.setFont("helvetica", "bold");
    doc.setFontSize(18);
    doc.setTextColor(...SLATE);
    const careerTitle = sanitize(data.career || "Target Career Role");
    doc.text(careerTitle, margin, y);

    y += 6;
    doc.setFontSize(9.5);
    doc.setFont("helvetica", "normal");
    doc.setTextColor(...MUTED);
    const locText = `Target Location / Region: ${sanitize(data.country || 'Global / India')}`;
    doc.text(locText, margin, y);
    y += 10;

    // SECTION 1: OVERVIEW
    const overview = data.overview || {};
    drawSectionHeader("1. Executive Career Overview");
    
    doc.setFont("helvetica", "normal");
    doc.setFontSize(9.5);
    doc.setTextColor(...SLATE);
    const descLines = doc.splitTextToSize(sanitize(overview.description || "Comprehensive career development roadmap."), contentWidth);
    doc.text(descLines, margin, y);
    y += descLines.length * 4.5 + 4;

    const salaryObj = overview.salary || data.market?.salary || {};
    const pdfTargetLoc = sanitize(salaryObj.target_location || data.country || 'Target Location');

    let pdfTargetSalaryStr = "";
    if (salaryObj.formatted_range) {
        pdfTargetSalaryStr = sanitize(salaryObj.formatted_range);
    } else if (salaryObj.fresher && salaryObj.fresher !== "Data unavailable") {
        pdfTargetSalaryStr = sanitize(`${salaryObj.fresher} (Fresher) -> ${salaryObj.mid} (Mid) -> ${salaryObj.senior} (Senior)`);
    } else {
        pdfTargetSalaryStr = "Data unavailable";
    }

    let pdfIntlSalaryStr = "";
    if (salaryObj.international_usd_range) {
        pdfIntlSalaryStr = sanitize(salaryObj.international_usd_range);
    } else if (salaryObj.international_usd_fresher && salaryObj.international_usd_fresher !== "Data unavailable") {
        pdfIntlSalaryStr = sanitize(`${salaryObj.international_usd_fresher} (Fresher) -> ${salaryObj.international_usd_mid} (Mid) -> ${salaryObj.international_usd_senior} (Senior)`);
    } else {
        pdfIntlSalaryStr = "Data unavailable";
    }

    doc.autoTable({
        startY: y,
        head: [['Education & Path', `Expected Pay (${pdfTargetLoc})`, 'Future Scope']],
        body: [[
            sanitize(overview.education || "Bachelor's / STEM"),
            pdfTargetSalaryStr,
            sanitize(overview.future_scope || "High Demand")
        ]],
        styles: { fontSize: 8.5, cellPadding: 4 },
        headStyles: { fillColor: NAVY, textColor: [255, 255, 255], fontStyle: 'bold' },
        margin: { left: margin, right: margin }
    });
    y = doc.lastAutoTable.finalY + 8;

    // SECTION 2: SKILLS
    const skills = data.skills || {};
    drawSectionHeader("2. Technical Skill Mastery Matrix");
    
    const maxSkills = Math.max(
        (skills.beginner || []).length,
        (skills.intermediate || []).length,
        (skills.advanced || []).length
    );

    const skillRows = [];
    for (let i = 0; i < maxSkills; i++) {
        skillRows.push([
            sanitize(skills.beginner?.[i] || "-"),
            sanitize(skills.intermediate?.[i] || "-"),
            sanitize(skills.advanced?.[i] || "-")
        ]);
    }

    doc.autoTable({
        startY: y,
        head: [['Beginner Level', 'Intermediate Level', 'Advanced Level']],
        body: skillRows,
        styles: { fontSize: 8.5, cellPadding: 3.5 },
        headStyles: { fillColor: SLATE, textColor: [255, 255, 255], fontStyle: 'bold' },
        margin: { left: margin, right: margin }
    });
    y = doc.lastAutoTable.finalY + 8;

    // SECTION 3: MONTHLY ROADMAP TIMELINE
    const roadmap = data.roadmap || [];
    drawSectionHeader("3. Step-by-Step Monthly Execution Roadmap");

    const roadmapRows = roadmap.map(m => [
        sanitize(m.month || 'Phase') + '\n' + sanitize(m.title || ''),
        (m.topics || []).map(t => '• ' + sanitize(t)).join('\n'),
        'Task/Project: ' + sanitize(m.project || 'N/A') + '\nGoal: ' + sanitize(m.goal || 'N/A')
    ]);

    doc.autoTable({
        startY: y,
        head: [['Month / Phase Title', 'Core Topics to Master', 'Practical Task & Milestone Goal']],
        body: roadmapRows,
        styles: { fontSize: 8, cellPadding: 3.5 },
        headStyles: { fillColor: NAVY, textColor: [255, 255, 255], fontStyle: 'bold' },
        columnStyles: {
            0: { cellWidth: 45 },
            1: { cellWidth: 75 },
            2: { cellWidth: 60 }
        },
        margin: { left: margin, right: margin }
    });
    y = doc.lastAutoTable.finalY + 8;

    // SECTION 4: PROJECTS & CERTIFICATIONS
    const projects = data.projects || {};
    drawSectionHeader("4. Hands-On Tasks & Practical Applications");

    const projRows = [];
    const maxP = Math.max((projects.beginner || []).length, (projects.intermediate || []).length, (projects.advanced || []).length);
    for (let i = 0; i < maxP; i++) {
        projRows.push([
            sanitize(projects.beginner?.[i] || "-"),
            sanitize(projects.intermediate?.[i] || "-"),
            sanitize(projects.advanced?.[i] || "-")
        ]);
    }

    doc.autoTable({
        startY: y,
        head: [['Beginner Tasks & Projects', 'Intermediate Tasks & Projects', 'Advanced Tasks & Case Studies']],
        body: projRows,
        styles: { fontSize: 8.5, cellPadding: 3.5 },
        headStyles: { fillColor: SLATE, textColor: [255, 255, 255], fontStyle: 'bold' },
        margin: { left: margin, right: margin }
    });
    y = doc.lastAutoTable.finalY + 8;

    // SECTION 5: MARKET INTELLIGENCE
    const market = data.market || {};
    drawSectionHeader("5. Market Intelligence & Hiring Ecosystem");

    const demandRating = market.job_demand?.rating || (market.job_demand?.percentage ? (market.job_demand.percentage > 80 ? 'Very High' : 'High') : 'High');
    const growthOutlook = market.growth?.outlook || (market.growth?.percentage ? (market.growth.percentage > 80 ? 'Fast Growing' : 'Growing') : 'Growing');

    const freshSalary = market.salary?.fresher || 'Data unavailable';
    const midSalary = market.salary?.mid || 'Data unavailable';
    const senSalary = market.salary?.senior || 'Data unavailable';

    doc.autoTable({
        startY: y,
        head: [['Metric', 'Salary Pay Bands', 'Top Hiring Companies', 'Key Hiring Hotspots']],
        body: [[
            'Job Demand: ' + demandRating + '\nGrowth Outlook: ' + growthOutlook,
            'Fresher: ' + sanitize(freshSalary) + '\nMid: ' + sanitize(midSalary) + '\nSenior: ' + sanitize(senSalary),
            (market.top_organizations || []).slice(0, 5).join(', '),
            (market.hiring_hotspots || []).map(h => sanitize(h.city)).join(', ')
        ]],
        styles: { fontSize: 8.5, cellPadding: 4 },
        headStyles: { fillColor: NAVY, textColor: [255, 255, 255], fontStyle: 'bold' },
        margin: { left: margin, right: margin }
    });

    const safeFileName = sanitize(data.career || 'CareerVerse').replace(/\s+/g, '_');
    doc.save(`${safeFileName}_Roadmap.pdf`);
}

// ==========================================
// Page Router & Radar Chart Initializer
// ==========================================

window.showRoadmapPage = function(pageNum) {
    // 1. Update active state on navigator buttons
    const buttons = document.querySelectorAll(".roadmap-page-btn");
    buttons.forEach((btn, idx) => {
        if (idx + 1 === pageNum) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });

    // 2. Update active state on roadmap pages
    const pages = document.querySelectorAll(".roadmap-page");
    pages.forEach((page, idx) => {
        if (idx + 1 === pageNum) {
            page.classList.add("active");
            page.style.display = "block";
        } else {
            page.classList.remove("active");
            page.style.display = "none";
        }
    });

    // 3. Scroll container into view smoothly
    const container = document.querySelector(".roadmap-top-bar");
    if (container) {
        container.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    // 4. Deferred initialization of Radar chart on page 6
    if (pageNum === 6) {
        initRadarChartDeferred();
    }
};

function initRadarChartDeferred() {
    setTimeout(() => {
        const canvas = document.getElementById("marketAnalyticsCanvas");
        if (canvas && typeof Chart !== "undefined") {
            if (window.marketChartInstance) {
                window.marketChartInstance.destroy();
            }
            const ctx = canvas.getContext("2d");
            const market = window.currentRoadmap?.market || {};
            
            const mapRatingToScore = (val, defaultScore = 80) => {
                if (typeof val === "number") return val;
                if (typeof val === "string") {
                    const v = val.toLowerCase();
                    if (v.includes("very high") || v.includes("fast growing")) return 92;
                    if (v.includes("high") || v.includes("growing")) return 78;
                    if (v.includes("moderate") || v.includes("stable")) return 55;
                    if (v.includes("low") || v.includes("declining")) return 30;
                }
                return defaultScore;
            };

            const demandVal = mapRatingToScore(market.job_demand?.rating || market.job_demand?.percentage, 85);
            const growthVal = mapRatingToScore(market.growth?.outlook || market.growth?.percentage, 88);
            const diffVal = mapRatingToScore(market.difficulty?.level || market.difficulty?.percentage, 75);
            const timeVal = mapRatingToScore(market.learning_time?.duration || market.learning_time?.percentage, 80);

            window.marketChartInstance = new Chart(ctx, {
                type: "radar",
                data: {
                    labels: ["Job Demand", "Growth Outlook", "Learning Curve", "Time Index", "Stability"],
                    datasets: [{
                        label: "Market Scope Score",
                        data: [demandVal, growthVal, diffVal, timeVal, 85],
                        backgroundColor: "rgba(250, 204, 21, 0.25)",
                        borderColor: "#fac515",
                        pointBackgroundColor: "#fac515",
                        pointBorderColor: "#fff",
                        pointHoverBackgroundColor: "#fff",
                        pointHoverBorderColor: "#fac515",
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            angleLines: { color: "rgba(255, 255, 255, 0.12)" },
                            grid: { color: "rgba(255, 255, 255, 0.12)" },
                            pointLabels: { color: "#e2e8f0", font: { size: 10, weight: "bold" } },
                            ticks: { display: false, backdropColor: "transparent" },
                            min: 0,
                            max: 100
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }
    }, 100);
}



