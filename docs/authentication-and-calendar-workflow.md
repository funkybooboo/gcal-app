# Google Calendar App - Authentication and Calendar Workflow Documentation

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Quick Workflow Summary](#quick-workflow-summary)
4. [Technology Stack](#technology-stack)
5. [Google OAuth2 Authentication Workflow](#google-oauth2-authentication-workflow)
   - [Configuration](#configuration)
   - [OAuth2 Flow Steps](#oauth2-flow-steps)
6. [Token Storage](#token-storage)
7. [Google Calendar API Workflow](#google-calendar-api-workflow)
   - [Authentication Check](#authentication-check)
   - [Fetching Calendar Events](#fetching-calendar-events)
   - [Fetching Calendar List](#fetching-calendar-list)
8. [Calendar View Workflow](#calendar-view-workflow)
   - [CalendarView Component](#calendarview-component)
   - [Month Navigation Workflow](#month-navigation-workflow)
   - [Event Display and Formatting](#event-display-and-formatting)
   - [Calendar Grid Generation](#calendar-grid-generation)
   - [User Interaction Features](#user-interaction-features)
9. [API Endpoints Summary](#api-endpoints-summary)
10. [Security Considerations](#security-considerations)
11. [Data Flow Diagrams](#data-flow-diagram)
12. [Environment Variables](#environment-variables)
13. [Common Issues and Troubleshooting](#common-issues-and-troubleshooting)
14. [File Reference Guide](#file-reference-guide)

---

## Overview

This application integrates Google Calendar using Google OAuth2 for authentication. There is **no Auth0 integration** in this application - authentication is handled entirely through Google's OAuth2 flow.

The application provides a clean, interactive calendar view that displays events from your Google Calendar in a familiar month-grid format, similar to Google Calendar's web interface.

## Features

- **Google OAuth2 Authentication**: Secure login with Google account
- **Interactive Calendar View**: Month-grid calendar displaying all your events
- **Month Navigation**: Browse through different months with previous/next controls
- **Event Display**:
  - Events shown on their respective days
  - Time formatting in 12-hour AM/PM format
  - All-day events clearly marked
  - Color-coded events by calendar
  - Event details on hover
- **Real-time Updates**: Events fetched automatically when navigating months
- **Responsive Design**: Works on desktop and mobile devices
- **Today Highlighting**: Current date highlighted for easy reference

## Quick Workflow Summary

1. **User logs in** → Redirected to Google OAuth consent screen
2. **User grants permissions** → Google redirects back with authorization code
3. **Backend exchanges code for tokens** → Tokens stored in Django session
4. **Frontend loads calendar** → Automatically fetches events for current month
5. **User navigates months** → Events fetched for each month on demand
6. **Events displayed in grid** → Color-coded, formatted, and organized by day

## Technology Stack

- **Frontend**: Vue.js 3 with Composition API (running on port 5173)
  - Components: App.vue (main app), CalendarView.vue (calendar UI)
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

**File**: `frontend/src/App.vue:112-148`

**Endpoint**: `GET http://localhost:8000/api/events`

The application automatically fetches events for the current month when authenticated, and refetches when the user navigates to different months:

```javascript
async fetchEventsForMonth(month, year) {
  this.loadingEvents = true
  this.eventsError = null

  // Get first and last day of the month
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0, 23, 59, 59)

  // Format as ISO strings
  const timeMin = firstDay.toISOString()
  const timeMax = lastDay.toISOString()

  const response = await axios.get(`${API_BASE_URL}/events`, {
    params: {
      time_min: timeMin,
      time_max: timeMax,
      max_results: 250
    },
    withCredentials: true
  })

  this.events = response.data.events
}
```

**Backend Handler** (`backend/calendar_api/views.py:125-183`):

1. **Authentication Check**: Verifies credentials exist in session
2. **Build Google API Client**: Creates Calendar API service
3. **Fetch Events**: Calls Google Calendar API with date range
4. **Add Calendar Metadata**: Adds calendarId to each event for color coding
5. **Return Events**: Sends events back to frontend

```python
credentials = Credentials(**credentials_data)
service = build('calendar', 'v3', credentials=credentials)

# Get query parameters
max_results = int(request.GET.get('max_results', 250))
time_min = request.GET.get('time_min')
time_max = request.GET.get('time_max')
calendar_id = request.GET.get('calendar_id', 'primary')

events_params = {
    'calendarId': calendar_id,
    'maxResults': max_results,
    'singleEvents': True,
    'orderBy': 'startTime'
}

if time_min:
    events_params['timeMin'] = time_min
else:
    events_params['timeMin'] = datetime.utcnow().isoformat() + 'Z'

if time_max:
    events_params['timeMax'] = time_max

events_result = service.events().list(**events_params).execute()
events = events_result.get('items', [])

# Add calendarId to each event for color coding
for event in events:
    event['calendarId'] = calendar_id
```

**Google API Endpoint Called**: `https://www.googleapis.com/calendar/v3/calendars/primary/events`

**Query Parameters**:
- `calendar_id`: Calendar ID to fetch events from (default: 'primary')
- `max_results`: Maximum number of events to return (default: 250)
- `time_min`: Start of date range (ISO 8601 format)
- `time_max`: End of date range (ISO 8601 format)
- `singleEvents`: True (expand recurring events)
- `orderBy`: 'startTime' (sort by start time)

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

## Calendar View Workflow

The application features a fully integrated calendar UI component that displays events in a month grid view.

### CalendarView Component

**File**: `frontend/src/components/CalendarView.vue`

The CalendarView component:
- Displays a month grid calendar (7 columns x 6 rows)
- Shows events from the current and adjacent months
- Highlights today's date
- Supports month-to-month navigation
- Color-codes events based on calendar ID
- Formats event times (12-hour format with AM/PM)
- Handles all-day events

### Month Navigation Workflow

**Files**:
- `frontend/src/components/CalendarView.vue:124-141` (navigation methods)
- `frontend/src/App.vue:149-154` (event handler)

When the user clicks the previous/next month buttons:

1. **CalendarView emits month-changed event**:
```javascript
// In CalendarView.vue
nextMonth() {
  if (this.currentMonth === 11) {
    this.currentMonth = 0
    this.currentYear++
  } else {
    this.currentMonth++
  }
  this.$emit('month-changed', { month: this.currentMonth, year: this.currentYear })
}
```

2. **App.vue handles the event**:
```javascript
// In App.vue
onMonthChanged({ month, year }) {
  this.currentMonth = month
  this.currentYear = year
  this.fetchEventsForMonth(month, year)
}
```

3. **Events are fetched for the new month** using the date range for that month
4. **CalendarView re-renders** with the new events

### Event Display and Formatting

**File**: `frontend/src/components/CalendarView.vue:142-186`

#### Event Filtering by Day

Events are filtered and displayed for each day in the calendar:

```javascript
getEventsForDay(dayDate) {
  return this.events.filter(event => {
    const eventDate = new Date(event.start.dateTime || event.start.date)
    eventDate.setHours(0, 0, 0, 0)
    const compareDate = new Date(dayDate)
    compareDate.setHours(0, 0, 0, 0)

    return eventDate.getTime() === compareDate.getTime()
  })
}
```

#### Time Formatting

Events display in 12-hour format with AM/PM:

```javascript
formatEventTime(event) {
  if (event.start.date) {
    return 'All day'
  }

  const startTime = new Date(event.start.dateTime)
  const hours = startTime.getHours()
  const minutes = startTime.getMinutes()
  const ampm = hours >= 12 ? 'PM' : 'AM'
  const displayHours = hours % 12 || 12
  const displayMinutes = minutes.toString().padStart(2, '0')

  return `${displayHours}:${displayMinutes} ${ampm}`
}
```

**Examples**:
- `2:30 PM` for 14:30
- `9:00 AM` for 09:00
- `All day` for full-day events

#### Event Color Coding

Events are color-coded based on their calendar ID using a consistent hashing algorithm:

```javascript
getEventColor(event) {
  if (event.calendarId) {
    const hash = event.calendarId.split('').reduce((acc, char) => {
      return char.charCodeAt(0) + ((acc << 5) - acc)
    }, 0)
    const colors = ['#4285f4', '#ea4335', '#fbbc04', '#34a853', '#ff6d00', '#46bdc6', '#7baaf7', '#f07b72']
    return colors[Math.abs(hash) % colors.length]
  }
  return '#4285f4'
}
```

This ensures:
- Events from the same calendar always have the same color
- Different calendars get visually distinct colors
- Colors are Google Calendar-inspired palette

### Calendar Grid Generation

**File**: `frontend/src/components/CalendarView.vue:65-121`

The calendar grid is computed to show:
1. **Previous month overflow days** (to fill the first week)
2. **Current month days** (1st through last day of month)
3. **Next month overflow days** (to complete 6 rows of 7 days)

For each day, the component:
- Determines if it's today (highlighted in blue)
- Determines if it's in the current month (grayed out if not)
- Fetches and displays all events for that day

### User Interaction Features

1. **Month Navigation**: Previous/next buttons to navigate months
2. **Event Hover**: Shows full event details on hover (title and time)
3. **Today Highlight**: Current date highlighted with blue circle
4. **Responsive Design**: Adapts to mobile screens (768px breakpoint)

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

### Calendar View Interaction Flow

```
┌─────────────┐                    ┌─────────────┐                    ┌─────────────┐
│             │                    │             │                    │             │
│  Calendar   │                    │   App.vue   │                    │   Django    │
│  View       │                    │  Component  │                    │   Backend   │
│             │                    │             │                    │             │
└──────┬──────┘                    └──────┬──────┘                    └──────┬──────┘
       │                                  │                                  │
       │                                  │ [User authenticates]             │
       │                                  │                                  │
       │                                  │ 1. Auto-fetch current month      │
       │                                  │    fetchEventsForMonth()         │
       │                                  │─────────────────────────────────>│
       │                                  │                                  │
       │                                  │ 2. Events for month              │
       │                                  │<─────────────────────────────────│
       │                                  │                                  │
       │ 3. Render calendar               │                                  │
       │  with events prop                │                                  │
       │<─────────────────────────────────│                                  │
       │                                  │                                  │
       │ 4. User clicks next/prev month   │                                  │
       │  emit('month-changed')           │                                  │
       │─────────────────────────────────>│                                  │
       │                                  │                                  │
       │                                  │ 5. Fetch new month events        │
       │                                  │─────────────────────────────────>│
       │                                  │                                  │
       │                                  │ 6. Events for new month          │
       │                                  │<─────────────────────────────────│
       │                                  │                                  │
       │ 7. Re-render with new events     │                                  │
       │<─────────────────────────────────│                                  │
       │                                  │                                  │
       │ 8. Display events in grid        │                                  │
       │    - Filter by day               │                                  │
       │    - Format times                │                                  │
       │    - Color code by calendar      │                                  │
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

### Events Not Showing in Calendar

1. **Check date range**: Events are fetched for specific month ranges; verify `time_min` and `time_max` parameters
2. **Check event filtering**: Ensure events have valid `start.dateTime` or `start.date` fields
3. **Check browser console**: Look for JavaScript errors in event filtering or display logic
4. **Check max_results**: Default is 250; if you have more events in a month, increase this value

### Calendar Not Updating When Changing Months

1. **Check month-changed event**: Verify CalendarView is emitting the event
2. **Check App.vue handler**: Ensure `onMonthChanged` is being called
3. **Check network requests**: Verify API call is made with correct date range
4. **Check browser console**: Look for errors in the fetchEventsForMonth function

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

- `frontend/src/App.vue`: Main Vue component with authentication and API orchestration
  - Lines 81-95: Login flow
  - Lines 67-80: Auth status check
  - Lines 96-111: Logout
  - Lines 112-148: Fetch events for month (with date range)
  - Lines 149-154: Handle month navigation
  - Lines 155-171: Handle OAuth callback
  - Lines 59-65: Auto-fetch events when authenticated

- `frontend/src/components/CalendarView.vue`: Calendar UI component
  - Lines 65-121: Calendar grid generation (computed property)
  - Lines 124-132: Previous month navigation
  - Lines 133-141: Next month navigation
  - Lines 142-161: Filter events by day
  - Lines 162-175: Format event times (12-hour AM/PM)
  - Lines 176-186: Generate event colors from calendar ID

- `frontend/src/main.js`: Vue app entry point
