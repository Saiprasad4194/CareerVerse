"""
CareerVerse Curated Resources & Anti-Hallucination Layer
=========================================================
Prevents hallucinated course/resource/certification recommendations.
- Enforces well-known, verified platforms (Coursera, Udemy, YouTube, freeCodeCamp, edX, Official Docs).
- Forbids direct, unverified LLM URLs in prompts.
- Maintains a hand-curated registry of real, authoritative learning resources per common skill.
- Constructs guaranteed-safe search / landing URLs on verified platforms rather than broken deep links.
"""

import urllib.parse
from typing import Dict, List, Any, Optional

# Vetted real platforms supported by the recommendation engine
VERIFIED_PLATFORMS = {
    "coursera": {
        "name": "Coursera",
        "base_url": "https://www.coursera.org",
        "search_url": "https://www.coursera.org/search?query={query}",
        "icon": "fa-solid fa-graduation-cap",
        "badge_color": "#0056D2"
    },
    "udemy": {
        "name": "Udemy",
        "base_url": "https://www.udemy.com",
        "search_url": "https://www.udemy.com/courses/search/?q={query}",
        "icon": "fa-solid fa-play",
        "badge_color": "#A435F0"
    },
    "freecodecamp": {
        "name": "freeCodeCamp",
        "base_url": "https://www.freecodecamp.org",
        "search_url": "https://www.freecodecamp.org/news/search/?query={query}",
        "icon": "fa-brands fa-free-code-camp",
        "badge_color": "#0A0A23"
    },
    "youtube": {
        "name": "YouTube",
        "base_url": "https://www.youtube.com",
        "search_url": "https://www.youtube.com/results?search_query={query}",
        "icon": "fa-brands fa-youtube",
        "badge_color": "#FF0000"
    },
    "edx": {
        "name": "edX",
        "base_url": "https://www.edx.org",
        "search_url": "https://www.edx.org/search?q={query}",
        "icon": "fa-solid fa-building-columns",
        "badge_color": "#B8262C"
    },
    "official docs": {
        "name": "Official Docs",
        "base_url": "https://devdocs.io",
        "search_url": "https://devdocs.io/#q={query}",
        "icon": "fa-solid fa-book-bookmark",
        "badge_color": "#10B981"
    },
    "github": {
        "name": "GitHub",
        "base_url": "https://github.com",
        "search_url": "https://github.com/search?q={query}",
        "icon": "fa-brands fa-github",
        "badge_color": "#24292F"
    },
    "linkedin learning": {
        "name": "LinkedIn Learning",
        "base_url": "https://www.linkedin.com/learning",
        "search_url": "https://www.linkedin.com/learning/search?keywords={query}",
        "icon": "fa-brands fa-linkedin",
        "badge_color": "#0A66C2"
    },
    "khan academy": {
        "name": "Khan Academy",
        "base_url": "https://www.khanacademy.org",
        "search_url": "https://www.khanacademy.org/search?page_search_query={query}",
        "icon": "fa-solid fa-leaf",
        "badge_color": "#14BF96"
    },
    "book": {
        "name": "Authoritative Book",
        "base_url": "https://www.goodreads.com",
        "search_url": "https://www.goodreads.com/search?q={query}",
        "icon": "fa-solid fa-book",
        "badge_color": "#3B82F6"
    }
}

# Curated Fallback Registry for Common Skills & Disciplines
# Hand-checked, reliable real courses, docs, and channels
CURATED_SKILL_RESOURCES: Dict[str, Dict[str, List[Dict[str, str]]]] = {
    "python": {
        "courses": [
            {"name": "Python for Everybody Specialization", "platform": "Coursera", "url": "https://www.coursera.org/specializations/python"},
            {"name": "Scientific Computing with Python Certification", "platform": "freeCodeCamp", "url": "https://www.freecodecamp.org/learn/scientific-computing-with-python/"},
            {"name": "Google IT Automation with Python", "platform": "Coursera", "url": "https://www.coursera.org/professional-certificates/google-it-automation"}
        ],
        "documentation": [
            {"name": "Python 3 Official Documentation & Tutorial", "platform": "Official Docs", "url": "https://docs.python.org/3/"},
            {"name": "The Hitchhiker's Guide to Python", "platform": "Official Docs", "url": "https://docs.python-guide.org/"}
        ],
        "youtube": [
            {"name": "Corey Schafer - Python Tutorials", "platform": "YouTube", "url": "https://www.youtube.com/@coreyms"},
            {"name": "freeCodeCamp.org - Full Python Course", "platform": "YouTube", "url": "https://www.youtube.com/@freecodecamp"}
        ],
        "certifications": [
            "PCEP - Certified Entry-Level Python Programmer (Python Institute)",
            "PCAP - Certified Associate in Python Programming (Python Institute)"
        ],
        "books": [
            {"name": "Automate the Boring Stuff with Python by Al Sweigart", "platform": "Authoritative Book", "url": "https://automatetheboringstuff.com/"},
            {"name": "Fluent Python by Luciano Ramalho", "platform": "Authoritative Book", "url": "https://www.goodreads.com/search?q=Fluent+Python"}
        ]
    },
    "javascript": {
        "courses": [
            {"name": "JavaScript Algorithms and Data Structures", "platform": "freeCodeCamp", "url": "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures-v8/"},
            {"name": "Meta Front-End Developer Professional Certificate", "platform": "Coursera", "url": "https://www.coursera.org/professional-certificates/meta-front-end-developer"},
            {"name": "The Complete JavaScript Course (Jonas Schmedtmann)", "platform": "Udemy", "url": "https://www.udemy.com/courses/search/?q=The+Complete+JavaScript+Course"}
        ],
        "documentation": [
            {"name": "MDN Web Docs - JavaScript Guide", "platform": "Official Docs", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript"},
            {"name": "JavaScript.info - The Modern JavaScript Tutorial", "platform": "Official Docs", "url": "https://javascript.info/"}
        ],
        "youtube": [
            {"name": "Traversy Media - Modern JavaScript Tutorials", "platform": "YouTube", "url": "https://www.youtube.com/@TraversyMedia"},
            {"name": "Fireship - 100 Seconds of Code & JS Guides", "platform": "YouTube", "url": "https://www.youtube.com/@Fireship"}
        ],
        "certifications": [
            "OpenJS Node.js Application Developer (JSNAD)",
            "W3C Front-End Web Developer Professional Certificate"
        ],
        "books": [
            {"name": "Eloquent JavaScript by Marijn Haverbeke", "platform": "Authoritative Book", "url": "https://eloquentjavascript.net/"},
            {"name": "You Don't Know JS Yet by Kyle Simpson", "platform": "Authoritative Book", "url": "https://github.com/getify/You-Dont-Know-JS"}
        ]
    },
    "react": {
        "courses": [
            {"name": "React Basics & Advanced React by Meta", "platform": "Coursera", "url": "https://www.coursera.org/learn/react-basics"},
            {"name": "Front End Development Libraries Certification", "platform": "freeCodeCamp", "url": "https://www.freecodecamp.org/learn/front-end-development-libraries/"}
        ],
        "documentation": [
            {"name": "React Official Documentation (react.dev)", "platform": "Official Docs", "url": "https://react.dev/"}
        ],
        "youtube": [
            {"name": "Web Dev Simplified - React Tutorials", "platform": "YouTube", "url": "https://www.youtube.com/@WebDevSimplified"},
            {"name": "Jack Herrington - React Architecture", "platform": "YouTube", "url": "https://www.youtube.com/@jherr"}
        ],
        "certifications": [
            "Meta Certified Front-End Developer",
            "Certified React Professional (OpenJS Foundation)"
        ],
        "books": [
            {"name": "Learning React by Alex Banks and Eve Porcello", "platform": "Authoritative Book", "url": "https://www.goodreads.com/search?q=Learning+React+Banks"}
        ]
    },
    "data science": {
        "courses": [
            {"name": "IBM Data Science Professional Certificate", "platform": "Coursera", "url": "https://www.coursera.org/professional-certificates/ibm-data-science"},
            {"name": "Machine Learning Specialization by Andrew Ng", "platform": "Coursera", "url": "https://www.coursera.org/specializations/machine-learning-introduction"},
            {"name": "Data Analysis with Python Certification", "platform": "freeCodeCamp", "url": "https://www.freecodecamp.org/learn/data-analysis-with-python/"}
        ],
        "documentation": [
            {"name": "Pandas & NumPy Official Documentation", "platform": "Official Docs", "url": "https://pandas.pydata.org/docs/"},
            {"name": "Scikit-Learn User Guide & API Docs", "platform": "Official Docs", "url": "https://scikit-learn.org/stable/"}
        ],
        "youtube": [
            {"name": "StatQuest with Josh Starmer", "platform": "YouTube", "url": "https://www.youtube.com/@statquest"},
            {"name": "3Blue1Brown - Neural Networks & Linear Algebra", "platform": "YouTube", "url": "https://www.youtube.com/@3blue1brown"},
            {"name": "Ken Jee - Data Science Career & Projects", "platform": "YouTube", "url": "https://www.youtube.com/@KenJee_ds"}
        ],
        "certifications": [
            "Google Cloud Professional Data Engineer",
            "IBM Certified Data Data Scientist",
            "Microsoft Certified: Azure Data Scientist Associate (DP-100)"
        ],
        "books": [
            {"name": "Python for Data Analysis by Wes McKinney", "platform": "Authoritative Book", "url": "https://wesmckinney.com/book/"},
            {"name": "Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow by Aurelien Geron", "platform": "Authoritative Book", "url": "https://www.goodreads.com/search?q=Hands-On+Machine+Learning+Geron"}
        ]
    },
    "machine learning": {
        "courses": [
            {"name": "Machine Learning Specialization (DeepLearning.AI)", "platform": "Coursera", "url": "https://www.coursera.org/specializations/machine-learning-introduction"},
            {"name": "Deep Learning Specialization (Andrew Ng)", "platform": "Coursera", "url": "https://www.coursera.org/specializations/deep-learning"},
            {"name": "Practical Deep Learning for Coders", "platform": "freeCodeCamp", "url": "https://course.fast.ai/"}
        ],
        "documentation": [
            {"name": "PyTorch Official Tutorials & Documentation", "platform": "Official Docs", "url": "https://pytorch.org/tutorials/"},
            {"name": "TensorFlow Official Guides", "platform": "Official Docs", "url": "https://www.tensorflow.org/tutorials"}
        ],
        "youtube": [
            {"name": "Andrej Karpathy - Neural Networks: Zero to Hero", "platform": "YouTube", "url": "https://www.youtube.com/@AndrejKarpathy"},
            {"name": "Yannic Kilcher - ML Paper Reviews", "platform": "YouTube", "url": "https://www.youtube.com/@YannicKilcher"}
        ],
        "certifications": [
            "TensorFlow Developer Certificate",
            "AWS Certified Machine Learning - Specialty",
            "Google Cloud Professional Machine Learning Engineer"
        ],
        "books": [
            {"name": "Deep Learning by Ian Goodfellow, Yoshua Bengio, and Aaron Courville", "platform": "Authoritative Book", "url": "https://www.deeplearningbook.org/"}
        ]
    },
    "cloud": {
        "courses": [
            {"name": "AWS Cloud Solutions Architect Specialization", "platform": "Coursera", "url": "https://www.coursera.org/specializations/aws-cloud-solutions-architect"},
            {"name": "AWS Certified Cloud Practitioner Full Course", "platform": "freeCodeCamp", "url": "https://www.freecodecamp.org/news/aws-certified-cloud-practitioner-study-course-pass-the-exam/"},
            {"name": "Google Cloud Architect Professional Certificate", "platform": "Coursera", "url": "https://www.coursera.org/professional-certificates/gcp-cloud-architect"}
        ],
        "documentation": [
            {"name": "Amazon Web Services (AWS) Documentation", "platform": "Official Docs", "url": "https://docs.aws.amazon.com/"},
            {"name": "Kubernetes Official Documentation", "platform": "Official Docs", "url": "https://kubernetes.io/docs/"}
        ],
        "youtube": [
            {"name": "TechWorld with Nana - DevOps & Cloud", "platform": "YouTube", "url": "https://www.youtube.com/@TechWorldwithNana"},
            {"name": "freeCodeCamp.org - Cloud Computing Certifications", "platform": "YouTube", "url": "https://www.youtube.com/@freecodecamp"}
        ],
        "certifications": [
            "AWS Certified Solutions Architect - Associate",
            "Microsoft Certified: Azure Fundamentals (AZ-900) & Administrator (AZ-104)",
            "Google Associate Cloud Engineer (ACE)",
            "CKA - Certified Kubernetes Administrator"
        ],
        "books": [
            {"name": "The Phoenix Project by Gene Kim, Kevin Behr, George Spafford", "platform": "Authoritative Book", "url": "https://www.goodreads.com/search?q=The+Phoenix+Project"},
            {"name": "Cloud Native Patterns by Cornelia Davis", "platform": "Authoritative Book", "url": "https://www.goodreads.com/search?q=Cloud+Native+Patterns"}
        ]
    },
    "cybersecurity": {
        "courses": [
            {"name": "Google Cybersecurity Professional Certificate", "platform": "Coursera", "url": "https://www.coursera.org/professional-certificates/google-cybersecurity"},
            {"name": "Information Security Certification", "platform": "freeCodeCamp", "url": "https://www.freecodecamp.org/learn/information-security/"},
            {"name": "IBM Cybersecurity Analyst Professional Certificate", "platform": "Coursera", "url": "https://www.coursera.org/professional-certificates/ibm-cybersecurity-analyst"}
        ],
        "documentation": [
            {"name": "OWASP Top 10 Security Risks", "platform": "Official Docs", "url": "https://owasp.org/www-project-top-ten/"},
            {"name": "NIST Cybersecurity Framework", "platform": "Official Docs", "url": "https://www.nist.gov/cyberframework"}
        ],
        "youtube": [
            {"name": "NetworkChuck - Cybersecurity, Linux & Networking", "platform": "YouTube", "url": "https://www.youtube.com/@NetworkChuck"},
            {"name": "Professor Messer - CompTIA Security+ Training", "platform": "YouTube", "url": "https://www.youtube.com/@professormesser"},
            {"name": "John Hammond - CTFs & Malware Analysis", "platform": "YouTube", "url": "https://www.youtube.com/@_JohnHammond"}
        ],
        "certifications": [
            "CompTIA Security+ (SY0-701)",
            "CEH (Certified Ethical Hacker) - EC-Council",
            "OSCP (Offensive Security Certified Professional)",
            "CISSP (Certified Information Systems Security Professional)"
        ],
        "books": [
            {"name": "The Web Application Hacker's Handbook by Dafydd Stuttard", "platform": "Authoritative Book", "url": "https://www.goodreads.com/search?q=The+Web+Application+Hacker's+Handbook"},
            {"name": "Practical Malware Analysis by Michael Sikorski", "platform": "Authoritative Book", "url": "https://www.goodreads.com/search?q=Practical+Malware+Analysis"}
        ]
    },
    "database": {
        "courses": [
            {"name": "Meta Database Engineer Professional Certificate", "platform": "Coursera", "url": "https://www.coursera.org/professional-certificates/meta-database-engineer"},
            {"name": "Relational Database Certification (PostgreSQL)", "platform": "freeCodeCamp", "url": "https://www.freecodecamp.org/learn/relational-database/"}
        ],
        "documentation": [
            {"name": "PostgreSQL Official Documentation", "platform": "Official Docs", "url": "https://www.postgresql.org/docs/"},
            {"name": "MySQL Reference Manual", "platform": "Official Docs", "url": "https://dev.mysql.com/doc/"}
        ],
        "youtube": [
            {"name": "Alex The Analyst - SQL Portfolio Projects", "platform": "YouTube", "url": "https://www.youtube.com/@AlexTheAnalyst"},
            {"name": "Luke Barousse - SQL for Data Analysts", "platform": "YouTube", "url": "https://www.youtube.com/@LukeBarousse"}
        ],
        "certifications": [
            "Oracle Certified Associate - Database SQL",
            "Microsoft Certified: Azure Database Administrator Associate (DP-300)"
        ],
        "books": [
            {"name": "SQL Antipatterns by Bill Karwin", "platform": "Authoritative Book", "url": "https://www.goodreads.com/search?q=SQL+Antipatterns"},
            {"name": "Database Internals by Alex Petrov", "platform": "Authoritative Book", "url": "https://www.goodreads.com/search?q=Database+Internals+Alex+Petrov"}
        ]
    },
    "system design": {
        "courses": [
            {"name": "Software Design and Architecture Specialization", "platform": "Coursera", "url": "https://www.coursera.org/specializations/software-design-architecture"}
        ],
        "documentation": [
            {"name": "The System Design Primer (by Donne Martin)", "platform": "GitHub", "url": "https://github.com/donnemartin/system-design-primer"}
        ],
        "youtube": [
            {"name": "ByteByteGo - System Design Architecture", "platform": "YouTube", "url": "https://www.youtube.com/@ByteByteGo"},
            {"name": "Gaurav Sen - Distributed Systems Design", "platform": "YouTube", "url": "https://www.youtube.com/@gkcs"}
        ],
        "certifications": [
            "AWS Certified Solutions Architect - Professional",
            "SEI Certified Software Architect (Carnegie Mellon)"
        ],
        "books": [
            {"name": "Designing Data-Intensive Applications by Martin Kleppmann", "platform": "Authoritative Book", "url": "https://www.goodreads.com/search?q=Designing+Data-Intensive+Applications"},
            {"name": "System Design Interview by Alex Xu", "platform": "Authoritative Book", "url": "https://www.goodreads.com/search?q=System+Design+Interview+Alex+Xu"}
        ]
    },
    "product management": {
        "courses": [
            {"name": "Google Project Management Professional Certificate", "platform": "Coursera", "url": "https://www.coursera.org/professional-certificates/google-project-management"},
            {"name": "Digital Product Management by University of Virginia", "platform": "Coursera", "url": "https://www.coursera.org/learn/uva-darden-digital-product-management"}
        ],
        "documentation": [
            {"name": "Product School Resources & Templates", "platform": "Official Docs", "url": "https://productschool.com/resources"}
        ],
        "youtube": [
            {"name": "Product School - Keynotes & PM Masterclasses", "platform": "YouTube", "url": "https://www.youtube.com/@ProductSchoolSanFrancisco"}
        ],
        "certifications": [
            "PMP - Project Management Professional (PMI)",
            "Certified Scrum Product Owner (CSPO) - Scrum Alliance",
            "CAPM - Certified Associate in Project Management"
        ],
        "books": [
            {"name": "Inspired: How to Create Tech Products Customers Love by Marty Cagan", "platform": "Authoritative Book", "url": "https://www.goodreads.com/search?q=Inspired+Marty+Cagan"},
            {"name": "Cracking the PM Interview by Gayle Laakmann McDowell", "platform": "Authoritative Book", "url": "https://www.goodreads.com/search?q=Cracking+the+PM+Interview"}
        ]
    },
    "ui ux": {
        "courses": [
            {"name": "Google UX Design Professional Certificate", "platform": "Coursera", "url": "https://www.coursera.org/professional-certificates/google-ux-design"},
            {"name": "UI / UX Design Specialization (CalArts)", "platform": "Coursera", "url": "https://www.coursera.org/specializations/ui-ux-design"}
        ],
        "documentation": [
            {"name": "Nielsen Norman Group UX Guidelines & Articles", "platform": "Official Docs", "url": "https://www.nngroup.com/articles/"},
            {"name": "Material Design Guidelines by Google", "platform": "Official Docs", "url": "https://m3.material.io/"}
        ],
        "youtube": [
            {"name": "DesignCourse - UI/UX Architecture & Figma", "platform": "YouTube", "url": "https://www.youtube.com/@DesignCourse"},
            {"name": "Mizko - Product Design Masterclasses", "platform": "YouTube", "url": "https://www.youtube.com/@mizko"}
        ],
        "certifications": [
            "Google Certified UX Designer",
            "Nielsen Norman Group UX Master Certification"
        ],
        "books": [
            {"name": "The Design of Everyday Things by Don Norman", "platform": "Authoritative Book", "url": "https://www.goodreads.com/search?q=The+Design+of+Everyday+Things"},
            {"name": "Don't Make Me Think by Steve Krug", "platform": "Authoritative Book", "url": "https://www.goodreads.com/search?q=Don%27t+Make+Me+Think"}
        ]
    },
    "finance": {
        "courses": [
            {"name": "Wharton Business and Financial Modeling Specialization", "platform": "Coursera", "url": "https://www.coursera.org/specializations/wharton-business-financial-modeling"},
            {"name": "Financial Markets by Yale University (Robert Shiller)", "platform": "Coursera", "url": "https://www.coursera.org/learn/financial-markets-global"}
        ],
        "documentation": [
            {"name": "Investopedia Financial Terminology & Guides", "platform": "Official Docs", "url": "https://www.investopedia.com/"}
        ],
        "youtube": [
            {"name": "Corporate Finance Institute (CFI) Tutorials", "platform": "YouTube", "url": "https://www.youtube.com/@CFI_Official"}
        ],
        "certifications": [
            "CFA - Chartered Financial Analyst (CFA Institute)",
            "FRM - Financial Risk Manager (GARP)",
            "CPA - Certified Public Accountant",
            "NCFM / NISM Certifications (India)"
        ],
        "books": [
            {"name": "The Intelligent Investor by Benjamin Graham", "platform": "Authoritative Book", "url": "https://www.goodreads.com/search?q=The+Intelligent+Investor"},
            {"name": "Valuation by McKinsey & Company", "platform": "Authoritative Book", "url": "https://www.goodreads.com/search?q=Valuation+McKinsey"}
        ]
    },
    "medical": {
        "courses": [
            {"name": "Harvard Medical School Online Learning Modules", "platform": "edX", "url": "https://online-learning.harvard.edu"},
            {"name": "Anatomy Specialization by University of Michigan", "platform": "Coursera", "url": "https://www.coursera.org/specializations/anatomy"}
        ],
        "documentation": [
            {"name": "World Health Organization (WHO) Clinical Guidelines", "platform": "Official Docs", "url": "https://www.who.int"},
            {"name": "PubMed Central (NCBI)", "platform": "Official Docs", "url": "https://pmc.ncbi.nlm.nih.gov"}
        ],
        "youtube": [
            {"name": "Ninja Nerd - Medicine & Physiology", "platform": "YouTube", "url": "https://www.youtube.com/@NinjaNerdOfficial"},
            {"name": "Osmosis from Elsevier - Clinical Pathology", "platform": "YouTube", "url": "https://www.youtube.com/@osmosis"}
        ],
        "certifications": [
            "BLS & ACLS (Basic & Advanced Cardiac Life Support) - AHA",
            "USMLE / PLAB / NEET PG Licensure",
            "Certified Electronic Health Records Specialist (CEHRS)"
        ],
        "books": [
            {"name": "Harrison's Principles of Internal Medicine", "platform": "Authoritative Book", "url": "https://www.goodreads.com/search?q=Harrison%27s+Principles+of+Internal+Medicine"},
            {"name": "Gray's Anatomy for Students", "platform": "Authoritative Book", "url": "https://www.goodreads.com/search?q=Gray%27s+Anatomy+for+Students"}
        ]
    }
}


def build_safe_platform_url(platform_name: str, resource_name: str = "") -> str:
    """
    Builds a reliable, working search or base URL for a vetted platform.
    Prevents hallucinating deep fake URLs that 404.
    """
    plat_key = (platform_name or "").strip().lower()
    meta = VERIFIED_PLATFORMS.get(plat_key)

    # Fuzzy platform match if not direct
    if not meta:
        for key, val in VERIFIED_PLATFORMS.items():
            if key in plat_key or plat_key in key:
                meta = val
                break

    if not meta:
        meta = VERIFIED_PLATFORMS["coursera"]  # Default reliable fallback

    clean_query = (resource_name or "").strip()
    # Remove generic qualifiers that pollute search
    for discard in ["Course", "Masterclass", "Tutorial", "Handbook", "Track", "Official"]:
        clean_query = clean_query.replace(f" {discard}", "")

    if clean_query:
        safe_q = urllib.parse.quote(clean_query)
        return meta["search_url"].format(query=safe_q)
    return meta["base_url"]


def normalize_platform_name(raw_platform: Optional[str]) -> str:
    """Normalizes any platform string to a vetted canonical platform name."""
    if not raw_platform:
        return "Coursera"
    plat_low = raw_platform.lower().strip()
    for key, meta in VERIFIED_PLATFORMS.items():
        if key in plat_low or plat_low in key:
            return meta["name"]
    return "Coursera"


def get_matching_domain_keys(career_text: str, skills_text: str = "") -> List[str]:
    """Identifies matching domain keys from the curated registry."""
    combined = f"{career_text} {skills_text}".lower()
    matches = []

    keyword_map = {
        "python": ["python", "django", "flask", "fastapi", "backend python"],
        "javascript": ["javascript", "js", "web dev", "frontend", "front-end", "node", "typescript"],
        "react": ["react", "next.js", "nextjs", "redux"],
        "data science": ["data scientist", "data science", "data analyst", "analytics", "pandas", "numpy"],
        "machine learning": ["machine learning", "ml", "ai engineer", "deep learning", "nlp", "computer vision", "llm"],
        "cloud": ["cloud", "aws", "azure", "gcp", "devops", "kubernetes", "docker", "sre"],
        "cybersecurity": ["security", "cyber", "penetration", "soc", "ethical hack", "infosec"],
        "database": ["database", "sql", "postgres", "mysql", "dba", "data engineer"],
        "system design": ["system design", "software engineer", "architect", "distributed systems", "backend"],
        "product management": ["product manager", "pm", "scrum", "agile", "project manager"],
        "ui ux": ["ui", "ux", "designer", "figma", "user experience", "product design"],
        "finance": ["finance", "bank", "analyst", "investment", "accounting", "chartered"],
        "medical": ["doctor", "surgeon", "medicine", "nurse", "physician", "clinical"]
    }

    for domain_key, triggers in keyword_map.items():
        if any(tr in combined for tr in triggers):
            matches.append(domain_key)

    return matches or ["system design"]


def get_curated_resources_for_skills(career: str, skills: str = "") -> Dict[str, List[Dict[str, str]]]:
    """
    Returns verified curated resources covering courses, docs, youtube, and books
    for the detected career and skills.
    """
    domain_keys = get_matching_domain_keys(career, skills)
    
    courses, docs, youtube, books, certs = [], [], [], [], []
    seen_names = set()

    for d_key in domain_keys:
        d_res = CURATED_SKILL_RESOURCES.get(d_key, {})
        for c in d_res.get("courses", []):
            if c["name"] not in seen_names:
                courses.append(c)
                seen_names.add(c["name"])
        for d in d_res.get("documentation", []):
            if d["name"] not in seen_names:
                docs.append(d)
                seen_names.add(d["name"])
        for y in d_res.get("youtube", []):
            if y["name"] not in seen_names:
                youtube.append(y)
                seen_names.add(y["name"])
        for b in d_res.get("books", []):
            if b["name"] not in seen_names:
                books.append(b)
                seen_names.add(b["name"])
        for ct in d_res.get("certifications", []):
            if ct not in seen_names:
                certs.append(ct)
                seen_names.add(ct)

    return {
        "courses": courses[:5],
        "documentation": docs[:5],
        "youtube": youtube[:5],
        "books": books[:5],
        "certifications": certs[:5]
    }


def enrich_and_sanitize_roadmap_resources(resources_dict: Any, career: str, skills: str = "") -> Dict[str, List[Dict[str, str]]]:
    """
    Sanitizes LLM resource recommendations for /roadmap:
    1. Removes any hallucinated/fake deep URLs.
    2. Enforces verified platforms only.
    3. Replaces URLs with verified links or reliable platform search URLs.
    4. Merges in curated skill resources to ensure at least 3-5 verified items per category.
    """
    curated = get_curated_resources_for_skills(career, skills)
    output: Dict[str, List[Dict[str, str]]] = {
        "courses": [],
        "documentation": [],
        "youtube": [],
        "books": []
    }

    raw_resources = resources_dict if isinstance(resources_dict, dict) else {}

    for cat in ["courses", "documentation", "youtube", "books"]:
        raw_list = raw_resources.get(cat, [])
        cat_items: List[Dict[str, str]] = []
        seen = set()

        if isinstance(raw_list, list):
            for item in raw_list:
                if isinstance(item, dict):
                    name = str(item.get("name") or item.get("title") or "").strip()
                    raw_plat = str(item.get("platform") or "").strip()
                    if not raw_plat:
                        # Infer platform if not explicitly given
                        if cat == "youtube":
                            raw_plat = "YouTube"
                        elif cat == "courses":
                            raw_plat = "Coursera"
                        elif cat == "documentation":
                            raw_plat = "Official Docs"
                        elif cat == "books":
                            raw_plat = "Authoritative Book"
                        else:
                            raw_plat = "Coursera"
                    
                    plat_canon = normalize_platform_name(raw_plat)
                    if name and name.lower() not in seen:
                        # Build guaranteed-safe working URL (no hallucinated deep links)
                        safe_url = build_safe_platform_url(plat_canon, name)
                        cat_items.append({
                            "name": name,
                            "platform": plat_canon,
                            "url": safe_url
                        })
                        seen.add(name.lower())
                elif isinstance(item, str) and item.strip():
                    name = item.strip()
                    plat = "YouTube" if cat == "youtube" else ("Official Docs" if cat == "documentation" else "Coursera")
                    if name.lower() not in seen:
                        cat_items.append({
                            "name": name,
                            "platform": plat,
                            "url": build_safe_platform_url(plat, name)
                        })
                        seen.add(name.lower())

        # Backfill from curated resources if category has fewer than 3 items
        for cur_item in curated.get(cat, []):
            if cur_item["name"].lower() not in seen and len(cat_items) < 5:
                cat_items.append({
                    "name": cur_item["name"],
                    "platform": cur_item.get("platform", "Coursera"),
                    "url": cur_item.get("url") or build_safe_platform_url(cur_item.get("platform", "Coursera"), cur_item["name"])
                })
                seen.add(cur_item["name"].lower())

        output[cat] = cat_items

    return output


def enrich_and_sanitize_navigator_roadmap(roadmap_data: Dict[str, Any], career: str, skills: str = "") -> Dict[str, Any]:
    """
    Sanitizes phase-level resources in /navigator-roadmap-api:
    - Replaces direct LLM URLs with safe verified platform URLs.
    - Supplements with curated resources matching each phase's skills.
    """
    if not isinstance(roadmap_data, dict):
        return roadmap_data

    curated = get_curated_resources_for_skills(career, skills)
    phases = roadmap_data.get("phases", [])
    if not isinstance(phases, list):
        return roadmap_data

    cur_courses = curated.get("courses", [])
    cur_docs = curated.get("documentation", [])
    cur_yt = curated.get("youtube", [])

    for idx, phase in enumerate(phases):
        if not isinstance(phase, dict):
            continue

        raw_res = phase.get("resources", [])
        sanitized_res = []
        seen = set()

        if isinstance(raw_res, list):
            for r in raw_res:
                if isinstance(r, dict):
                    name = str(r.get("name") or "").strip()
                    plat = normalize_platform_name(r.get("platform") or r.get("type"))
                    if name and name.lower() not in seen:
                        sanitized_res.append({
                            "name": name,
                            "platform": plat,
                            "url": build_safe_platform_url(plat, name)
                        })
                        seen.add(name.lower())
                elif isinstance(r, str) and r.strip():
                    name = r.strip()
                    plat = "Coursera" if "course" in name.lower() else "Official Docs"
                    if name.lower() not in seen:
                        sanitized_res.append({
                            "name": name,
                            "platform": plat,
                            "url": build_safe_platform_url(plat, name)
                        })
                        seen.add(name.lower())

        # Ensure at least 3 high-quality resources per phase from curated bank
        phase_fallbacks = []
        if idx == 0:
            phase_fallbacks = cur_docs[:1] + cur_courses[:1] + cur_yt[:1]
        elif idx == 1:
            phase_fallbacks = cur_courses[:2] + cur_docs[:1]
        elif idx == 2:
            phase_fallbacks = cur_courses[1:3] + cur_yt[:1]
        else:
            phase_fallbacks = cur_courses[:1] + cur_docs[:1] + cur_yt[:1]

        for fb in phase_fallbacks:
            if len(sanitized_res) < 3 and fb["name"].lower() not in seen:
                sanitized_res.append({
                    "name": fb["name"],
                    "platform": fb.get("platform", "Coursera"),
                    "url": fb.get("url") or build_safe_platform_url(fb.get("platform", "Coursera"), fb["name"])
                })
                seen.add(fb["name"].lower())

        phase["resources"] = sanitized_res[:4]

    return roadmap_data


def enrich_gap_analysis_resources(career: str, user_skills: str = "") -> Dict[str, Any]:
    """
    Returns curated, non-hallucinated course, doc, and certification recommendations
    for skill gap endpoints.
    """
    curated = get_curated_resources_for_skills(career, user_skills)
    courses_formatted = [
        {
            "name": c["name"],
            "platform": c.get("platform", "Coursera"),
            "url": c.get("url") or build_safe_platform_url(c.get("platform", "Coursera"), c["name"])
        }
        for c in curated.get("courses", [])
    ]
    docs_formatted = [
        {
            "name": d["name"],
            "platform": d.get("platform", "Official Docs"),
            "url": d.get("url") or build_safe_platform_url(d.get("platform", "Official Docs"), d["name"])
        }
        for d in curated.get("documentation", [])
    ]

    return {
        "recommended_courses": courses_formatted[:4],
        "recommended_docs": docs_formatted[:3],
        "recommended_certifications": curated.get("certifications", [])[:4]
    }
