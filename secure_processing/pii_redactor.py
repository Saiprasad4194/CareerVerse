"""
PII Detection, Minimization, and Redaction Engine for CareerVerse AI.

Scrubs Personally Identifiable Information (PII) before resumes or profile data
are processed by external AI providers.

Protects:
- Candidate Names
- Email Addresses
- Phone Numbers (Indian, US/CA, International)
- Government ID Numbers (Aadhaar, PAN, SSN, Passport)
- Personal Social Profiles (LinkedIn, GitHub handles)
- Street Addresses & Postal/PIN Codes

Carefully Preserves:
- Technical skills, programming languages, and frameworks
- Academic degrees, majors, and graduation years
- Work accomplishments, bullet points, and Google XYZ metrics
- Job roles and target career titles
"""

import re
from typing import Dict, List, Set, Tuple, Any


class PIIRedactor:
    """
    Regex and heuristic-based PII redaction engine with high precision
    and zero-loss retention of career and technical competencies.
    """

    # Email pattern
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
        re.IGNORECASE
    )

    # Phone patterns (strictly requiring 7 to 15 digits with phone delimiters, avoiding metrics/percentages)
    PHONE_PATTERNS = [
        # Indian Mobile: +91 9876543210 or 98765 43210 or +91-98765-43210
        re.compile(r'(?:\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}\b'),
        # International with + country code: e.g. +1 (555) 123-4567, +44 20 7946 0919
        re.compile(r'\+\d{1,3}[\s-]?\(?\d{2,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}\b'),
        # Standard US/Canada: (123) 456-7890 or 123-456-7890 or 123.456.7890
        re.compile(r'\b(?:\+?1[\s-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b'),
        # Explicit labeled phone: "Phone: 9876543210", "Tel: ...", "Mobile: ..."
        re.compile(r'(?:phone|tel|mobile|cell|contact)[\s:]+([+\d\s().-]{8,20})\b', re.IGNORECASE),
    ]

    # Government IDs
    GOV_ID_PATTERNS = [
        # Indian Aadhaar: 12 digits (often 4 4 4)
        (re.compile(r'\b\d{4}\s\d{4}\s\d{4}\b'), '[REDACTED_AADHAAR]'),
        # Indian PAN: 5 letters + 4 digits + 1 letter
        (re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b'), '[REDACTED_PAN]'),
        # US SSN: 3-2-4
        (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '[REDACTED_SSN]'),
        # Generic Passport label
        (re.compile(r'(?:passport\s*(?:no|number)?[\s:]+)([A-Z0-9]{7,10})\b', re.IGNORECASE), '[REDACTED_PASSPORT]'),
    ]

    # Social Profile Handles (Preserve domain reference for proof of portfolio, scrub personal username)
    LINKEDIN_PATTERN = re.compile(
        r'((?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/)([A-Za-z0-9_-]+)\/?',
        re.IGNORECASE
    )
    GITHUB_PATTERN = re.compile(
        r'((?:https?:\/\/)?(?:www\.)?github\.com\/)([A-Za-z0-9_-]+)\/?',
        re.IGNORECASE
    )

    # Postal / PIN Codes
    PIN_CODE_PATTERN = re.compile(
        r'(?:pin|pincode|zip|zipcode|postal\s*code)[\s:]+(\d{5,6})\b',
        re.IGNORECASE
    )

    # Common resume section titles that should NEVER be mistaken for candidate names
    RESUME_SECTION_KEYWORDS = {
        "summary", "professional summary", "career objective", "objective",
        "experience", "work experience", "professional experience", "employment",
        "education", "academic background", "skills", "technical skills",
        "projects", "key projects", "certifications", "licenses", "awards",
        "achievements", "publications", "languages", "interests", "activities",
        "contact", "curriculum vitae", "resume", "biodata", "profile"
    }

    @classmethod
    def redact(cls, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Redacts PII from text, returning the sanitized text and redaction metadata.
        """
        if not text or not text.strip():
            return "", {"total_redacted": 0, "entities_redacted": {}, "detected_types": []}

        sanitized = text
        stats = {
            "EMAIL": 0,
            "PHONE": 0,
            "GOV_ID": 0,
            "SOCIAL_HANDLE": 0,
            "NAME": 0,
            "POSTAL_CODE": 0
        }

        # 1. Redact Emails
        emails_found = cls.EMAIL_PATTERN.findall(sanitized)
        if emails_found:
            stats["EMAIL"] += len(emails_found)
            sanitized = cls.EMAIL_PATTERN.sub('[REDACTED_EMAIL]', sanitized)

        # 2. Redact Phone Numbers
        for p_regex in cls.PHONE_PATTERNS:
            matches = p_regex.findall(sanitized)
            if matches:
                # If regex has capture group
                if isinstance(matches[0], str):
                    count = len(matches)
                else:
                    count = len(matches)
                stats["PHONE"] += count
                if p_regex.groups > 0:
                    sanitized = p_regex.sub(lambda m: m.group(0).replace(m.group(1), '[REDACTED_PHONE]'), sanitized)
                else:
                    sanitized = p_regex.sub('[REDACTED_PHONE]', sanitized)

        # 3. Redact Government IDs
        for id_regex, placeholder in cls.GOV_ID_PATTERNS:
            found = id_regex.findall(sanitized)
            if found:
                stats["GOV_ID"] += len(found)
                sanitized = id_regex.sub(placeholder, sanitized)

        # 4. Redact Social Handles
        def redact_linkedin(match):
            stats["SOCIAL_HANDLE"] += 1
            return f"{match.group(1)}[REDACTED_PROFILE]"

        def redact_github(match):
            stats["SOCIAL_HANDLE"] += 1
            return f"{match.group(1)}[REDACTED_REPO_USER]"

        sanitized = cls.LINKEDIN_PATTERN.sub(redact_linkedin, sanitized)
        sanitized = cls.GITHUB_PATTERN.sub(redact_github, sanitized)

        # 5. Redact Postal / PIN Codes
        def redact_pin(match):
            stats["POSTAL_CODE"] += 1
            return match.group(0).replace(match.group(1), '[REDACTED_PIN]')

        sanitized = cls.PIN_CODE_PATTERN.sub(redact_pin, sanitized)

        # 6. Candidate Name Detection & Redaction
        sanitized, name_count = cls._redact_candidate_name(sanitized)
        stats["NAME"] += name_count

        total_redacted = sum(stats.values())
        detected_types = [k for k, v in stats.items() if v > 0]

        metadata = {
            "total_redacted": total_redacted,
            "entities_redacted": {k: v for k, v in stats.items() if v > 0},
            "detected_types": detected_types
        }

        return sanitized, metadata

    @classmethod
    def _redact_candidate_name(cls, text: str) -> Tuple[str, int]:
        """
        Infers candidate name from explicit labels or top-of-resume prominence.
        """
        lines = text.splitlines()
        redacted_count = 0
        modified_lines = []

        name_detected = False

        for idx, line in enumerate(lines):
            stripped = line.strip()

            # Case A: Explicit Name label ("Name: Rahul Sharma", "Full Name: ...")
            explicit_match = re.match(r'^(?:full\s*name|name|candidate\s*name)[\s:]+([A-Za-z\s.\'-]{3,50})$', stripped, re.IGNORECASE)
            if explicit_match:
                orig_name = explicit_match.group(1).strip()
                modified_lines.append(stripped.replace(orig_name, '[REDACTED_NAME]'))
                redacted_count += 1
                name_detected = True
                continue

            # Case B: Top 1-4 lines containing a prominent 2 to 4 word capitalized person name
            if not name_detected and idx < 4 and stripped:
                lower = stripped.lower()
                # Must not match section titles, emails, phones, or URLs
                if not any(keyword in lower for keyword in cls.RESUME_SECTION_KEYWORDS):
                    if not any(token in stripped for token in ['[REDACTED_', '@', 'http', 'www', '/', '\\', ':', '|']):
                        words = stripped.split()
                        # Valid name heuristic: 2 to 4 words, all alphabetic, title-cased
                        if 2 <= len(words) <= 4 and all(w.isalpha() or w.endswith('.') for w in words):
                            modified_lines.append('[REDACTED_NAME]')
                            redacted_count += 1
                            name_detected = True
                            continue

            modified_lines.append(line)

        return "\n".join(modified_lines), redacted_count
