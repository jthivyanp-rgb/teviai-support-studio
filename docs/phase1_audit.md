# Phase 1 release audit

Checked the TeviAI prototype on 21 November 2026 with Chrome 157, mobile touch emulation, axe-core 4.14.1 and pytest. All test records, names, identifiers and payment examples were fictional. [Public demo](https://teviai-support-studio.streamlit.app/)

The Python regression suite passed 86 tests, including the 18 checks shown in Safety Lab. The same Chrome workflow passed on the local and public apps. Axe-core reported no violations in 13 checked states on each app. The dashboard gradient text and the high-severity warning were also checked manually. Their lowest measured contrast ratios were 5.45:1 and 6.50:1 respectively.

## Findings fixed

- Caption contrast measured 4.42:1 on the deployed baseline. The updated caption colors measure 7.24:1 against the main canvas. Chart values now also appear as text, headings follow the page hierarchy, keyboard navigation has a visible focus outline, and Activity Log offers a plain-text view of each event. [WCAG text contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- The collapsible inbox form could interfere with focusing the message field on the hosted mobile layout. The form is now directly available and a blank message preserves the other fields while showing the error.
- A blocked approval used to hide Reject, Escalate and Return to Draft Studio until the next interaction. All review actions now stay visible when a validation error appears.
- Draft Studio now shows enquiry warnings by the customer message and any additional draft warnings by the editor.
- Closing-time questions now use the configured hours. Unclear questions ask for clarification.
- The risk checks now flag and mask more labelled sensitive values, including card security codes, PINs, sort codes, birth dates and passport numbers. Review blocks the tested refund-completed and booking-confirmation phrasings.

## Checklist

| Area | Check | Evidence |
| --- | --- | --- |
| Website & deployment | Opens in Chrome | Normal Chrome profile loaded the dashboard without a runtime exception. |
| | Opens in Incognito without an account | Fresh off-the-record Chrome profile loaded the app without signing in. |
| | Works on mobile | Touch emulation at 320 and 390 CSS pixels opened the inbox and submitted a 4,000-character enquiry. Page width stayed within the viewport. |
| | Navigation | All five core pages plus Settings and Safety Lab opened. Keyboard activation also worked. |
| | Buttons and links | Workflow controls exercised across the seven pages and app-owned page links resolved. |
| | Branding and typography | TeviAI side navigation remained consistent and all main headings used the same font family. |
| | Text and warnings | Caption contrast corrected. The automated accessibility checks covered empty, populated, high-risk and mobile states. |
| Dashboard | Total | Zero on a fresh session and ten after the sample load. |
| | Pending | One after submission for review and zero after the decision. |
| | Flagged | Eight flagged enquiries in the ten-sample fixture. |
| | Approved and rejected | After the tested decisions, one approved and one rejected. |
| | Empty state | Zero metrics and explanatory empty-state text. |
| Customer Enquiries | New submissions | Fictional product, privacy and instruction-override enquiries classified. |
| | Samples | Ten loaded, with the repeat-load button disabled. |
| | Blank messages | Rejected before a record or event was added. Other fields stayed filled. |
| | Unique IDs | Separate fictional enquiries produced different IDs that matched their activity records. |
| | Categories and flags | Product and refund classification, privacy and instruction-override flags, and low confidence verified. |
| | Long and ambiguous input | A 4,000-character entry reflowed and raised a low-confidence flag. The server test rejected 4,001 characters. |
| Response Drafting | Suggested replies | Generated rule-based delivery, refund and product drafts. |
| | Relevant replies | Checked delivery and price enquiries in Chrome, and closing-time and ambiguity regressions in pytest. |
| | Unverified facts | No price fabricated in the product draft. A missing-policy test directed staff to verify. |
| | Source labels | The browser showed Rule-Based. The controlled provider test showed AI-Assisted on success. |
| | Draft edits | Saved a Draft Studio edit and confirmed it appeared in the approval editor. |
| | AI errors | The controlled provider timeout produced a labelled Rule-Based fallback and warning. The public app showed no enabled AI generation control. |
| Human Approval | Edit before approval | A separate reviewer edit appeared in the approved reply and was copied. |
| | Approve | An eligible delivery reply reached Approved — Not Sent. |
| | Reject | A refund draft was rejected after the unsupported promise remained blocked. |
| | Escalate | Privacy case moved to Escalated with the selected reviewer. |
| | Mandatory review | High-risk approval required an acknowledgement. Acknowledgement could not override the unsafe-content block. |
| | No messages or refunds sent | Code inspection found no customer-message or refund integration. Browser approval changed session status and exposed a copy control. |
| Activity Log | Enquiry processing | Received, classified, drafted and edited events in the export. |
| | Human decisions | Approve, reject and escalate events in the export. |
| | Timestamps and IDs | Every exported test row had a parseable ISO 8601 UTC timestamp and matching ID format. |
| | CSV download | Downloaded both the complete export and the Escalated-only filtered export. |
| | Data minimisation | Export excluded customer names, raw messages, reply edits and the test sensitive values. |
| | Temporary storage | The page explains reload loss and absence of tamper protection. |
| Security & privacy | Fictional test data | Browser runs used built-in samples and explicitly fictional manual enquiries. |
| | API keys | Audited tracked source for common credential signatures and confirmed the public drafting UI had no configured provider. |
| | Sensitive data flags | The browser masked the fictional CVC and passport values. Regression tests also cover PIN, sort code, and birth-date values. |
| | Instruction overrides | The fictional override raised a warning, generated a rule-based reply and triggered no action. |
| | Session isolation | Both new mobile profiles started with empty inboxes while the desktop session held its own enquiries. |
| | External AI during public test | No provider calls or personal data were sent. Provider success and failure were exercised locally with a test double. |

The automated scans cover specific accessibility rules. Screen-reader testing, physical-device testing and a credentialed live Gemini call were outside this audit.

## Repeat the checks

Run pytest from the project root. To repeat the browser audit, use Node.js with Playwright and axe-core installed and Chrome available. Set TEVIAI_AUDIT_URL to the desired app URL. The browser check expects a rule-based deployment without a configured Gemini key.

    node tests/browser_audit.cjs

The browser runner creates disposable Chrome profiles and uses fictional data. Set TEVIAI_AUDIT_REPORT to save detailed scan results, including rules that need manual review.
