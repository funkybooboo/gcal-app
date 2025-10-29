# Google Calendar App

A full-stack application using Vue.js, Vite, and Django to interact with the Google Calendar API.

## Project Structure

```
.
├── backend/                 # Django backend
│   ├── gcal_backend/       # Django project settings
│   ├── calendar_api/       # Calendar API app
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile          # Backend Docker configuration
│   └── .env                # Backend environment variables
├── frontend/               # Vue.js frontend
│   ├── src/               # Source files
│   │   ├── App.vue        # Main component
│   │   ├── main.js        # Entry point
│   │   └── style.css      # Styles
│   ├── package.json       # Node dependencies
│   ├── Dockerfile         # Frontend Docker configuration
│   └── .env               # Frontend environment variables
└── docker-compose.yml     # Docker orchestration
```

## Features

- OAuth2 authentication with Google
- View list of calendars
- Display upcoming calendar events
- Dockerized development environment

## Prerequisites

- Docker and Docker Compose
- Google Cloud Console account
- Google Calendar API credentials

## Google Calendar API Setup

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top of the page
3. Click "New Project"
4. Enter a project name (e.g., "Google Calendar App")
5. Click "Create"

### Step 2: Enable Google Calendar API

1. In the Google Cloud Console, make sure your new project is selected
2. Go to "APIs & Services" > "Library" (or visit [API Library](https://console.cloud.google.com/apis/library))
3. Search for "Google Calendar API"
4. Click on "Google Calendar API"
5. Click "Enable"

### Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" > "OAuth consent screen"
2. Select "External" as the User Type (unless you have a Google Workspace)
3. Click "Create"
4. Fill in the required fields:
   - **App name**: Your application name (e.g., "Google Calendar App")
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
5. Click "Save and Continue"
6. On the "Scopes" page, click "Add or Remove Scopes"
7. Search for "Google Calendar API" and select:
   - `https://www.googleapis.com/auth/calendar.readonly`
8. Click "Update" then "Save and Continue"
9. On the "Test users" page, add your Google account email as a test user
10. Click "Save and Continue"
11. Review the summary and click "Back to Dashboard"

### Step 4: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Web application" as the application type
4. Enter a name (e.g., "Calendar Web Client")
5. Under "Authorized JavaScript origins", add:
   - `http://localhost:8000`
6. Under "Authorized redirect URIs", add:
   - `http://localhost:8000/api/auth/callback`
7. Click "Create"
8. A dialog will appear with your **Client ID** and **Client Secret**
9. **IMPORTANT**: Copy these values - you'll need them for the next step

### Step 5: Configure Environment Variables

1. Copy the example environment files:
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```

2. Edit `backend/.env` and add your Google credentials:
   ```env
   DJANGO_SECRET_KEY=your-django-secret-key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

   # Google Calendar API credentials
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/callback
   ```

3. The `frontend/.env` should already have the correct default:
   ```env
   VITE_API_BASE_URL=http://localhost:8000/api
   ```

## Running the Application

### Using Docker Compose (Recommended)

1. Make sure Docker and Docker Compose are installed and running

2. Start the application:
   ```bash
   docker-compose up --build
   ```

3. The application will be available at:
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000

4. To stop the application:
   ```bash
   docker-compose down
   ```

### Running Locally (Without Docker)

#### Backend Setup

1. Create a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run migrations:
   ```bash
   python manage.py migrate
   ```

4. Start the development server:
   ```bash
   python manage.py runserver
   ```

#### Frontend Setup

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

## Usage

1. Open your browser and navigate to http://localhost:5173
2. Click "Login with Google"
3. You'll be redirected to Google's OAuth consent screen
4. Select your Google account and grant permissions
5. After successful authentication, you'll be redirected back to the app
6. Click "Load Calendars" to see your calendars
7. Click "Load Events" to see your upcoming calendar events

## API Endpoints

### Authentication

- `GET /api/auth/init` - Initialize OAuth flow
- `GET /api/auth/callback` - OAuth callback handler
- `GET /api/auth/status` - Check authentication status
- `POST /api/auth/logout` - Logout user

### Calendar

- `GET /api/calendars` - List all calendars
- `GET /api/events?max_results=10` - List upcoming events

## Troubleshooting

### "Access blocked: Authorization Error"

If you see this error during login:
1. Make sure you've added your email as a test user in the OAuth consent screen
2. Verify that the OAuth consent screen is properly configured
3. Check that the redirect URI matches exactly: `http://localhost:8000/api/auth/callback`

### "Error 400: redirect_uri_mismatch"

This means the redirect URI in your request doesn't match the one configured in Google Cloud Console:
1. Go to Google Cloud Console > APIs & Services > Credentials
2. Click on your OAuth 2.0 Client ID
3. Make sure `http://localhost:8000/api/auth/callback` is listed under "Authorized redirect URIs"

### CORS Errors

If you see CORS errors in the browser console:
1. Make sure both frontend and backend are running
2. Verify the `VITE_API_BASE_URL` in frontend/.env matches your backend URL
3. Check that django-cors-headers is properly configured in the backend

### No events showing up

1. Make sure you have events in your Google Calendar
2. Check that you've granted the calendar.readonly permission
3. Try logging out and logging in again

## Development

### Backend

The Django backend uses:
- Django REST Framework for API endpoints
- Google Auth libraries for OAuth2 flow
- Session-based authentication to store credentials

### Frontend

The Vue frontend uses:
- Vue 3 Composition API
- Axios for HTTP requests
- Vite for fast development and building

## Security Notes

- Never commit the `.env` files to version control
- In production, use HTTPS instead of HTTP
- Generate a strong `DJANGO_SECRET_KEY` for production
- Set `DEBUG=False` in production
- Configure proper CORS settings for production domains

## License

MIT License
