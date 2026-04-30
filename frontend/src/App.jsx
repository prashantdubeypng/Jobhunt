import { useEffect, useMemo, useState } from 'react'
import './App.css'
import { ResumeUploadComponent } from './ResumeUploadComponent'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/v1/api/users'
const FRONTEND_ORIGIN = import.meta.env.VITE_FRONTEND_URL ?? 'http://localhost:5173'
const TOKEN_STORAGE_KEY = 'jobhunt_app_token'

const emptyPreferences = {
  target_job_titles: [],
  target_locations: [],
  target_companies: [],
  target_sources: ['y_combinator', 'linkedin'],
  auto_apply: false,
  auto_email: false,
  linkedin_outreach: false,
  weekly_digest: true,
  default_resume: '',
}

const emptyResume = {
  title: '',
  file: '',
  parsed_text: '',
  notes: '',
  is_primary: false,
}

const emptyApplication = {
  resume: '',
  company_name: '',
  company_website: '',
  role_title: '',
  role_location: '',
  source: 'manual',
  source_url: '',
  tracking_url: '',
  status: 'draft',
  cover_letter: '',
  application_payload: '{}',
  response_summary: '',
  notes: '',
  applied_at: '',
}

const emptyOutreach = {
  application: '',
  resume: '',
  recipient_name: '',
  recipient_email: '',
  recipient_linkedin_url: '',
  channel: 'email',
  subject: '',
  body: '',
  status: 'draft',
  error_message: '',
}

function readToken() {
  return window.localStorage.getItem(TOKEN_STORAGE_KEY) ?? ''
}

function saveToken(token) {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token)
}

function clearToken() {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY)
}

async function request(path, options = {}, token = '') {
  const headers = new Headers(options.headers || {})
  headers.set('Accept', 'application/json')

  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData
  if (options.body && !isFormData) {
    headers.set('Content-Type', 'application/json')
  }

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    body: options.body && !isFormData ? JSON.stringify(options.body) : options.body,
  })

  const contentType = response.headers.get('content-type') || ''
  const data = contentType.includes('application/json') ? await response.json() : null

  if (!response.ok) {
    throw new Error(data?.detail || data?.message || 'Request failed.')
  }

  return data
}

function splitList(value) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function parseCallbackToken() {
  const hash = window.location.hash.replace(/^#/, '')
  if (!hash) {
    return null
  }

  const params = new URLSearchParams(hash)
  const token = params.get('token')
  const email = params.get('email') || ''
  const userId = params.get('user_id') || ''
  if (!token) {
    return null
  }

  return { token, email, userId }
}

function LoginScreen({ onLogin }) {
  return (
    <main className="shell shell-login">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">AI Job Hunting Agent</p>
          <h1>Track applications, resumes, and outreach in one place.</h1>
          <p className="lede">
            Use Google OAuth to connect your backend and manage the full job search workflow without spreadsheets.
          </p>

          <div className="hero-actions">
            <button className="primary-btn" onClick={onLogin}>
              Continue with Google
            </button>
            <a className="secondary-link" href="#features">
              Explore features
            </a>
          </div>
        </div>

        <div className="hero-panel">
          <div className="glass-card">
            <p className="panel-label">What you can do</p>
            <ul className="mini-list">
              <li>Sign in with Google OAuth</li>
              <li>Store resumes and preferences</li>
              <li>Track applications, status, and outreach</li>
              <li>Review your dashboard statistics</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="feature-grid" id="features">
        <article className="feature-card">
          <h3>Applications</h3>
          <p>Save each application, update statuses, and keep a history of progress.</p>
        </article>
        <article className="feature-card">
          <h3>Resumes</h3>
          <p>Upload multiple resumes and mark one as the primary profile for submissions.</p>
        </article>
        <article className="feature-card">
          <h3>Outreach</h3>
          <p>Draft email or LinkedIn outreach linked to the right role and resume.</p>
        </article>
      </section>
    </main>
  )
}

function Field({ label, children, hint }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
      {hint ? <small>{hint}</small> : null}
    </label>
  )
}

function TextInput(props) {
  return <input className="input" {...props} />
}

function TextArea(props) {
  return <textarea className="input textarea" {...props} />
}

function Select(props) {
  return <select className="input" {...props} />
}

function DashboardCard({ title, children, className = '' }) {
  return (
    <section className={`content-card ${className}`.trim()}>
      <h2>{title}</h2>
      {children}
    </section>
  )
}

function AppShell({ token, email, userId, onLogout }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [profile, setProfile] = useState(null)
  const [dashboard, setDashboard] = useState(null)
  const [preferences, setPreferences] = useState(emptyPreferences)
  const [resumes, setResumes] = useState([])
  const [applications, setApplications] = useState([])
  const [outreach, setOutreach] = useState([])
  const [activeTab, setActiveTab] = useState('dashboard')
  const [resumeForm, setResumeForm] = useState(emptyResume)
  const [applicationForm, setApplicationForm] = useState(emptyApplication)
  const [outreachForm, setOutreachForm] = useState(emptyOutreach)
  const [saving, setSaving] = useState(false)

  const summaryCards = useMemo(() => {
    return [
      { label: 'Applications', value: dashboard?.stats?.application_counts ? Object.values(dashboard.stats.application_counts).reduce((count, value) => count + Number(value || 0), 0) : 0 },
      { label: 'Resumes', value: dashboard?.stats?.resume_count ?? resumes.length },
      { label: 'Outreach', value: dashboard?.stats?.outreach_count ?? outreach.length },
      { label: 'Digest', value: preferences.weekly_digest ? 'On' : 'Off' },
    ]
  }, [dashboard, preferences.weekly_digest, resumes.length, outreach.length])

  useEffect(() => {
    let isMounted = true

    async function loadData() {
      try {
        setLoading(true)
        setError('')

        const [me, dashboardData, preferenceData, resumeData, applicationData, outreachData] = await Promise.all([
          request('/me/', {}, token),
          request('/dashboard/', {}, token),
          request('/preferences/', {}, token),
          request('/resumes/', {}, token),
          request('/applications/', {}, token),
          request('/outreach/', {}, token),
        ])

        if (!isMounted) {
          return
        }

        setProfile(me)
        setDashboard(dashboardData)
        setPreferences({ ...emptyPreferences, ...preferenceData })
        setResumes(Array.isArray(resumeData) ? resumeData : [])
        setApplications(Array.isArray(applicationData) ? applicationData : [])
        setOutreach(Array.isArray(outreachData) ? outreachData : [])
        setApplicationForm((current) => ({ ...current, resume: applicationData?.[0]?.resume || '' }))
      } catch (requestError) {
        if (isMounted) {
          setError(requestError.message)
        }
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    loadData()

    return () => {
      isMounted = false
    }
  }, [token])

  async function refreshCollections() {
    const [dashboardData, preferenceData, resumeData, applicationData, outreachData] = await Promise.all([
      request('/dashboard/', {}, token),
      request('/preferences/', {}, token),
      request('/resumes/', {}, token),
      request('/applications/', {}, token),
      request('/outreach/', {}, token),
    ])

    setDashboard(dashboardData)
    setPreferences({ ...emptyPreferences, ...preferenceData })
    setResumes(Array.isArray(resumeData) ? resumeData : [])
    setApplications(Array.isArray(applicationData) ? applicationData : [])
    setOutreach(Array.isArray(outreachData) ? outreachData : [])
  }

  async function handlePreferenceSave(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = {
        ...preferences,
        target_job_titles: Array.isArray(preferences.target_job_titles) ? preferences.target_job_titles : splitList(preferences.target_job_titles || ''),
        target_locations: Array.isArray(preferences.target_locations) ? preferences.target_locations : splitList(preferences.target_locations || ''),
        target_companies: Array.isArray(preferences.target_companies) ? preferences.target_companies : splitList(preferences.target_companies || ''),
        target_sources: Array.isArray(preferences.target_sources) ? preferences.target_sources : splitList(preferences.target_sources || ''),
        default_resume: preferences.default_resume || null,
      }
      const updatedPreferences = await request('/preferences/', { method: 'PATCH', body: payload }, token)
      setPreferences({ ...emptyPreferences, ...updatedPreferences })
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleResumeCreate(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      const formData = new FormData()
      formData.append('title', resumeForm.title)
      if (resumeForm.file) {
        formData.append('file', resumeForm.file)
      }
      formData.append('parsed_text', resumeForm.parsed_text)
      formData.append('notes', resumeForm.notes)
      formData.append('is_primary', resumeForm.is_primary ? 'true' : 'false')
      await request('/resumes/', { method: 'POST', body: formData }, token)
      setResumeForm(emptyResume)
      await refreshCollections()
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleApplicationCreate(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = {
        ...applicationForm,
        resume: applicationForm.resume ? Number(applicationForm.resume) : null,
        application_payload: (() => {
          try {
            return JSON.parse(applicationForm.application_payload || '{}')
          } catch {
            return {}
          }
        })(),
      }
      await request('/applications/', { method: 'POST', body: payload }, token)
      setApplicationForm(emptyApplication)
      await refreshCollections()
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleOutreachCreate(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = {
        ...outreachForm,
        application: outreachForm.application ? Number(outreachForm.application) : null,
        resume: outreachForm.resume ? Number(outreachForm.resume) : null,
      }
      await request('/outreach/', { method: 'POST', body: payload }, token)
      setOutreachForm(emptyOutreach)
      await refreshCollections()
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleLogout() {
    try {
      await request('/auth/logout/', { method: 'POST' }, token)
    } catch {
      // Ignore logout failures and clear the local session anyway.
    } finally {
      clearToken()
      onLogout()
    }
  }

  if (loading) {
    return (
      <main className="shell shell-home loading-shell">
        <p className="eyebrow">Loading</p>
        <h1>Preparing your dashboard</h1>
      </main>
    )
  }

  return (
    <main className="shell shell-home">
      <header className="topbar">
        <div>
          <p className="eyebrow">Dashboard</p>
          <h1>Welcome back</h1>
          <p className="user-meta">
            {profile?.email || email || 'Signed in'} {userId ? `· User ${userId}` : ''}
          </p>
        </div>
        <button className="ghost-btn" onClick={handleLogout}>
          Logout
        </button>
      </header>

      {error ? <div className="alert-banner">{error}</div> : null}

      <section className="stats-grid">
        {summaryCards.map((stat) => (
          <article className="stat-card" key={stat.label}>
            <span>{stat.label}</span>
            <strong>{stat.value}</strong>
          </article>
        ))}
      </section>

      <nav className="tabbar">
        {['dashboard', 'preferences', 'resumes', 'applications', 'outreach'].map((tab) => (
          <button
            key={tab}
            className={activeTab === tab ? 'tab active' : 'tab'}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </nav>

      {activeTab === 'dashboard' ? (
        <section className="content-grid">
          <DashboardCard title="Recent applications" className="large">
            <div className="stack">
              {(dashboard?.recent_applications || applications.slice(0, 5)).map((application) => (
                <div className="timeline-item" key={application.id}>
                  <span className={`status-dot ${application.status || 'draft'}`} />
                  <div>
                    <strong>{application.company_name}</strong>
                    <p>
                      {application.role_title} · {application.status}
                    </p>
                  </div>
                </div>
              ))}
              {!applications.length ? <p className="muted">No applications yet.</p> : null}
            </div>
          </DashboardCard>

          <DashboardCard title="Quick actions">
            <div className="action-list">
              <button className="action-btn" onClick={() => setActiveTab('resumes')}>
                Manage resumes
              </button>
              <button className="action-btn" onClick={() => setActiveTab('applications')}>
                Add application
              </button>
              <button className="action-btn" onClick={() => setActiveTab('outreach')}>
                Draft outreach
              </button>
            </div>
          </DashboardCard>
        </section>
      ) : null}

      {activeTab === 'preferences' ? (
        <div className="content-grid two-col">
          <DashboardCard title="Job preferences">
            <form className="form-grid" onSubmit={handlePreferenceSave}>
              <Field label="Target job titles" hint="Comma separated values">
                <TextInput
                  value={Array.isArray(preferences.target_job_titles) ? preferences.target_job_titles.join(', ') : preferences.target_job_titles || ''}
                  onChange={(event) => setPreferences((current) => ({ ...current, target_job_titles: splitList(event.target.value) }))}
                />
              </Field>
              <Field label="Target locations" hint="Comma separated values">
                <TextInput
                  value={Array.isArray(preferences.target_locations) ? preferences.target_locations.join(', ') : preferences.target_locations || ''}
                  onChange={(event) => setPreferences((current) => ({ ...current, target_locations: splitList(event.target.value) }))}
                />
              </Field>
              <Field label="Target companies" hint="Comma separated values">
                <TextInput
                  value={Array.isArray(preferences.target_companies) ? preferences.target_companies.join(', ') : preferences.target_companies || ''}
                  onChange={(event) => setPreferences((current) => ({ ...current, target_companies: splitList(event.target.value) }))}
                />
              </Field>
              <Field label="Target sources" hint="Comma separated values">
                <TextInput
                  value={Array.isArray(preferences.target_sources) ? preferences.target_sources.join(', ') : preferences.target_sources || ''}
                  onChange={(event) => setPreferences((current) => ({ ...current, target_sources: splitList(event.target.value) }))}
                />
              </Field>
              <div className="toggle-grid">
                {[
                  ['auto_apply', 'Auto apply'],
                  ['auto_email', 'Auto email'],
                  ['linkedin_outreach', 'LinkedIn outreach'],
                  ['weekly_digest', 'Weekly digest'],
                ].map(([key, label]) => (
                  <label className="toggle" key={key}>
                    <input
                      type="checkbox"
                      checked={Boolean(preferences[key])}
                      onChange={(event) => setPreferences((current) => ({ ...current, [key]: event.target.checked }))}
                    />
                    <span>{label}</span>
                  </label>
                ))}
              </div>
              <Field label="Default resume">
                <Select
                  value={preferences.default_resume || ''}
                  onChange={(event) => setPreferences((current) => ({ ...current, default_resume: event.target.value }))}
                >
                  <option value="">Select a resume</option>
                  {resumes.map((resume) => (
                    <option key={resume.id} value={resume.id}>
                      {resume.title}
                    </option>
                  ))}
                </Select>
              </Field>
              <button className="primary-btn" disabled={saving}>
                Save preferences
              </button>
            </form>
          </DashboardCard>

          <DashboardCard title="Preference summary">
            <div className="stack">
              <p className="muted">Dashboard source: /v1/api/users/preferences/</p>
              <p className="muted">Applications are filtered using the same backend preferences.</p>
            </div>
          </DashboardCard>
        </div>
      ) : null}

      {activeTab === 'resumes' ? (
        <div className="content-grid two-col">
          <DashboardCard title="Upload resume (S3)">
            <ResumeUploadComponent 
              token={token} 
              onUploadComplete={() => refreshCollections()}
              onError={(msg) => setError(msg)}
            />
          </DashboardCard>

          <DashboardCard title="Your resumes">
            <div className="stack">
              {resumes.map((resume) => (
                <article className="mini-record" key={resume.id}>
                  <strong>{resume.title}</strong>
                  <p>{resume.is_primary ? '⭐ Primary resume' : 'Secondary resume'}</p>
                  {resume.upload_status && (
                    <p className="muted">Status: {resume.upload_status}</p>
                  )}
                  {resume.s3_url && (
                    <p className="muted">📦 S3: {resume.s3_key}</p>
                  )}
                  {resume.uploaded_at && (
                    <p className="muted">📅 {new Date(resume.uploaded_at).toLocaleDateString()}</p>
                  )}
                </article>
              ))}
              {!resumes.length ? <p className="muted">No resumes uploaded yet.</p> : null}
            </div>
          </DashboardCard>
        </div>
      ) : null}

      {activeTab === 'applications' ? (
        <div className="content-grid two-col">
          <DashboardCard title="Add application">
            <form className="form-grid" onSubmit={handleApplicationCreate}>
              <Field label="Resume">
                <Select value={applicationForm.resume} onChange={(event) => setApplicationForm((current) => ({ ...current, resume: event.target.value }))}>
                  <option value="">Select resume</option>
                  {resumes.map((resume) => (
                    <option key={resume.id} value={resume.id}>
                      {resume.title}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Company name">
                <TextInput value={applicationForm.company_name} onChange={(event) => setApplicationForm((current) => ({ ...current, company_name: event.target.value }))} required />
              </Field>
              <Field label="Role title">
                <TextInput value={applicationForm.role_title} onChange={(event) => setApplicationForm((current) => ({ ...current, role_title: event.target.value }))} required />
              </Field>
              <Field label="Source">
                <Select value={applicationForm.source} onChange={(event) => setApplicationForm((current) => ({ ...current, source: event.target.value }))}>
                  <option value="manual">Manual</option>
                  <option value="linkedin">LinkedIn</option>
                  <option value="y_combinator">Y Combinator</option>
                </Select>
              </Field>
              <Field label="Status">
                <Select value={applicationForm.status} onChange={(event) => setApplicationForm((current) => ({ ...current, status: event.target.value }))}>
                  <option value="draft">Draft</option>
                  <option value="applied">Applied</option>
                  <option value="in_review">In review</option>
                  <option value="interview">Interview</option>
                  <option value="rejected">Rejected</option>
                  <option value="offer">Offer</option>
                  <option value="withdrawn">Withdrawn</option>
                </Select>
              </Field>
              <Field label="Company website">
                <TextInput value={applicationForm.company_website} onChange={(event) => setApplicationForm((current) => ({ ...current, company_website: event.target.value }))} />
              </Field>
              <Field label="Role location">
                <TextInput value={applicationForm.role_location} onChange={(event) => setApplicationForm((current) => ({ ...current, role_location: event.target.value }))} />
              </Field>
              <Field label="Source URL">
                <TextInput value={applicationForm.source_url} onChange={(event) => setApplicationForm((current) => ({ ...current, source_url: event.target.value }))} />
              </Field>
              <Field label="Tracking URL">
                <TextInput value={applicationForm.tracking_url} onChange={(event) => setApplicationForm((current) => ({ ...current, tracking_url: event.target.value }))} />
              </Field>
              <Field label="Application payload" hint="JSON object">
                <TextArea value={applicationForm.application_payload} onChange={(event) => setApplicationForm((current) => ({ ...current, application_payload: event.target.value }))} rows="4" />
              </Field>
              <Field label="Cover letter">
                <TextArea value={applicationForm.cover_letter} onChange={(event) => setApplicationForm((current) => ({ ...current, cover_letter: event.target.value }))} rows="4" />
              </Field>
              <Field label="Notes">
                <TextArea value={applicationForm.notes} onChange={(event) => setApplicationForm((current) => ({ ...current, notes: event.target.value }))} rows="3" />
              </Field>
              <button className="primary-btn" disabled={saving}>
                Save application
              </button>
            </form>
          </DashboardCard>

          <DashboardCard title="Application list">
            <div className="stack">
              {applications.map((application) => (
                <article className="mini-record" key={application.id}>
                  <strong>{application.company_name}</strong>
                  <p>
                    {application.role_title} · {application.status}
                  </p>
                </article>
              ))}
              {!applications.length ? <p className="muted">No applications yet.</p> : null}
            </div>
          </DashboardCard>
        </div>
      ) : null}

      {activeTab === 'outreach' ? (
        <div className="content-grid two-col">
          <DashboardCard title="Draft outreach">
            <form className="form-grid" onSubmit={handleOutreachCreate}>
              <Field label="Application">
                <Select value={outreachForm.application} onChange={(event) => setOutreachForm((current) => ({ ...current, application: event.target.value }))}>
                  <option value="">Select application</option>
                  {applications.map((application) => (
                    <option key={application.id} value={application.id}>
                      {application.company_name}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Resume">
                <Select value={outreachForm.resume} onChange={(event) => setOutreachForm((current) => ({ ...current, resume: event.target.value }))}>
                  <option value="">Select resume</option>
                  {resumes.map((resume) => (
                    <option key={resume.id} value={resume.id}>
                      {resume.title}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Recipient name">
                <TextInput value={outreachForm.recipient_name} onChange={(event) => setOutreachForm((current) => ({ ...current, recipient_name: event.target.value }))} required />
              </Field>
              <Field label="Recipient email">
                <TextInput value={outreachForm.recipient_email} onChange={(event) => setOutreachForm((current) => ({ ...current, recipient_email: event.target.value }))} />
              </Field>
              <Field label="LinkedIn URL">
                <TextInput value={outreachForm.recipient_linkedin_url} onChange={(event) => setOutreachForm((current) => ({ ...current, recipient_linkedin_url: event.target.value }))} />
              </Field>
              <Field label="Channel">
                <Select value={outreachForm.channel} onChange={(event) => setOutreachForm((current) => ({ ...current, channel: event.target.value }))}>
                  <option value="email">Email</option>
                  <option value="linkedin">LinkedIn</option>
                </Select>
              </Field>
              <Field label="Subject">
                <TextInput value={outreachForm.subject} onChange={(event) => setOutreachForm((current) => ({ ...current, subject: event.target.value }))} />
              </Field>
              <Field label="Body">
                <TextArea value={outreachForm.body} onChange={(event) => setOutreachForm((current) => ({ ...current, body: event.target.value }))} rows="5" required />
              </Field>
              <Field label="Status">
                <Select value={outreachForm.status} onChange={(event) => setOutreachForm((current) => ({ ...current, status: event.target.value }))}>
                  <option value="draft">Draft</option>
                  <option value="queued">Queued</option>
                  <option value="sent">Sent</option>
                  <option value="delivered">Delivered</option>
                  <option value="opened">Opened</option>
                  <option value="replied">Replied</option>
                  <option value="failed">Failed</option>
                </Select>
              </Field>
              <Field label="Error message">
                <TextArea value={outreachForm.error_message} onChange={(event) => setOutreachForm((current) => ({ ...current, error_message: event.target.value }))} rows="3" />
              </Field>
              <button className="primary-btn" disabled={saving}>
                Save outreach
              </button>
            </form>
          </DashboardCard>

          <DashboardCard title="Outreach list">
            <div className="stack">
              {outreach.map((message) => (
                <article className="mini-record" key={message.id}>
                  <strong>{message.recipient_name}</strong>
                  <p>
                    {message.channel} · {message.status}
                  </p>
                </article>
              ))}
              {!outreach.length ? <p className="muted">No outreach yet.</p> : null}
            </div>
          </DashboardCard>
        </div>
      ) : null}
    </main>
  )
}

function App() {
  const [session, setSession] = useState(() => {
    const token = readToken()
    return { token, email: '', userId: '' }
  })
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const callback = parseCallbackToken()
    if (callback) {
      saveToken(callback.token)
      setSession(callback)
      window.history.replaceState({}, '', '/')
    }
    setReady(true)
  }, [])

  const handleLogin = () => {
    window.location.href = `${API_BASE_URL}/auth/google/`
  }

  const handleLogout = () => {
    setSession({ token: '', email: '', userId: '' })
  }

  if (!ready) {
    return <main className="shell shell-login loading-shell">Loading...</main>
  }

  if (!session.token) {
    return <LoginScreen onLogin={handleLogin} />
  }

  return <AppShell token={session.token} email={session.email} userId={session.userId} onLogout={handleLogout} />
}

export default App
