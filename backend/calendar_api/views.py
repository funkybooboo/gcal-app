from django.conf import settings
from django.shortcuts import redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import json


# OAuth2 scopes for Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def get_flow():
    """Create and return a Flow instance for OAuth2."""
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
            }
        },
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )


@api_view(['GET'])
def auth_init(request):
    """Initialize the OAuth2 flow and return the authorization URL."""
    try:
        flow = get_flow()
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        # Store state in session for verification
        request.session['oauth_state'] = state

        return Response({
            'auth_url': authorization_url
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def auth_callback(request):
    """Handle the OAuth2 callback from Google."""
    try:
        state = request.session.get('oauth_state')
        flow = get_flow()
        flow.fetch_token(authorization_response=request.build_absolute_uri())

        credentials = flow.credentials

        # Store credentials in session
        request.session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }

        # Redirect to frontend with success
        return redirect(f'http://localhost:5173?auth=success')

    except Exception as e:
        return redirect(f'http://localhost:5173?auth=error&message={str(e)}')


@api_view(['GET'])
def auth_status(request):
    """Check if user is authenticated."""
    credentials_data = request.session.get('credentials')

    if credentials_data:
        return Response({'authenticated': True})
    else:
        return Response({'authenticated': False})


@api_view(['POST'])
def auth_logout(request):
    """Logout user by clearing session."""
    if 'credentials' in request.session:
        del request.session['credentials']

    return Response({'message': 'Logged out successfully'})


@api_view(['GET'])
def list_events(request):
    """List upcoming calendar events."""
    credentials_data = request.session.get('credentials')

    if not credentials_data:
        return Response(
            {'error': 'Not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        credentials = Credentials(**credentials_data)
        service = build('calendar', 'v3', credentials=credentials)

        # Get query parameters
        max_results = int(request.GET.get('max_results', 10))
        time_min = request.GET.get('time_min')

        # Call the Calendar API
        events_params = {
            'calendarId': 'primary',
            'maxResults': max_results,
            'singleEvents': True,
            'orderBy': 'startTime'
        }

        if time_min:
            events_params['timeMin'] = time_min
        else:
            from datetime import datetime
            events_params['timeMin'] = datetime.utcnow().isoformat() + 'Z'

        events_result = service.events().list(**events_params).execute()
        events = events_result.get('items', [])

        return Response({'events': events})

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def list_calendars(request):
    """List all calendars."""
    credentials_data = request.session.get('credentials')

    if not credentials_data:
        return Response(
            {'error': 'Not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        credentials = Credentials(**credentials_data)
        service = build('calendar', 'v3', credentials=credentials)

        # Call the Calendar API
        calendars_result = service.calendarList().list().execute()
        calendars = calendars_result.get('items', [])

        return Response({'calendars': calendars})

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
