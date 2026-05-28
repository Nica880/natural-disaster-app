import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'
import App from './App.jsx'
import Home from './routes/Home.jsx'
import Analyze from './routes/Analyze.jsx'
import Monitor from './routes/Monitor.jsx'
import About from './routes/About.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<App />}>
          {/* Monitor is the operator's main workspace — it's the default landing. */}
          <Route index element={<Monitor />} />
          <Route path="analyze" element={<Analyze />} />
          <Route path="overview" element={<Home />} />
          <Route path="about" element={<About />} />
          {/* Legacy /monitor path kept so old bookmarks still resolve. */}
          <Route path="monitor" element={<Navigate to="/" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
