# 🔒 API Key Authentication Implementation

## Overview
Implemented API Key authentication for administrative endpoints to protect sensitive analytics data.

## Changes Made

### 1. Configuration (`app/core/config.py`)
- Added `ADMIN_API_KEY` field with default value
- Imported `Field` from pydantic for proper field definition

### 2. Authentication Module (`app/core/auth.py`)
- Created `verify_admin_api_key()` function for X-API-Key header validation
- Added `verify_admin_bearer_token()` as alternative Bearer token method
- Proper error handling with 401 responses and WWW-Authenticate headers
- Logging for security monitoring

### 3. Protected Endpoints

#### Chat Endpoints (`app/api/v1/endpoints/chat.py`)
- `GET /conversations` - All conversation pairs (ADMIN ONLY)
- `GET /conversations/{session_id}` - Session-specific conversations (ADMIN ONLY)  
- `GET /top-questions` - Most frequent questions analysis (ADMIN ONLY)

#### Analytics Endpoints (`app/api/v1/endpoints/analytics.py`)
- `GET /metrics` - Overall system metrics (ADMIN ONLY)
- `GET /metrics/daily` - Daily metrics aggregation (ADMIN ONLY)
- `GET /gdpr/data/{session_id}` - User data access (ADMIN ONLY)

## Usage

### API Key Authentication
```bash
# Using X-API-Key header
curl -H "X-API-Key: admin-key-change-in-production" \
     http://localhost:8080/api/v1/conversations

# Using Authorization Bearer (alternative)
curl -H "Authorization: Bearer admin-key-change-in-production" \
     http://localhost:8080/api/v1/conversations
```

### Environment Variable
Set `ADMIN_API_KEY` in your environment:
```bash
export ADMIN_API_KEY="your-secure-admin-key-here"
```

## Security Features

1. **Rate Limiting**: Maintained existing rate limits on protected endpoints
2. **Error Handling**: Proper 401 responses with WWW-Authenticate headers
3. **Logging**: Security events logged for monitoring
4. **Flexible Auth**: Supports both X-API-Key and Bearer token methods

## Unprotected Endpoints
These remain public (rate-limited only):
- `POST /capture-data` - Data capture (user-facing)
- `POST /gdpr/consent` - GDPR consent (user-facing)
- `DELETE /gdpr/data/{session_id}` - Data deletion (user-facing)
- `POST /chat` - Main chat endpoint (user-facing)

## Next Steps
1. Change default API key in production
2. Consider implementing JWT tokens for more robust auth
3. Add API key rotation mechanism
4. Implement audit logging for admin access
