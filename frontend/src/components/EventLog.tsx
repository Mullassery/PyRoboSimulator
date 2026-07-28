import React from 'react'
import '../styles/EventLog.css'

interface Event {
  id: number
  type: string
  agent_id: number
  pos: [number, number, number]
  data?: Record<string, any>
}

interface EventLogProps {
  events: Event[]
}

export default function EventLog({ events }: EventLogProps) {
  return (
    <div className="event-log">
      <h3>Recent Events</h3>
      <div className="events-list">
        {events.length === 0 ? (
          <p className="empty-message">No events yet</p>
        ) : (
          events.slice(-20).map((event) => (
            <div key={event.id} className={`event-item event-${event.type}`}>
              <span className="event-type">{event.type}</span>
              <span className="event-agent">Agent {event.agent_id}</span>
              <span className="event-pos">
                ({event.pos[0].toFixed(1)}, {event.pos[1].toFixed(1)})
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
