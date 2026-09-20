# CareerVerse AI - Security Architecture & Confidential Computing Specification

## 1. Overview & Security Philosophy

CareerVerse AI is an AI-powered career intelligence and guidance platform. Users entrust CareerVerse with sensitive personal and professional data—including comprehensive resumes, employment histories, contact information, target aspirations, and career concerns.

Our core security philosophy is **Zero-Trust & Zero-Knowledge Architecture**:
- Sensitive data is isolated in memory and minimized before any external processing.
- Raw resumes are processed as ephemeral in-memory byte streams (`io.BytesIO`) with **zero disk retention**.
- Personally Identifiable Information (PII) is automatically redacted before prompts reach third-party Large Language Model APIs.
- The system employs a modular **Confidential Computing / Trusted Execution Environment (TEE)** provider abstraction designed to run inside hardware-isolated enclaves (such as AWS Nitro Enclaves, AMD SEV-SNP, or Google Cloud Confidential VMs).
- **Honest Security Claims**: CareerVerse AI strictly adheres to technical truth. Hardware-backed TEE protection is never claimed unless running on verified, attestation-validated confidential hardware. In local development or standard cloud environments, the system transparently indicates that software simulation mode is active.

---

## 2. What is a Trusted Execution Environment (TEE)?

A **Trusted Execution Environment (TEE)** is a hardware-enforced, isolated execution space within a processor that provides:
1. **Confidentiality**: Memory is encrypted at the hardware controller level using ephemeral keys (e.g., AMD SEV-SNP, Intel SGX/TDX, AWS Nitro Enclaves). Even root administrators of the host operating system, hypervisors, and cloud providers cannot inspect data in memory.
2. **Integrity**: The code executing inside the enclave cannot be altered or hijacked by external processes.
3. **Cryptographic Attestation**: The hardware security module (e.g. AWS Nitro Security Module `NSM`) cryptographically signs a measurement of the enclave image (Platform Configuration Registers: PCR0 for image, PCR1 for kernel, PCR2 for app) alongside a cryptographic challenge nonce, proving to external parties that the authentic code is running untampered inside the hardware enclave.

---

## 3. Why CareerVerse AI Uses Confidential Computing

Traditional cloud web applications expose data in three states:
- **Data in Transit**: Protected by TLS 1.3 / HTTPS.
- **Data at Rest**: Protected by AES-256 disk encryption (LUKS / AWS EBS encryption).
- **Data in Use (Memory)**: **Vulnerable in standard architectures!** When a resume is decrypted and processed in host RAM, malicious host processes, memory scrapers, compromised cloud hypervisors, or rogue infrastructure administrators can inspect plaintext PII.

**Confidential Computing closes the "Data in Use" vulnerability gap**:
By routing resume parsing, PII redaction, and cryptographic key operations into a hardware-isolated enclave, CareerVerse ensures user resumes and contact information are protected even while actively being computed in memory.

---

## 4. Data Classification

| Data Classification | Examples in CareerVerse | Protection Mechanisms |
| :--- | :--- | :--- |
| **High Sensitivity (PII & Secrets)** | Candidate full names, personal emails, phone numbers, home addresses, government IDs (Aadhaar, PAN, SSN), Gemini API keys, session secrets. | In-memory processing only, ephemeral AES-256-GCM cipher, automatic PII redaction, zero disk retention, zero logging, strictly server-side secret management. |
| **Medium Sensitivity (Career Context)** | Academic degrees, GPAs, project descriptions, target job roles, salary queries, interview chat messages. | Session-isolated memory, rate limiting, validated input schemas, sanitized error reporting. |
| **Low Sensitivity (Public Benchmarks)** | Standard career taxonomies, official labor market salary datasets, cost of living index tables, currency conversion rates. | Cached in-memory JSON data layers, read-only distribution. |

---

## 5. End-to-End Data Flow

```
[User Browser]
      │
      │ 1. HTTPS Upload (PDF Stream <= 10MB)
      ▼
[Flask API Gateway & Middleware]
      │ - Rate limiter check (sliding-window: 15 req/min)
      │ - MIME & Magic Byte validation (%PDF-)
      │ - Security Headers injected
      ▼
[Secure Processing Layer: ISecureProvider]
      │
      ├── (Production TEE) ──► [AWS Nitro Enclave via AF_VSOCK (Port 5000)]
      │                        │ - Hypervisor hardware memory encryption
      │                        │ - NSM cryptographic attestation
      │                        │ - In-enclave PII Redactor
      │                        │ - In-enclave ephemeral memory cipher
      │                        ▼
      └── (Local Dev) ───────► [LocalDevelopmentProvider]
                               │ - In-memory software enclave simulation
                               │ - In-memory PII Redactor
                               │ - In-memory ephemeral cipher
                               │ - Transparent non-hardware declaration
                               ▼
[PII Minimization Engine]
      │ - Redacts names, emails, phones, IDs, addresses
      │ - Preserves technical skills, degrees, metrics
      ▼
[External AI Inference Gateway (Server-Side)]
      │ - Sends sanitized, de-identified prompt to Google Gemini
      │ - Gemini API key stored strictly server-side
      ▼
[Result Harmonization & Memory Shredding]
      │ - In-memory buffers overwritten with zeros
      │ - Temporary streams closed and discarded
      ▼
[Safe Client Response]
      │ - Structured evaluation JSON
      │ - Verified security metadata & honest display badge
      ▼
[User Browser Results Dashboard]
```

---

## 6. Personally Identifiable Information (PII) Protection

### PII Redaction Rules
CareerVerse's deterministic `PIIRedactor` automatically scrubs:
- **Names**: Prominent candidate names or explicit labels (`Name: ...`) -> `[REDACTED_NAME]`
- **Emails**: RFC-compliant email regex -> `[REDACTED_EMAIL]`
- **Phones**: Indian mobile (`+91 9876543210`), US/Canada `(123) 456-7890`, and international phone patterns -> `[REDACTED_PHONE]`
- **Government IDs**: Aadhaar (`XXXX XXXX XXXX`), PAN, SSN -> `[REDACTED_AADHAAR]`, `[REDACTED_PAN]`, `[REDACTED_SSN]`
- **Social Handles**: Personal usernames on LinkedIn and GitHub -> `[REDACTED_PROFILE]`, `[REDACTED_REPO_USER]` (preserving domain presence for portfolio proof)
- **Postal Codes**: PIN and ZIP codes -> `[REDACTED_PIN]`

### Competency & Metric Preservation
Crucially, `PIIRedactor` **never** removes or corrupts:
- Programming languages (`Python`, `C++`, `Java`, `TypeScript`, `Go`, `Rust`)
- Frameworks (`React`, `Node.js`, `Docker`, `Kubernetes`, `AWS`, `GCP`)
- Academic qualifications (`B.Tech CSE`, `M.S. Data Science`, `Ph.D.`, `MBBS`)
- Measurable achievements (`"Reduced latency by 42%"`, `"Served 100k daily requests"`, `"8.8 CGPA"`)
- Target job titles and industry keywords

---

## 7. Secret Management & Key Security

1. **No Frontend Secrets**: The Gemini API key (`GEMINI_API_KEY`) is strictly accessed on the server. No client JavaScript or template ever receives or renders the API key.
2. **Environment Variable Injection**: All secrets are loaded via environment variables or cloud secret managers (e.g. AWS Secrets Manager, GCP Secret Manager).
3. **Log Sanitization**: `SecurityAuditLogger` scans every log entry through regex filters, automatically scrubbing `AIzaSy...` patterns and auth tokens before writing to logs.
4. **Sanitized Error Messages**: In `handle_gemini_error`, raw exceptions that could contain internal filesystem paths or API tokens are scrubbed. The user receives a safe, generic message while safe diagnostic codes are retained in server logs.

---

## 8. Cryptographic Implementation

- **Algorithm**: Authenticated Encryption with Associated Data (AEAD) using **AES-256-GCM**.
- **Key Derivation**: **HKDF-SHA256** (HMAC-based Extract-and-Expand Key Derivation Function) with cryptographically secure salt.
- **Nonce Generation**: 96-bit cryptographically secure pseudorandom nonces (`os.urandom(12)`) per encryption operation.
- **Memory Shredding**: Ephemeral mutable memory buffers (`bytearray`) are overwritten with zeros prior to deallocation to mitigate memory remanence.

---

## 9. TEE Provider Abstraction & Modularity

The application code depends exclusively on `ISecureProvider` via `secure_processing.get_secure_provider()`:

```python
from secure_processing import process_sensitive_data, get_security_status

# Application remains agnostic to hardware vs local execution
sec_res = process_sensitive_data(resume_text, options={"target_role": target_role})
sanitized_text = sec_res["processed_text"]
```

### Configured Modes (`SECURITY_MODE`):
- `auto` (Default): Automatically detects if an AWS Nitro Enclave or Confidential VM is reachable. If detected, activates hardware TEE; otherwise initializes `LocalDevelopmentProvider`.
- `tee_enclave`: Connects to the AWS Nitro Enclave microservice over `AF_VSOCK`.
- `local_dev`: Forces the software-isolated local development provider.

---

## 10. Local Development vs. Production TEE Comparison

| Feature | Local Development Mode (`local_provider.py`) | Production Hardware TEE (`tee_provider.py`) |
| :--- | :--- | :--- |
| **Execution Environment** | Standard Host OS (Windows / macOS / Linux) | AWS Nitro Enclave / AMD SEV-SNP Confidential VM |
| **Hardware Memory Encryption** | ❌ No (Standard RAM) | ✅ Yes (Hypervisor-enforced memory controller encryption) |
| **Network Isolation** | ❌ Shared Host Network | ✅ Total Network Isolation (No external IP / AF_VSOCK only) |
| **Cryptographic Attestation** | ⚠️ Simulated Diagnostic (Declared Non-Hardware) | ✅ Authentic NSM Hardware Attestation (Signed by AWS Root CA) |
| **PII Redaction & Minimization** | ✅ Fully Active | ✅ Fully Active (Runs inside Enclave) |
| **Zero Disk Retention** | ✅ In-memory `io.BytesIO` | ✅ In-memory `io.BytesIO` |
| **UI Display Badge** | `"Secure Processing: Development Mode"` | `"Confidential Computing: Hardware TEE Active"` |

---

## 11. Production Deployment Requirements

To run CareerVerse AI with true hardware-backed TEE:
1. **Cloud Instance**: Deploy on an AWS Nitro-supported EC2 instance (e.g. `c6i.xlarge`, `m6i.xlarge`) with Nitro Enclaves enabled.
2. **Enclave Build**:
   ```bash
   bash secure_processing/enclave_app/run_enclave.sh
   ```
3. **Environment Variables**:
   ```env
   SECURITY_MODE=tee_enclave
   NITRO_ENCLAVE_CID=16
   NITRO_ENCLAVE_PORT=5000
   ```
4. **Attestation Validation**: The host verifies that PCR0, PCR1, and PCR2 match the authorized build hash before dispatching sensitive payloads over `AF_VSOCK`.

---

## 12. Threat Model (STRIDE Analysis)

| Threat Category | Potential Risk | CareerVerse Mitigation |
| :--- | :--- | :--- |
| **Spoofing** | Unauthorized clients impersonating legitimate users or spoofing attestation. | Cryptographically signed sessions, rate limiting, and hardware NSM signature verification on attestation documents. |
| **Tampering** | Modifying encrypted memory buffers or altering resumes during transit. | TLS 1.3 in transit; AES-256-GCM 128-bit authentication tags detect any ciphertext tampering; immutable EIF hashes in TEE. |
| **Repudiation** | Denying security policy actions or rate limit abuse. | Immutable, zero-PII structured security audit logs (`SecurityAuditLogger`) with timestamps and client hashes. |
| **Information Disclosure** | Leakage of candidate PII to external AI APIs, logs, or disk. | In-memory stream processing (zero disk retention), PII redaction engine, regex log scrubber, sanitized error messages. |
| **Denial of Service (DoS)** | Uploading massive PDF files or spamming AI endpoints to exhaust quotas. | 10MB maximum content limit (`MAX_CONTENT_LENGTH`), magic-byte inspection (`%PDF-`), and sliding-window rate limiters. |
| **Elevation of Privilege** | Host root compromise inspecting application memory. | Hardware TEE (AWS Nitro Enclaves) isolates memory from the host operating system and root users entirely. |

---

## 13. Security Assumptions & Residual Risks

1. **Third-Party AI Model Trust Boundary**: CareerVerse de-identifies PII before transmitting prompts to Gemini. However, the external LLM provider still processes the sanitized career experience text.
2. **Client-Side Security**: If the user's personal workstation is infected with malware or screen scrapers, input can be intercepted before reaching CareerVerse over HTTPS.
3. **Development Mode Caveat**: When running in `development_isolated` mode, security relies on operating system memory boundaries rather than cryptographic hardware enclaves. Production environments must configure `SECURITY_MODE=tee_enclave`.
