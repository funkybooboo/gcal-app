<template>
  <div>
    <h1>Google Calendar App</h1>

    <div v-if="!authenticated" class="card">
      <h2>Login to Google Calendar</h2>
      <p>Click the button below to authenticate with your Google account.</p>
      <button @click="login">Login with Google</button>
    </div>

    <div v-else>
      <div class="card">
        <h2>Welcome!</h2>
        <button @click="logout">Logout</button>
      </div>

      <div class="card">
        <h2>Your Calendars</h2>
        <button @click="fetchCalendars">Load Calendars</button>

        <div v-if="loadingCalendars" class="loading">Loading calendars...</div>

        <div v-if="calendarsError" class="error">{{ calendarsError }}</div>

        <div v-if="calendars.length > 0">
          <div v-for="calendar in calendars" :key="calendar.id" class="calendar-item">
            <div class="calendar-name">{{ calendar.summary }}</div>
            <div class="event-time">{{ calendar.id }}</div>
          </div>
        </div>
      </div>

      <div class="card">
        <h2>Upcoming Events</h2>
        <button @click="fetchEvents">Load Events</button>

        <div v-if="loadingEvents" class="loading">Loading events...</div>

        <div v-if="eventsError" class="error">{{ eventsError }}</div>

        <div v-if="events.length > 0">
          <div v-for="event in events" :key="event.id" class="event-card">
            <div class="event-title">{{ event.summary || 'No Title' }}</div>
            <div class="event-time">
              {{ formatEventTime(event) }}
            </div>
          </div>
        </div>
        <div v-else-if="!loadingEvents && events.length === 0">
          <p>No upcoming events found.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

export default {
  name: 'App',
  data() {
    return {
      authenticated: false,
      events: [],
      calendars: [],
      loadingEvents: false,
      loadingCalendars: false,
      eventsError: null,
      calendarsError: null
    }
  },
  mounted() {
    this.checkAuthStatus()
    this.handleAuthCallback()
  },
  methods: {
    async checkAuthStatus() {
      try {
        const response = await axios.get(`${API_BASE_URL}/auth/status`, {
          withCredentials: true
        })
        this.authenticated = response.data.authenticated
      } catch (error) {
        console.error('Error checking auth status:', error)
      }
    },
    async login() {
      try {
        const response = await axios.get(`${API_BASE_URL}/auth/init`, {
          withCredentials: true
        })
        window.location.href = response.data.auth_url
      } catch (error) {
        console.error('Error initiating login:', error)
        alert('Failed to initiate login')
      }
    },
    async logout() {
      try {
        await axios.post(`${API_BASE_URL}/auth/logout`, {}, {
          withCredentials: true
        })
        this.authenticated = false
        this.events = []
        this.calendars = []
      } catch (error) {
        console.error('Error logging out:', error)
      }
    },
    async fetchEvents() {
      this.loadingEvents = true
      this.eventsError = null

      try {
        const response = await axios.get(`${API_BASE_URL}/events`, {
          params: { max_results: 20 },
          withCredentials: true
        })
        this.events = response.data.events
      } catch (error) {
        console.error('Error fetching events:', error)
        this.eventsError = error.response?.data?.error || 'Failed to fetch events'
      } finally {
        this.loadingEvents = false
      }
    },
    async fetchCalendars() {
      this.loadingCalendars = true
      this.calendarsError = null

      try {
        const response = await axios.get(`${API_BASE_URL}/calendars`, {
          withCredentials: true
        })
        this.calendars = response.data.calendars
      } catch (error) {
        console.error('Error fetching calendars:', error)
        this.calendarsError = error.response?.data?.error || 'Failed to fetch calendars'
      } finally {
        this.loadingCalendars = false
      }
    },
    handleAuthCallback() {
      const urlParams = new URLSearchParams(window.location.search)
      const authStatus = urlParams.get('auth')

      if (authStatus === 'success') {
        this.authenticated = true
        window.history.replaceState({}, document.title, '/')
      } else if (authStatus === 'error') {
        const message = urlParams.get('message')
        alert(`Authentication failed: ${message}`)
        window.history.replaceState({}, document.title, '/')
      }
    },
    formatEventTime(event) {
      const start = event.start?.dateTime || event.start?.date
      const end = event.end?.dateTime || event.end?.date

      if (!start) return 'No time specified'

      const startDate = new Date(start)
      const endDate = end ? new Date(end) : null

      const options = {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }

      let timeString = startDate.toLocaleString('en-US', options)

      if (endDate) {
        timeString += ` - ${endDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}`
      }

      return timeString
    }
  }
}
</script>
