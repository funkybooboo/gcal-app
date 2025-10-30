<template>
  <div class="calendar-container">
    <div class="calendar-header">
      <button @click="previousMonth" class="nav-button">&lt;</button>
      <h2>{{ monthName }} {{ currentYear }}</h2>
      <button @click="nextMonth" class="nav-button">&gt;</button>
    </div>

    <div class="calendar-grid">
      <div class="day-header" v-for="day in weekDays" :key="day">
        {{ day }}
      </div>

      <div
        v-for="day in calendarDays"
        :key="day.id"
        class="day-cell"
        :class="{
          'other-month': !day.isCurrentMonth,
          'today': day.isToday
        }"
      >
        <div class="day-number">{{ day.date }}</div>
        <div class="events-container">
          <div
            v-for="event in day.events"
            :key="event.id"
            class="event"
            :style="{ backgroundColor: event.color }"
            :title="event.summary + '\n' + event.time"
          >
            <span class="event-time">{{ event.time }}</span>
            <span class="event-title">{{ event.summary }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CalendarView',
  props: {
    events: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      currentMonth: new Date().getMonth(),
      currentYear: new Date().getFullYear(),
      weekDays: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    }
  },
  computed: {
    monthName() {
      const months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
      ]
      return months[this.currentMonth]
    },
    calendarDays() {
      const days = []
      const firstDay = new Date(this.currentYear, this.currentMonth, 1)
      const lastDay = new Date(this.currentYear, this.currentMonth + 1, 0)
      const prevLastDay = new Date(this.currentYear, this.currentMonth, 0)

      const firstDayOfWeek = firstDay.getDay()
      const lastDate = lastDay.getDate()
      const prevLastDate = prevLastDay.getDate()

      const today = new Date()
      today.setHours(0, 0, 0, 0)

      // Previous month's days
      for (let i = firstDayOfWeek - 1; i >= 0; i--) {
        const date = prevLastDate - i
        const dayDate = new Date(this.currentYear, this.currentMonth - 1, date)
        days.push({
          id: `prev-${date}`,
          date: date,
          isCurrentMonth: false,
          isToday: false,
          fullDate: dayDate,
          events: this.getEventsForDay(dayDate)
        })
      }

      // Current month's days
      for (let date = 1; date <= lastDate; date++) {
        const dayDate = new Date(this.currentYear, this.currentMonth, date)
        const isToday = dayDate.getTime() === today.getTime()
        days.push({
          id: `current-${date}`,
          date: date,
          isCurrentMonth: true,
          isToday: isToday,
          fullDate: dayDate,
          events: this.getEventsForDay(dayDate)
        })
      }

      // Next month's days to fill the grid
      const remainingDays = 42 - days.length // 6 rows * 7 days
      for (let date = 1; date <= remainingDays; date++) {
        const dayDate = new Date(this.currentYear, this.currentMonth + 1, date)
        days.push({
          id: `next-${date}`,
          date: date,
          isCurrentMonth: false,
          isToday: false,
          fullDate: dayDate,
          events: this.getEventsForDay(dayDate)
        })
      }

      return days
    }
  },
  methods: {
    previousMonth() {
      if (this.currentMonth === 0) {
        this.currentMonth = 11
        this.currentYear--
      } else {
        this.currentMonth--
      }
      this.$emit('month-changed', { month: this.currentMonth, year: this.currentYear })
    },
    nextMonth() {
      if (this.currentMonth === 11) {
        this.currentMonth = 0
        this.currentYear++
      } else {
        this.currentMonth++
      }
      this.$emit('month-changed', { month: this.currentMonth, year: this.currentYear })
    },
    getEventsForDay(dayDate) {
      if (!this.events || this.events.length === 0) return []

      return this.events.filter(event => {
        const eventDate = new Date(event.start.dateTime || event.start.date)
        eventDate.setHours(0, 0, 0, 0)
        const compareDate = new Date(dayDate)
        compareDate.setHours(0, 0, 0, 0)

        return eventDate.getTime() === compareDate.getTime()
      }).map(event => {
        return {
          id: event.id,
          summary: event.summary || 'No Title',
          time: this.formatEventTime(event),
          color: this.getEventColor(event),
          ...event
        }
      })
    },
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
    },
    getEventColor(event) {
      // Use a hash of the calendar ID to generate consistent colors
      if (event.calendarId) {
        const hash = event.calendarId.split('').reduce((acc, char) => {
          return char.charCodeAt(0) + ((acc << 5) - acc)
        }, 0)
        const colors = ['#4285f4', '#ea4335', '#fbbc04', '#34a853', '#ff6d00', '#46bdc6', '#7baaf7', '#f07b72']
        return colors[Math.abs(hash) % colors.length]
      }
      return '#4285f4'
    }
  }
}
</script>

<style scoped>
.calendar-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 10px;
}

.calendar-header h2 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  color: #202124;
}

.nav-button {
  background: #fff;
  border: 1px solid #dadce0;
  border-radius: 4px;
  padding: 8px 16px;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-button:hover {
  background: #f8f9fa;
  border-color: #5f6368;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1px;
  background: #dadce0;
  border: 1px solid #dadce0;
  border-radius: 8px;
  overflow: hidden;
}

.day-header {
  background: #f8f9fa;
  padding: 12px;
  text-align: center;
  font-weight: 600;
  font-size: 14px;
  color: #5f6368;
  text-transform: uppercase;
}

.day-cell {
  background: #fff;
  min-height: 120px;
  padding: 8px;
  position: relative;
  cursor: pointer;
  transition: background 0.2s;
}

.day-cell:hover {
  background: #f8f9fa;
}

.day-cell.other-month {
  background: #fafafa;
  color: #9aa0a6;
}

.day-cell.other-month:hover {
  background: #f1f3f4;
}

.day-cell.today {
  background: #e8f0fe;
}

.day-cell.today .day-number {
  background: #1a73e8;
  color: white;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.day-number {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
  color: #202124;
}

.events-container {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.event {
  padding: 2px 4px;
  border-radius: 3px;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: white;
  cursor: pointer;
  transition: opacity 0.2s;
}

.event:hover {
  opacity: 0.8;
}

.event-time {
  font-weight: 600;
  margin-right: 4px;
}

.event-title {
  font-weight: 400;
}

@media (max-width: 768px) {
  .calendar-container {
    padding: 10px;
  }

  .day-cell {
    min-height: 80px;
    padding: 4px;
  }

  .event {
    font-size: 10px;
  }

  .day-number {
    font-size: 12px;
  }
}
</style>
