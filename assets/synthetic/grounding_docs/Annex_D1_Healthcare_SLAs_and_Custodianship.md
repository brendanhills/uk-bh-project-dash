# Annex D.1: Healthcare Service Level Agreements (SLA) & Data Custodianship Ledger

## 1. Service Level Guarantees (SLA)
- **Emergency Department EHR Ingestion**: 99.999% monthly availability (< 26 seconds allowable downtime/month).
- **Clinical PACS Diagnostic Imaging Retrieval**: Median latency < 450ms for urgent radiological CT/MRI scans.
- **Outpatient FHIR API Availability**: 99.95% monthly uptime.

## 2. Financial Penalty & Service Credit Matrix
Breaches of core clinical availability trigger progressive service credits:
- Monthly availability < 99.99%: 10% monthly service fee rebate.
- Monthly availability < 99.90%: 25% monthly service fee rebate and immediate root-cause presentation to the Joint Clinical Steering Committee.

## 3. Data Custodianship & Sovereignty
The customer retains sole legal and beneficial ownership of all patient clinical records, diagnostic images, and telemetry data. Vendor access is strictly mediated by ephemeral, audited access tokens granted by the Hospital Data Custodian.
