# Google Calendar App - Authentication and Calendar Workflow Documentation

## Overview

This application integrates Google Calendar using Google OAuth2 for authentication. There is **no Auth0 integration** in this application - authentication is handled entirely through Google's OAuth2 flow.

## Technology Stack

- **Frontend**: Vue.js (running on port 5173)
- **Backend**: Django (running on port 8000)
- **Authentication**: Google OAuth2
- **API**: Google Calendar API v3
- **Token Storage**: Django Sessions

---

## Google OAuth2 Authentication Workflow

### Configuration

OAuth2 credentials are configured in `backend/gcal_backend/settings.py`:

```python
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/api/auth/callback')
```

These values should be set in a `.env` file in the backend directory.

### OAuth2 Flow Steps

#### 1. User Initiates Login (Frontend)

**File**: `frontend/src/App.vue:95-108`

When the user clicks "Login with Google":

```javascript
async login() {
  const response = await axios.get(`${API_BASE_URL}/auth/init`, {
    withCredentials: true
  })
  window.location.href = response.data.auth_url
}
```

**Endpoint Called**: `GET http://localhost:8000/api/auth/init`

---

#### 2. Backend Generates Authorization URL

**File**: `backend/calendar_api/views.py:36-61`

**Endpoint**: `/api/auth/init`

The backend:
1. Creates a Google OAuth2 Flow instance with client credentials
2. Generates an authorization URL with required scopes
3. Stores the OAuth state in the Django session for CSRF protection
4. Returns the authorization URL to the frontend

```python
flow = get_flow()
authorization_url, state = flow.authorization_url(
    access_type='offline',
    include_granted_scopes='true',
    prompt='consent'
)
request.session['oauth_state'] = state
```

**OAuth Scopes Required**:
- `https://www.googleapis.com/auth/calendar.readonly`

**Response**:
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?..."
}
```

---

#### 3. User Redirects to Google

The frontend redirects the user to Google's OAuth consent screen using `window.location.href`.

Google handles:
- User authentication
- Consent for calendar access
- Generation of authorization code

---

#### 4. Google Redirects Back to Callback

**Redirect URL**: `http://localhost:8000/api/auth/callback?code=...&state=...`

Google redirects the user back to the backend with:
- `code`: Authorization code to exchange for tokens
- `state`: CSRF protection token (matches what was stored in session)

---

#### 5. Backend Handles Callback and Exchanges Code for Tokens

**File**: `backend/calendar_api/views.py:64-96`

**Endpoint**: `/api/auth/callback`

The backend:
1. Retrieves the OAuth state from the session
2. Creates a new Flow instance
3. Exchanges the authorization code for access and refresh tokens
4. Stores credentials in the Django session
5. Redirects to frontend with success/error status

```python
flow = get_flow()
flow.fetch_token(authorization_response=request.build_absolute_uri())
credentials = flow.credentials

request.session['credentials'] = {
    'token': credentials.token,
    'refresh_token': credentials.refresh_token,
    'token_uri': credentials.token_uri,
    'client_id': credentials.client_id,
    'client_secret': credentials.client_secret,
    'scopes': credentials.scopes
}
```

**Token Storage Location**: Django session (server-side)

**Success Redirect**: `http://localhost:5173?auth=success`
**Error Redirect**: `http://localhost:5173?auth=error&message=...`

---

#### 6. Frontend Handles Callback Response

**File**: `frontend/src/App.vue:169-185`

The frontend:
1. Checks URL parameters for `auth=success` or `auth=error`
2. Updates the `authenticated` state accordingly
3. Cleans up the URL by removing query parameters

```javascript
handleAuthCallback() {
  const urlParams = new URLSearchParams(window.location.search)
  const authStatus = urlParams.get('auth')

  if (authStatus === 'success') {
    this.authenticated = true
    window.history.replaceState({}, document.title, '/')
  }
}
```

---

## Token Storage

### Where Tokens Are Stored

**Storage Mechanism**: Django Sessions (server-side)

**Session Configuration** (`backend/gcal_backend/settings.py:104-106`):
```python
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
```

**Database Location**: `backend/data/db.sqlite3`
- Django uses SQLite for session storage by default
- Session data includes the credentials dictionary

### Token Structure

The credentials stored in the session include:
- `token`: Access token for API requests (short-lived)
- `refresh_token`: Token to obtain new access tokens (long-lived)
- `token_uri`: Google's token endpoint
- `client_id`: OAuth client ID
- `client_secret`: OAuth client secret
- `scopes`: List of granted permissions

---

## Google Calendar API Workflow

### Authentication Check

**File**: `frontend/src/App.vue:81-94`

**Endpoint**: `GET http://localhost:8000/api/auth/status`

On app mount, the frontend checks authentication status:

```javascript
async checkAuthStatus() {
  const response = await axios.get(`${API_BASE_URL}/auth/status`, {
    withCredentials: true
  })
  this.authenticated = response.data.authenticated
}
```

**Backend Handler** (`backend/calendar_api/views.py:98-109`):
```python
credentials_data = request.session.get('credentials')
if credentials_data:
    return Response({'authenticated': True})
else:
    return Response({'authenticated': False})
```

---

### Fetching Calendar Events

**File**: `frontend/src/App.vue:126-147`

**Endpoint**: `GET http://localhost:8000/api/events?max_results=20`

When the user clicks "Load Events":

```javascript
async fetchEvents() {
  const response = await axios.get(`${API_BASE_URL}/events`, {
    params: { max_results: 20 },
    withCredentials: true
  })
  this.events = response.data.events
}
```

**Backend Handler** (`backend/calendar_api/views.py:125-174`):

1. **Authentication Check**: Verifies credentials exist in session
2. **Build Google API Client**: Creates Calendar API service
3. **Fetch Events**: Calls Google Calendar API
4. **Return Events**: Sends events back to frontend

```python
credentials = Credentials(**credentials_data)
service = build('calendar', 'v3', credentials=credentials)

events_result = service.events().list(
    calendarId='primary',
    maxResults=max_results,
    singleEvents=True,
    orderBy='startTime',
    timeMin=datetime.utcnow().isoformat() + 'Z'
).execute()
```

**Google API Endpoint Called**: `https://www.googleapis.com/calendar/v3/calendars/primary/events`

**Query Parameters**:
- `calendarId`: 'primary' (user's main calendar)
- `maxResults`: Number of events to return (default: 10)
- `singleEvents`: True (expand recurring events)
- `orderBy`: 'startTime' (sort by start time)
- `timeMin`: Current UTC time (only future events)

---

### Fetching Calendar List

**File**: `frontend/src/App.vue:148-168`

**Endpoint**: `GET http://localhost:8000/api/calendars`

When the user clicks "Load Calendars":

```javascript
async fetchCalendars() {
  const response = await axios.get(`${API_BASE_URL}/calendars`, {
    withCredentials: true
  })
  this.calendars = response.data.calendars
}
```

**Backend Handler** (`backend/calendar_api/views.py:177-208`):

```python
credentials = Credentials(**credentials_data)
service = build('calendar', 'v3', credentials=credentials)

calendars_result = service.calendarList().list().execute()
calendars = calendars_result.get('items', [])
```

**Google API Endpoint Called**: `https://www.googleapis.com/calendar/v3/users/me/calendarList`

---

### Logout

**File**: `frontend/src/App.vue:110-125`

**Endpoint**: `POST http://localhost:8000/api/auth/logout`

When the user clicks "Logout":

```javascript
async logout() {
  await axios.post(`${API_BASE_URL}/auth/logout`, {}, {
    withCredentials: true
  })
  this.authenticated = false
  this.events = []
  this.calendars = []
}
```

**Backend Handler** (`backend/calendar_api/views.py:112-122`):
```python
if 'credentials' in request.session:
    del request.session['credentials']
return Response({'message': 'Logged out successfully'})
```

This clears the stored credentials from the Django session.

---

## API Endpoints Summary

| Endpoint | Method | Purpose | File Reference |
|----------|--------|---------|----------------|
| `/api/auth/init` | GET | Start OAuth2 flow, get authorization URL | `views.py:36-61` |
| `/api/auth/callback` | GET | Handle OAuth2 callback, exchange code for tokens | `views.py:64-96` |
| `/api/auth/status` | GET | Check if user is authenticated | `views.py:98-109` |
| `/api/auth/logout` | POST | Clear session credentials | `views.py:112-122` |
| `/api/events` | GET | Fetch calendar events from Google | `views.py:125-174` |
| `/api/calendars` | GET | Fetch list of user's calendars | `views.py:177-208` |

All endpoints are defined in `backend/calendar_api/urls.py:4-11`

---

## Security Considerations

### Session Security

1. **CORS Configuration** (`settings.py:91-97`):
   - Only specific origins allowed (localhost:5173, 127.0.0.1:5173)
   - Credentials allowed via `CORS_ALLOW_CREDENTIALS = True`

2. **Session Cookies**:
   - `SESSION_COOKIE_SAMESITE = 'Lax'` prevents CSRF attacks
   - `withCredentials: true` required on all frontend requests
   - Session cookies are httpOnly by default (not accessible via JavaScript)

3. **OAuth State Parameter**:
   - State token stored in session prevents CSRF attacks
   - Validated during callback (implicitly by the Flow library)

### Token Security

1. **Server-Side Storage**: Tokens stored in Django sessions, never exposed to frontend
2. **Refresh Tokens**: Long-lived tokens stored for obtaining new access tokens
3. **Access Type Offline**: Allows backend to refresh tokens without user interaction

---

## Data Flow Diagram

```
┌─────────────┐                    ┌─────────────┐                    ┌─────────────┐
│             │                    │             │                    │             │
│  Vue.js     │                    │   Django    │                    │   Google    │
│  Frontend   │                    │   Backend   │                    │   OAuth2    │
│             │                    │             │                    │             │
└──────┬──────┘                    └──────┬──────┘                    └──────┬──────┘
       │                                  │                                  │
       │ 1. GET /api/auth/init            │                                  │
       │─────────────────────────────────>│                                  │
       │                                  │                                  │
       │ 2. {auth_url}                    │                                  │
       │<─────────────────────────────────│                                  │
       │                                  │                                  │
       │ 3. Redirect to auth_url          │                                  │
       │──────────────────────────────────────────────────────────────────>│
       │                                  │                                  │
       │                                  │ 4. Redirect with code & state    │
       │                                  │<─────────────────────────────────│
       │                                  │                                  │
       │                                  │ 5. Exchange code for tokens      │
       │                                  │─────────────────────────────────>│
       │                                  │                                  │
       │                                  │ 6. Access & Refresh tokens       │
       │                                  │<─────────────────────────────────│
       │                                  │                                  │
       │                                  │ [Tokens stored in session]       │
       │                                  │                                  │
       │ 7. Redirect to frontend          │                                  │
       │<─────────────────────────────────│                                  │
       │                                  │                                  │
       │ 8. GET /api/events               │                                  │
       │─────────────────────────────────>│                                  │
       │                                  │                                  │
       │                                  │ 9. GET calendar/v3/events        │
       │                                  │─────────────────────────────────>│
       │                                  │                                  │
       │                                  │ 10. Events data                  │
       │                                  │<─────────────────────────────────│
       │                                  │                                  │
       │ 11. {events: [...]}              │                                  │
       │<─────────────────────────────────│                                  │
       │                                  │                                  │
```

---

## Environment Variables

Create a `.env` file in the `backend` directory with:

```env
# Django Settings
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Google OAuth2 Credentials
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/callback

# Logging
DJANGO_LOG_LEVEL=INFO
APP_LOG_LEVEL=DEBUG
```

To obtain Google OAuth2 credentials:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:8000/api/auth/callback`

---

## Common Issues and Troubleshooting

### Authentication Fails

1. **Check credentials**: Ensure `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set correctly
2. **Check redirect URI**: Must match exactly in Google Cloud Console and `.env` file
3. **Check CORS**: Frontend must be running on allowed origin (localhost:5173)

### Tokens Not Persisting

1. **Check cookies**: Ensure `withCredentials: true` is set on all axios requests
2. **Check session middleware**: Ensure Django session middleware is enabled
3. **Check database**: Ensure `backend/data/db.sqlite3` exists and is writable

### API Requests Fail

1. **Check authentication**: Call `/api/auth/status` to verify session exists
2. **Check token expiry**: Access tokens expire; backend should handle refresh automatically
3. **Check scopes**: Ensure correct Calendar API scopes are requested

---

## File Reference Guide

### Backend Files

- `backend/gcal_backend/settings.py`: Django configuration, OAuth2 settings
- `backend/calendar_api/views.py`: All API endpoint handlers
- `backend/calendar_api/urls.py`: API route definitions
- `backend/gcal_backend/urls.py`: Main URL configuration
- `backend/calendar_api/models.py`: Database models (currently empty)
- `backend/data/db.sqlite3`: SQLite database (sessions and auth data)

### Frontend Files

- `frontend/src/App.vue`: Main Vue component with all authentication and API logic
- Lines 95-108: Login flow
- Lines 81-94: Auth status check
- Lines 126-147: Fetch events
- Lines 148-168: Fetch calendars
- Lines 110-125: Logout
- Lines 169-185: Handle OAuth callback
