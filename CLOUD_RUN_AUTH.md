# 🔐 Cloud Run Authentication Strategy

## Overview
Implemented hybrid authentication strategy that automatically adapts to the deployment environment:
- **Cloud Run**: Uses Service Account authentication (more secure)
- **Local Development**: Falls back to API Key authentication (simpler)

## Authentication Methods

### 1. Service Account Authentication (Cloud Run)
```bash
# Generate Service Account token
gcloud auth print-access-token

# Use in requests
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     https://your-service.run.app/api/v1/metrics
```

### 2. API Key Authentication (Local Development)
```bash
# Use API Key header
curl -H "X-API-Key: admin-key-change-in-production" \
     http://localhost:8080/api/v1/metrics
```

## Implementation Details

### Auto-Detection Logic
The system automatically detects the environment:
- **Cloud Run**: When `GCP_PROJECT_ID` and `CLOUD_SQL_CONNECTION_NAME` are set
- **Local**: Falls back to API Key authentication

### Security Benefits

#### Service Account (Cloud Run)
- ✅ **Native GCP integration**
- ✅ **Automatic token rotation**
- ✅ **Fine-grained IAM permissions**
- ✅ **Audit logging built-in**
- ✅ **No additional costs**

#### API Key (Local)
- ✅ **Simple for development**
- ✅ **No external dependencies**
- ✅ **Easy to test**

## Next Steps for Full GCP Integration

### 1. Create Service Account
```bash
# Create dedicated service account for admin access
gcloud iam service-accounts create chatbot-admin \
    --display-name="Chatbot Admin Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:chatbot-admin@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"
```

### 2. Deploy with Service Account
```bash
# Update deploy script to use service account
gcloud run deploy chatbot-api \
  --service-account=chatbot-admin@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --no-allow-unauthenticated
```

### 3. Access from Local Machine
```bash
# Authenticate as service account
gcloud auth activate-service-account \
    --key-file=path/to/service-account-key.json

# Get access token
gcloud auth print-access-token
```

## Current Status
- ✅ Hybrid authentication implemented
- ✅ Auto-detection working
- ✅ Fallback to API Key for local development
- 🔄 Service Account token verification (placeholder)
- 🔄 Full JWT validation (TODO)

## Security Comparison

| Method | Security Level | Complexity | Cost | Audit |
|--------|---------------|------------|------|-------|
| **Service Account** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Free | ✅ Built-in |
| **API Key** | ⭐⭐⭐ | ⭐ | Free | ❌ Manual |
| **API Gateway** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $ | ✅ Built-in |

## Recommendation
**Service Account authentication is the most secure and cost-effective solution** for Cloud Run deployments. The current implementation provides a solid foundation that can be enhanced with full JWT validation when needed.
