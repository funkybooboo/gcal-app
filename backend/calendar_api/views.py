from django.conf import settings
from django.shortcuts import redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import json
import logging

logger = logging.getLogger('calendar_api')


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
    logger.info("Initializing OAuth2 flow")
    try:
        flow = get_flow()
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        # Store state in session for verification
        request.session['oauth_state'] = state
        logger.debug(f"OAuth state stored in session: {state}")

        logger.info("OAuth2 flow initialized successfully")
        return Response({
            'auth_url': authorization_url
        })
    except Exception as e:
        logger.error(f"Error initializing OAuth2 flow: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def auth_callback(request):
    """Handle the OAuth2 callback from Google."""
    logger.info("Handling OAuth2 callback from Google")
    try:
        state = request.session.get('oauth_state')
        logger.debug(f"Retrieved OAuth state from session: {state}")

        flow = get_flow()
        flow.fetch_token(authorization_response=request.build_absolute_uri())

        credentials = flow.credentials
        logger.info("Successfully fetched OAuth2 credentials")

        # Store credentials in session
        request.session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        logger.debug("Credentials stored in session")

        # Redirect to frontend with success
        logger.info("Redirecting to frontend with success")
        return redirect(f'http://localhost:5173?auth=success')

    except Exception as e:
        logger.error(f"Error in OAuth2 callback: {str(e)}", exc_info=True)
        return redirect(f'http://localhost:5173?auth=error&message={str(e)}')


@api_view(['GET'])
def auth_status(request):
    """Check if user is authenticated."""
    logger.debug("Checking authentication status")
    credentials_data = request.session.get('credentials')

    if credentials_data:
        logger.info("User is authenticated")
        return Response({'authenticated': True})
    else:
        logger.info("User is not authenticated")
        return Response({'authenticated': False})


@api_view(['POST'])
def auth_logout(request):
    """Logout user by clearing session."""
    logger.info("User logout requested")
    if 'credentials' in request.session:
        del request.session['credentials']
        logger.info("User credentials cleared from session")
    else:
        logger.debug("No credentials found in session during logout")

    return Response({'message': 'Logged out successfully'})


@api_view(['GET'])
def list_events(request):
    """List upcoming calendar events."""
    logger.info("Listing calendar events")
    credentials_data = request.session.get('credentials')

    if not credentials_data:
        logger.warning("Unauthenticated request to list events")
        return Response(
            {'error': 'Not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        credentials = Credentials(**credentials_data)
        service = build('calendar', 'v3', credentials=credentials)
        logger.debug("Calendar service built successfully")

        # Get query parameters
        max_results = int(request.GET.get('max_results', 250))
        time_min = request.GET.get('time_min')
        time_max = request.GET.get('time_max')
        calendar_id = request.GET.get('calendar_id', 'primary')
        logger.debug(f"Query parameters - max_results: {max_results}, time_min: {time_min}, time_max: {time_max}")

        # Call the Calendar API
        events_params = {
            'calendarId': calendar_id,
            'maxResults': max_results,
            'singleEvents': True,
            'orderBy': 'startTime'
        }

        if time_min:
            events_params['timeMin'] = time_min
        else:
            from datetime import datetime
            events_params['timeMin'] = datetime.utcnow().isoformat() + 'Z'

        if time_max:
            events_params['timeMax'] = time_max

        logger.debug(f"Fetching events with parameters: {events_params}")
        events_result = service.events().list(**events_params).execute()
        events = events_result.get('items', [])

        # Add calendarId to each event for color coding
        for event in events:
            event['calendarId'] = calendar_id

        logger.info(f"Successfully retrieved {len(events)} events")
        return Response({'events': events})

    except Exception as e:
        logger.error(f"Error listing events: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def list_calendars(request):
    """List all calendars."""
    logger.info("Listing calendars")
    credentials_data = request.session.get('credentials')

    if not credentials_data:
        logger.warning("Unauthenticated request to list calendars")
        return Response(
            {'error': 'Not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        credentials = Credentials(**credentials_data)
        service = build('calendar', 'v3', credentials=credentials)
        logger.debug("Calendar service built successfully")

        # Call the Calendar API
        logger.debug("Fetching calendar list from Google Calendar API")
        calendars_result = service.calendarList().list().execute()
        calendars = calendars_result.get('items', [])

        logger.info(f"Successfully retrieved {len(calendars)} calendars")
        return Response({'calendars': calendars})

    except Exception as e:
        logger.error(f"Error listing calendars: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
