<template>
  <div id="app">
    <div class="app-header">
      <h1>Google Calendar</h1>
      <button v-if="authenticated" @click="logout" class="logout-btn">Logout</button>
    </div>

    <div v-if="!authenticated" class="login-container">
      <div class="login-card">
        <h2>Login to Google Calendar</h2>
        <p>View your Google Calendar events in an integrated calendar interface.</p>
        <button @click="login" class="login-btn">Login with Google</button>
      </div>
    </div>

    <div v-else>
      <div v-if="loadingEvents" class="loading-overlay">
        <div class="loading-spinner">Loading calendar...</div>
      </div>

      <div v-if="eventsError" class="error-banner">
        {{ eventsError }}
      </div>

      <CalendarView
        :events="events"
        @month-changed="onMonthChanged"
      />
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import CalendarView from './components/CalendarView.vue'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

export default {
  name: 'App',
  components: {
    CalendarView
  },
  data() {
    return {
      authenticated: false,
      events: [],
      loadingEvents: false,
      eventsError: null,
      currentMonth: new Date().getMonth(),
      currentYear: new Date().getFullYear()
    }
  },
  mounted() {
    console.log('[App] Component mounted')
    this.checkAuthStatus()
    this.handleAuthCallback()
  },
  watch: {
    authenticated(newVal) {
      if (newVal) {
        this.fetchEventsForMonth(this.currentMonth, this.currentYear)
      }
    }
  },
  methods: {
    async checkAuthStatus() {
      console.log('[Auth] Checking authentication status')
      try {
        const response = await axios.get(`${API_BASE_URL}/auth/status`, {
          withCredentials: true
        })
        console.log('[Auth] Status response:', response.data)
        this.authenticated = response.data.authenticated
        console.log('[Auth] Authenticated:', this.authenticated)
      } catch (error) {
        console.error('[Auth] Error checking auth status:', error)
        console.error('[Auth] Error details:', error.response?.data)
      }
    },
    async login() {
      console.log('[Auth] Initiating login')
      try {
        const response = await axios.get(`${API_BASE_URL}/auth/init`, {
          withCredentials: true
        })
        console.log('[Auth] Auth URL received:', response.data.auth_url)
        console.log('[Auth] Redirecting to Google OAuth...')
        window.location.href = response.data.auth_url
      } catch (error) {
        console.error('[Auth] Error initiating login:', error)
        console.error('[Auth] Error details:', error.response?.data)
        alert('Failed to initiate login')
      }
    },
    async logout() {
      console.log('[Auth] Logging out')
      try {
        await axios.post(`${API_BASE_URL}/auth/logout`, {}, {
          withCredentials: true
        })
        console.log('[Auth] Logout successful')
        this.authenticated = false
        this.events = []
        this.calendars = []
        console.log('[Auth] State cleared')
      } catch (error) {
        console.error('[Auth] Error logging out:', error)
        console.error('[Auth] Error details:', error.response?.data)
      }
    },
    async fetchEventsForMonth(month, year) {
      console.log('[Events] Fetching events for', month, year)
      this.loadingEvents = true
      this.eventsError = null

      try {
        // Get first and last day of the month
        const firstDay = new Date(year, month, 1)
        const lastDay = new Date(year, month + 1, 0, 23, 59, 59)

        // Format as ISO strings
        const timeMin = firstDay.toISOString()
        const timeMax = lastDay.toISOString()

        console.log('[Events] Date range:', timeMin, 'to', timeMax)

        const response = await axios.get(`${API_BASE_URL}/events`, {
          params: {
            time_min: timeMin,
            time_max: timeMax,
            max_results: 250
          },
          withCredentials: true
        })

        console.log('[Events] Received events:', response.data)
        console.log('[Events] Event count:', response.data.events?.length || 0)
        this.events = response.data.events
      } catch (error) {
        console.error('[Events] Error fetching events:', error)
        console.error('[Events] Error details:', error.response?.data)
        this.eventsError = error.response?.data?.error || 'Failed to fetch events'
      } finally {
        this.loadingEvents = false
        console.log('[Events] Loading complete')
      }
    },
    onMonthChanged({ month, year }) {
      console.log('[Calendar] Month changed to', month, year)
      this.currentMonth = month
      this.currentYear = year
      this.fetchEventsForMonth(month, year)
    },
    handleAuthCallback() {
      const urlParams = new URLSearchParams(window.location.search)
      const authStatus = urlParams.get('auth')

      if (authStatus === 'success') {
        console.log('[Auth] Authentication callback: SUCCESS')
        this.authenticated = true
        window.history.replaceState({}, document.title, '/')
      } else if (authStatus === 'error') {
        const message = urlParams.get('message')
        console.error('[Auth] Authentication callback: ERROR -', message)
        alert(`Authentication failed: ${message}`)
        window.history.replaceState({}, document.title, '/')
      } else if (authStatus) {
        console.log('[Auth] Unknown auth status:', authStatus)
      }
    }
  }
}
</script>

<style scoped>
#app {
  min-height: 100vh;
  background: #f8f9fa;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
}

.app-header {
  background: #fff;
  padding: 16px 24px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.app-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
  color: #202124;
}

.logout-btn {
  background: #fff;
  border: 1px solid #dadce0;
  border-radius: 4px;
  padding: 8px 16px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  color: #202124;
}

.logout-btn:hover {
  background: #f8f9fa;
  border-color: #5f6368;
}

.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 72px);
  padding: 20px;
}

.login-card {
  background: #fff;
  padding: 48px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
  text-align: center;
  max-width: 400px;
}

.login-card h2 {
  margin: 0 0 16px 0;
  font-size: 24px;
  font-weight: 500;
  color: #202124;
}

.login-card p {
  margin: 0 0 32px 0;
  color: #5f6368;
  line-height: 1.5;
}

.login-btn {
  background: #1a73e8;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.login-btn:hover {
  background: #1557b0;
}

.loading-overlay {
  text-align: center;
  padding: 20px;
}

.loading-spinner {
  color: #5f6368;
  font-size: 16px;
}

.error-banner {
  background: #fce8e6;
  color: #c5221f;
  padding: 16px;
  margin: 16px 24px;
  border-radius: 4px;
  border-left: 4px solid #c5221f;
}
</style>
