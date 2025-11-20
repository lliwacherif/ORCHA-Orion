# ORCHA Document Verification Workflow

## Overview
This guide explains how ORCHA processes user-submitted documents (PDF, DOC, images) to verify identity or financial data, such as IBAN, passports, licenses, or insurance vouchers. The flow combines ingestion, OCR, parsing, validation, and reporting to determine document legitimacy.

---

## High-Level Flow
1. **Upload**
   - User attaches files via the frontend (PDF, DOC, DOCX, PNG, JPG, etc.).
   - Frontend sends the file metadata and base64 data to the backend endpoint POST /api/v1/orcha/chat or /orcha/ocr/extract depending on the context.

2. **Routing**
   - ORCHA inspects the payload and determines whether to send the document for:
     - **Direct OCR extraction** (if base64 image or PDF with text content).
     - **OCR queue** (if large files or remote URIs requiring asynchronous processing).
     - **RAG ingestion** (if the document must be stored for retrieval).

3. **Extraction**
   - extract_pdf_text() handles PDF files with embedded text.
   - call_ocr() or extract_text_from_image() processes images or scanned PDFs to extract text.
   - The extracted text is appended to the user message as context.

4. **Normalization**
   - Text is cleaned (remove headers, footers, watermarks) to improve accuracy.
   - 	runcate_memory_to_tokens() keeps text within token limits.

5. **Verification Logic**
   - ORCHA applies specific checks based on document type:
     - **IBAN validation**: alidate_iban_format() ensures structure, checksum, and country code.
     - **Passport validation**: check_passport_mrz() evaluates the machine-readable zone for checksum accuracy.
     - **Identity matching**: compare_user_metadata() compares extracted names, birthdates, or ID numbers with account data.
     - **Document metadata**: inspect_document_properties() checks issuance date, expiration, issuing authority.
   - These checks occur inside the orchestrator before calling the LLM.

6. **LLM Analysis**
   - The orchestrator builds a prompt combining:
     - Extracted text.
     - Document metadata (type, filename, detected fields).
     - Verification results (e.g., IBAN checksum failure).
   - The prompt is sent to the LLM via call_lmstudio_chat() to produce a human-readable explanation.

7. **Risk Scoring**
   - Optional stage where calculate_risk_score() returns low/medium/high based on discrepancies or mismatched fields.

8. **Response Assembly**
   - The orchestrator returns a structured response:
     - Summary of the analysis.
     - Pass/fail status or confidence.
     - List of detected issues (e.g., IBAN invalid, passport expired).
     - Token usage and trace information.

9. **Storage & Audit**
   - Conversation stored in ChatMessage table (ole=user, ole=assistant).
   - Documents ingested into RAG for future traces (optional).
   - PostgreSQLTokenTracker records token usage for billing.

---

## Example Scenario: IBAN Verification
1. User uploads a PDF bank statement containing an IBAN.
2. PDF passes through extract_pdf_text().
3. alidate_iban_format() extracts the IBAN and runs the checksum.
4. ORCHA compares the IBAN with account records via compare_user_metadata().
5. LLM summarizes findings: "IBAN valid and matches registered account" or details discrepancies.
6. Response returned to frontend for user confirmation.

---

## Example Scenario: Passport Check
1. User uploads a passport image (JPG).
2. Image passes through extract_text_from_image() to OCR the MRZ.
3. check_passport_mrz() validates the MRZ checksums.
4. A compare_user_metadata() check ensures the passport belongs to the account holder.
5. LLM produces a summary noting validity, expiration date, and identity match results.
6. Frontend displays results and offers next steps.

---

## Key Considerations
- **Timeouts**: ensure LM timeout (LM_TIMEOUT) matches proxy/ingress timeout.
- **Security**: sanitize documents; ensure GDPR compliance when storing.
- **Logging**: enable detailed logs for auditing decisions.
- **Error handling**: graceful fallbacks if OCR fails or documents unreadable.
- **Token usage**: monitor for large document batches.

---

## Future Enhancements
- Integrate dedicated validators for regional IDs (e.g., national IDs, driver licenses).
- Add confidence scores per extracted field.
- Automate rejections/approvals based on rules engine.
- Support digital signatures verification.

---

## Summary
By combining OCR, structured validation, and LLM reasoning, ORCHA evaluates uploaded documents for authenticity and consistency. Each stage—from ingestion to response—ensures that users receive clear guidance about whether their files are legitimate and what issues (if any) were detected.
