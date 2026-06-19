/**
 * AppLayout — Wraps authenticated pages with Sidebar + main content area
 */

import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import ChatBot from './ChatBot'

export default function AppLayout() {
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="app-main">
        <Outlet />
      </main>
      <ChatBot />
    </div>
  )
}
