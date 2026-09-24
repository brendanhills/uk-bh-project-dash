# Annex B.1: Clinical Data Protection, HIPAA & Health Record Security Controls

## 1. Compliance Baseline
All services and storage buckets deployed under Project Aurora must comply with:
- **HIPAA Security & Privacy Rules** (45 CFR Part 160 and Part 164)
- **Australian My Health Record Privacy Framework & Privacy Act 1988**
- **ISO 27799:2016** (Health informatics & information security management in health)

## 2. Cryptographic Controls & Key Management
- **At-Rest Protection**: All patient health identifiers (PHI) and clinical records stored within database columns or cloud storage objects must utilize AES-256 GCM authenticated encryption with Customer-Managed Encryption Keys (CMEK) held in regional dedicated Cloud HSM partitions.
- **In-Transit Protection**: Clinical REST endpoints enforce TLS 1.3 with mutual authentication (mTLS) for all backend service-to-service calls.
- **Automated Evidence Collection**: Continuous compliance probers verify zero unencrypted data stores daily, automatically streaming audit logs to immutable cold storage.
