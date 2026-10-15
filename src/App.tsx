import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { ArrowDown, ArrowLeft, ArrowRight, ArrowUp, ArrowUpRight, Bookmark, Bus, Check, ChevronDown, CircleHelp, Clock3, Compass, CloudSun, Heart, Home, LogOut, Map, MapPin, Menu, Plus, Search, Settings, Share2, ShieldCheck, Sparkles, Star, Trash2, TrainFront, UsersRound, Wallet, Wind, X } from 'lucide-react'
import { authApi, friendsApi, placesApi, profileApi, tripsApi, type Budget, type Place, type Profile, type Recommendation, type Stop, type TransportOption, type Trip, type User } from './api'

const interests = ['history', 'food', 'nature', 'spiritual', 'shopping', 'nightlife']
const categories = ['All places', 'Heritage', 'Nature', 'Culture', 'Museum', 'Food & Shopping', 'Food & Nightlife', 'Shopping', 'Adventure']
const pretty = (value: string) => value.charAt(0).toUpperCase() + value.slice(1)
const money = (value: number) => `₹${Math.round(value).toLocaleString('en-IN')}`
const initials = (name: string) => name.split(' ').map((part) => part[0]).slice(0, 2).join('').toUpperCase()
const coverImage = (place: Place | Recommendation) => {
  const key = place.name.toLowerCase()
  if (key.includes('shaniwar')) return 'https://images.unsplash.com/photo-1606293926075-69a00dbfde81?auto=format&fit=crop&w=1000&q=85'
  if (key.includes('aga khan')) return 'https://images.unsplash.com/photo-1595658658481-d53d3f999875?auto=format&fit=crop&w=1000&q=85'
  if (key.includes('fort') || key.includes('hill') || key.includes('tekdi')) return 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1000&q=85'
  if (key.includes('garden') || key.includes('baug')) return 'https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?auto=format&fit=crop&w=1000&q=85'
  if (key.includes('temple') || key.includes('mahal')) return 'https://images.unsplash.com/photo-1605649487212-47bdab064df7?auto=format&fit=crop&w=1000&q=85'
  if (key.includes('fc road') || key.includes('koregaon') || key.includes('phoenix')) return 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1000&q=85'
  return 'https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1000&q=85'
}

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [profile, setProfile] = useState<Profile | null>(null)
  const [ready, setReady] = useState(false)
  const [notice, setNotice] = useState('')
  const location = useLocation()
  const navigate = useNavigate()

  const refreshProfile = useCallback(async () => {
    const response = await profileApi.get()
    setProfile(response.data)
    return response.data
  }, [])

  useEffect(() => {
    const token = localStorage.getItem('routewise_token')
    if (!token) { setReady(true); return }
    Promise.all([authApi.me(), profileApi.get()]).then(([me, details]) => {
      setUser(me.data)
      setProfile(details.data)
    }).catch(() => {
      localStorage.removeItem('routewise_token')
      setUser(null)
      setProfile(null)
    }).finally(() => setReady(true))
  }, [])

  useEffect(() => {
    const handleLogout = () => { setUser(null); setProfile(null); navigate('/login') }
    window.addEventListener('routewise:logout', handleLogout)
    return () => window.removeEventListener('routewise:logout', handleLogout)
  }, [navigate])

  useEffect(() => { if (notice) { const timer = window.setTimeout(() => setNotice(''), 3400); return () => window.clearTimeout(timer) } }, [notice])

  const signIn = async (nextUser: User, token: string) => {
    localStorage.setItem('routewise_token', token)
    setUser(nextUser)
    const details = await refreshProfile()
    navigate(details.interests.length ? '/' : '/onboarding')
  }
  const signOut = () => { localStorage.removeItem('routewise_token'); setUser(null); setProfile(null); navigate('/login') }
  const fullPage = ['/login', '/signup', '/onboarding'].includes(location.pathname)

  if (!ready) return <div className="loading-screen"><div className="brand-mark">R</div><span>Getting Pune ready for you…</span></div>

  return <>
    {!fullPage && user && profile && <AppShell user={user} profile={profile} onSignOut={signOut}><Routes><Route path="/" element={<Dashboard user={user} profile={profile} onNavigate={navigate} />} /><Route path="/explore" element={<Explore profile={profile} onNotice={setNotice} />} /><Route path="/planner" element={<Planner profile={profile} onNotice={setNotice} />} /><Route path="/saved" element={<Saved onNotice={setNotice} />} /><Route path="/friends" element={<Friends onNotice={setNotice} />} /><Route path="/profile" element={<ProfilePage profile={profile} onSave={async (data) => setProfile((await profileApi.save(data)).data)} onNotice={setNotice} />} /><Route path="*" element={<Dashboard user={user} profile={profile} onNavigate={navigate} />} /></Routes></AppShell>}
    {(!user || !profile || fullPage) && <Routes><Route path="/login" element={<AuthPage mode="login" onAuth={signIn} />} /><Route path="/signup" element={<AuthPage mode="signup" onAuth={signIn} />} /><Route path="/onboarding" element={user ? <Onboarding user={user} onDone={async (data) => { const result = await profileApi.save(data); setProfile(result.data); navigate('/') }} /> : <AuthPage mode="login" onAuth={signIn} />} /><Route path="*" element={user ? <Onboarding user={user} onDone={async (data) => { const result = await profileApi.save(data); setProfile(result.data); navigate('/') }} /> : <AuthPage mode="login" onAuth={signIn} />} /></Routes>}
    {notice && <div className="toast" role="status"><Check size={16} />{notice}</div>}
  </>
}

function AuthPage({ mode, onAuth }: { mode: 'login' | 'signup'; onAuth: (user: User, token: string) => Promise<void> }) {
  const [isSignup, setIsSignup] = useState(mode === 'signup')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()

  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setError(''); setBusy(true)
    try {
      if (isSignup) {
        const registered = await authApi.register({ name, email, password })
        const session = await authApi.login({ email, password })
        await onAuth(registered.data, session.data.access_token)
      } else {
        const session = await authApi.login({ email, password })
        await onAuth(session.data.user, session.data.access_token)
      }
    } catch (reason: unknown) {
      const message = (reason as { response?: { data?: { detail?: string } } }).response?.data?.detail
      setError(message || 'RouteWise could not connect to the API. Start the local services and try again.')
    } finally { setBusy(false) }
  }

  return <div className="auth-page">
    <div className="auth-photo"><div className="auth-photo-overlay" /><div className="auth-brand"><span className="brand-mark">R</span><span>RouteWise</span></div><div className="auth-caption"><span className="eyebrow">A city with a story on every street</span><h1>Find your own<br />way through Pune.</h1><p>The landmark you almost missed. The chai stop you’ll come back for. All part of the same day.</p><div className="auth-photo-credit"><MapPin size={14} /> A quiet moment above the old city</div></div><div className="auth-dots"><i /><i /><i /></div></div>
    <div className="auth-form-side"><Link to="/" className="auth-mobile-brand"><span className="brand-mark">R</span>RouteWise</Link><Link className="back-link" to="/"><ArrowLeft size={15} /> Back to welcome</Link><form className="auth-form" onSubmit={submit}>
      <div className="eyebrow">PUNE, YOUR WAY</div><h2>{isSignup ? 'Your next day out starts here.' : 'Good to have you back.'}</h2><p className="auth-subtitle">{isSignup ? 'Create your account and we’ll help you find your kind of Pune.' : 'Sign in to pick up right where your next adventure begins.'}</p>
      {isSignup && <label className="field-label">Your name<input autoComplete="name" value={name} onChange={(event) => setName(event.target.value)} placeholder="Aarav Deshmukh" minLength={2} required /></label>}
      <label className="field-label">Email address<input type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" required /></label>
      <label className="field-label">Password<input type="password" autoComplete={isSignup ? 'new-password' : 'current-password'} value={password} onChange={(event) => setPassword(event.target.value)} placeholder={isSignup ? 'At least 8 characters' : 'Enter your password'} minLength={isSignup ? 8 : 1} required /></label>
      {error && <div className="form-error" role="alert">{error}</div>}
      <button className="button button-dark button-full" type="submit" disabled={busy}>{busy ? 'One moment…' : isSignup ? 'Create my account' : 'Sign in'}<ArrowRight size={17} /></button>
      <div className="auth-switch">{isSignup ? 'Already have an account?' : 'New around here?'} <button type="button" onClick={() => { setIsSignup(!isSignup); setError(''); navigate(isSignup ? '/login' : '/signup') }}>{isSignup ? 'Sign in' : 'Create an account'}</button></div>
    </form><div className="auth-trust"><ShieldCheck size={15} />Your account and trips stay yours.</div></div>
  </div>
}

function Onboarding({ user, onDone }: { user: User; onDone: (data: Omit<Profile, 'id' | 'name' | 'email'>) => Promise<void> }) {
  const [selected, setSelected] = useState<string[]>([])
  const [budget, setBudget] = useState<Profile['budget_style']>('mid')
  const [transport, setTransport] = useState<Profile['preferred_transport']>('Bus')
  const [area, setArea] = useState('Pune Station')
  const [busy, setBusy] = useState(false)
  const toggle = (interest: string) => setSelected((current) => current.includes(interest) ? current.filter((item) => item !== interest) : [...current, interest])
  return <div className="onboarding-page"><div className="onboarding-top"><Link to="/" className="brand"><span className="brand-mark">R</span>RouteWise</Link><span>01 <span className="muted">/ 01</span></span></div><div className="onboarding-content"><div className="eyebrow">LET’S MAKE IT YOURS</div><h1>What does a good<br />day in Pune look like?</h1><p className="auth-subtitle">A few quick picks help us find places that feel like you, {user.name.split(' ')[0]}.</p><div className="onboarding-label">I’M DRAWN TO <span>Select a few</span></div><div className="interest-grid">{interests.map((item) => <button key={item} className={`interest-chip ${selected.includes(item) ? 'selected' : ''}`} onClick={() => toggle(item)} type="button"><span>{({ history: '🏛️', food: '☕', nature: '🌿', spiritual: '🪷', shopping: '🛍️', nightlife: '🌙' } as Record<string, string>)[item]}</span>{pretty(item)}{selected.includes(item) && <Check size={14} />}</button>)}</div><div className="onboarding-columns"><label className="field-label">My usual starting point<select value={area} onChange={(event) => setArea(event.target.value)}><option>Pune Station</option><option>Swargate</option><option>Shivajinagar</option><option>Kothrud</option><option>Hinjawadi</option><option>Koregaon Park</option><option>Viman Nagar</option></select></label><label className="field-label">My travel style<select value={transport} onChange={(event) => setTransport(event.target.value as Profile['preferred_transport'])}><option>Bus</option><option>Metro</option><option>Auto</option><option>Walk</option></select></label></div><div className="onboarding-label">MY SPENDING STYLE</div><div className="budget-choices">{([['budget', 'Keep it easy', 'Mostly free & affordable'], ['mid', 'A little of both', 'A treat here and there'], ['comfort', 'Here for the experience', 'Comfort over cost']] as const).map(([value, title, detail]) => <button key={value} type="button" className={`budget-choice ${budget === value ? 'active' : ''}`} onClick={() => setBudget(value)}><span className="radio-dot" /><span><strong>{title}</strong><small>{detail}</small></span></button>)}</div><button className="button button-dark button-full onboarding-submit" disabled={!selected.length || busy} onClick={async () => { setBusy(true); await onDone({ interests: selected, budget_style: budget, preferred_transport: transport, home_area: area, share_checkins: true }); setBusy(false) }}>{busy ? 'Building your Pune…' : 'Find my Pune'}<ArrowRight size={17} /></button><p className="onboarding-note">Your preferences can be changed anytime in your profile.</p></div></div>
}

function AppShell({ children, user, profile, onSignOut }: { children: React.ReactNode; user: User; profile: Profile; onSignOut: () => void }) {
  const location = useLocation()
  const [open, setOpen] = useState(false)
  const navItems = [{ to: '/', label: 'Today', icon: Home }, { to: '/explore', label: 'Explore Pune', icon: Compass }, { to: '/planner', label: 'My trip', icon: Map }, { to: '/saved', label: 'Saved trips', icon: Bookmark }, { to: '/friends', label: 'Travel friends', icon: UsersRound }]
  return <div className="app-layout"><aside className={`sidebar ${open ? 'sidebar-open' : ''}`}><Link to="/" className="brand"><span className="brand-mark">R</span><span>RouteWise</span></Link><div className="sidebar-city"><MapPin size={13} /> Pune, Maharashtra <ChevronDown size={13} /></div><div className="nav-section">YOUR SPACE</div><nav>{navItems.map(({ to, label, icon: Icon }) => <Link key={to} to={to} onClick={() => setOpen(false)} className={`nav-link ${location.pathname === to ? 'active' : ''}`}><Icon size={18} strokeWidth={1.8} /><span>{label}</span>{label === 'My trip' && <span className="nav-pip" />}</Link>)}</nav><div className="sidebar-tip"><div className="tip-icon"><Sparkles size={17} /></div><strong>A little local wisdom</strong><p>Shaniwar Wada is at its quietest just after opening time.</p><Link to="/explore">Explore places <ArrowRight size={13} /></Link></div><div className="sidebar-bottom"><Link to="/profile" className={`nav-link ${location.pathname === '/profile' ? 'active' : ''}`}><Settings size={18} strokeWidth={1.8} /><span>Preferences</span></Link><div className="sidebar-profile"><div className="avatar">{initials(user.name)}</div><div className="sidebar-profile-text"><strong>{user.name}</strong><span>{profile.home_area} local</span></div><button className="icon-button logout-button" onClick={onSignOut} title="Sign out" aria-label="Sign out"><LogOut size={16} /></button></div></div></aside><div className="main-area"><header className="topbar"><button className="icon-button menu-toggle" onClick={() => setOpen(!open)} aria-label="Toggle menu"><Menu size={19} /></button><div className="breadcrumb"><span className="breadcrumb-city">PUNE</span><span className="breadcrumb-slash">/</span><span>{navItems.find((item) => item.to === location.pathname)?.label || 'Preferences'}</span></div><div className="topbar-right"><div className="weather-pill"><CloudSun size={17} /><span>Plan a good day out</span></div><Link to="/profile" className="avatar avatar-small">{initials(user.name)}</Link></div></header><main className="page-content">{children}</main></div></div>
}

function Dashboard({ user, profile, onNavigate }: { user: User; profile: Profile; onNavigate: (path: string) => void }) {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [places, setPlaces] = useState<Place[]>([])
  const [trips, setTrips] = useState<Trip[]>([])
  const [weather, setWeather] = useState<{ temperature_c?: number; description?: string; available: boolean } | null>(null)
  useEffect(() => { placesApi.recommendations().then((response) => setRecommendations(response.data)).catch(() => setRecommendations([])); placesApi.list().then((response) => setPlaces(response.data)).catch(() => setPlaces([])); tripsApi.list().then((response) => setTrips(response.data)).catch(() => setTrips([])); tripsApi.weather().then((response) => setWeather(response.data)).catch(() => setWeather({ available: false })) }, [])
  const picks = recommendations.length ? recommendations.slice(0, 4) : places.slice(0, 4)
  const today = new Intl.DateTimeFormat('en-IN', { weekday: 'long', day: 'numeric', month: 'long' }).format(new Date())
  return <div className="dashboard-page"><div className="welcome-row"><div><div className="eyebrow">{today.toUpperCase()} <span className="dot-divider">·</span> YOUR PUNE EDITION</div><h1>Good morning, {user.name.split(' ')[0]}<span className="hello-dot">.</span></h1><p className="page-subtitle">Your next favourite corner of the city is closer than you think.</p></div><button className="button button-dark new-trip-button" onClick={() => onNavigate('/planner')}>Plan a day out <ArrowRight size={16} /></button></div><div className="hero-card"><img className="hero-image" src="https://images.unsplash.com/photo-1595658658481-d53d3f999875?auto=format&fit=crop&w=1800&q=90" alt="Historic palace and greenery in Pune" /><div className="hero-shade" /><div className="hero-content"><div className="hero-kicker"><span className="hero-kicker-dot" /> A CITY THAT REWARDS CURIOSITY</div><h2>Pune looks different<br />when you slow down.</h2><p>One fort, one filter coffee, one unplanned turn.<br />Let’s make a day of it.</p><button className="button button-light" onClick={() => onNavigate('/explore')}>Find your somewhere <ArrowRight size={16} /></button></div><div className="hero-side-note"><MapPin size={14} /> 18°31′N&nbsp; 73°51′E</div></div><div className="dashboard-section-heading"><div><div className="eyebrow">A GOOD PLACE TO START</div><h2>Picked with you in mind</h2></div><button className="text-button" onClick={() => onNavigate('/explore')}>See every place <ArrowRight size={15} /></button></div><div className="place-grid dashboard-place-grid">{picks.slice(0, 3).map((item) => <PlaceCard key={'poi_id' in item ? item.poi_id : item.id} place={item} onAdd={() => onNavigate('/planner')} />)}</div><div className="dashboard-bottom"><div className="mini-card weather-card"><div className="mini-card-top"><span className="mini-icon weather-icon"><CloudSun size={18} /></span><span className="eyebrow">OUTSIDE, RIGHT NOW</span><ArrowUpRight size={16} /></div><div className="weather-reading">{weather?.available && weather.temperature_c != null ? `${Math.round(weather.temperature_c)}°` : 'Pune'}<span>{weather?.available ? weather.description : 'Ready for a day out'}</span></div><div className="weather-foot"><Wind size={14} /> Live Pune weather via Open-Meteo</div></div><div className="mini-card saved-card"><div className="mini-card-top"><span className="mini-icon trip-icon"><Map size={18} /></span><span className="eyebrow">YOUR LITTLE PLANS</span></div><h3>{trips.length ? `${trips.length} ${trips.length === 1 ? 'trip' : 'trips'} taking shape` : 'A day out starts with one place.'}</h3><p>{trips[0]?.name || 'Keep the places you love together.'}</p><button className="text-button" onClick={() => onNavigate(trips.length ? '/saved' : '/planner')}>{trips.length ? 'Pick up where you left off' : 'Start a trip'} <ArrowRight size={15} /></button></div></div><div className="home-note"><Sparkles size={16} /> Made for your love of {profile.interests.slice(0, 2).map(pretty).join(' and ') || 'Pune'}.</div></div>
}

function PlaceCard({ place, onAdd, compact = false }: { place: Place | Recommendation; onAdd?: () => void; compact?: boolean }) {
  const name = place.name
  const key = 'poi_id' in place ? place.poi_id : place.id
  return <article className={`place-card ${compact ? 'place-card-compact' : ''}`}><div className="place-image-wrap"><img src={coverImage(place)} alt={name} /><span className="place-category">{place.category}</span><button className="save-place icon-button" aria-label={`Save ${name}`}><Heart size={17} /></button></div><div className="place-card-body"><div className="place-title-line"><h3>{name}</h3><span className="place-rating"><Star size={14} fill="currentColor" /> {place.rating.toFixed(1)}</span></div><div className="place-location"><MapPin size={13} /> {place.area}</div><p className="place-description">{place.description}</p><div className="place-card-footer"><span>{place.entry_fee ? `${money(place.entry_fee)} entry` : 'Free to explore'}<span className="footer-dot">·</span>{Math.round(place.recommended_duration / 60 * 10) / 10} hr</span>{onAdd && <button className="add-place-button" onClick={onAdd}><Plus size={14} /> Add to day</button>}</div></div><span className="sr-only">Place {key}</span></article>
}

function Explore({ profile, onNotice }: { profile: Profile; onNotice: (message: string) => void }) {
  const [places, setPlaces] = useState<Place[]>([])
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('All places')
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  useEffect(() => { placesApi.list().then((response) => setPlaces(response.data)).catch(() => onNotice('Could not load places. Please check the API connection.')).finally(() => setLoading(false)) }, [onNotice])
  const filtered = useMemo(() => places.filter((place) => (category === 'All places' || place.category.toLowerCase() === category.toLowerCase()) && `${place.name} ${place.area} ${place.tags} ${place.category}`.toLowerCase().includes(search.toLowerCase())), [places, category, search])
  const preferred = places.filter((place) => profile.interests.some((interest) => place.tags.toLowerCase().includes(interest))).slice(0, 3)
  const addPlace = async (place: Place) => {
    try {
      const response = await tripsApi.list()
      const current = response.data[0]
      if (!current) { onNotice('Start a day in My trip, then add places as you explore.'); navigate('/planner'); return }
      await tripsApi.addStop(current.id, place.id)
      onNotice(`${place.name} added to ${current.name}.`)
    } catch (error) {
      const detail = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
      onNotice(detail || 'Could not add this place to your trip.')
    }
  }
  return <div className="explore-page"><div className="page-heading-row"><div><div className="eyebrow">THE CITY IS YOURS</div><h1>Find your somewhere.</h1><p className="page-subtitle">The familiar favourites, the happy detours and everything in between.</p></div><span className="place-count"><Compass size={15} /> {places.length} local finds</span></div><div className="explore-spotlight"><div><div className="eyebrow">A ROUTEWISE LITTLE NUDGE</div><h2>{preferred[0]?.name || 'Pune is full of good surprises.'}</h2><p>{preferred[0] ? `${preferred[0].description} We picked it because you love ${profile.interests[0] || 'exploring'}.` : 'Take the day slowly. The city will meet you halfway.'}</p></div><div className="spotlight-mark"><Sparkles size={26} /><span>For you</span></div></div><div className="explore-controls"><label className="search-box"><Search size={17} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Try Shaniwar Wada, Koregaon Park…" /><kbd>/</kbd></label><div className="category-row">{categories.map((item) => <button className={`category-chip ${category === item ? 'active' : ''}`} key={item} onClick={() => setCategory(item)}>{item}</button>)}</div></div>{loading ? <div className="empty-state"><Compass className="spin-icon" size={22} /> Finding lovely places…</div> : filtered.length ? <div className="place-grid">{filtered.map((place) => <PlaceCard key={place.id} place={place} onAdd={() => addPlace(place)} />)}</div> : <div className="empty-state"><Search size={23} /><h3>Nothing around that corner.</h3><p>Try another name or pick a different category.</p></div>}<div className="along-route-panel"><div className="along-route-icon"><MapPin size={19} /></div><div><div className="eyebrow">GOING SOMEWHERE ANYWAY?</div><h3>Leave room for a good detour.</h3><p>Search Swargate to FC Road and add a few local favourites to your day.</p></div><Link to="/planner" className="button button-dark">Explore on my day <ArrowRight size={15} /></Link></div></div>
}

function Planner({ profile, onNotice }: { profile: Profile; onNotice: (message: string) => void }) {
  const [trip, setTrip] = useState<Trip | null>(null)
  const [stops, setStops] = useState<Stop[]>([])
  const [places, setPlaces] = useState<Place[]>([])
  const [budget, setBudget] = useState<Budget | null>(null)
  const [options, setOptions] = useState<TransportOption[]>([])
  const [selectedMode, setSelectedMode] = useState('')
  const [loading, setLoading] = useState(false)
  const [origin, setOrigin] = useState(profile.home_area === 'Pune Station' ? 'Swargate' : profile.home_area)
  const [budgetInput, setBudgetInput] = useState('1000')
  const [search, setSearch] = useState('')
  const [activeLeg, setActiveLeg] = useState<[number, number] | null>(null)
  const [shareUrl, setShareUrl] = useState('')

  const loadTrip = useCallback(async (current: Trip) => {
    const [stopResponse, budgetResponse] = await Promise.all([tripsApi.stops(current.id), tripsApi.budget(current.id)])
    setStops(stopResponse.data); setBudget(budgetResponse.data); setTrip(current)
    if (stopResponse.data.length > 1) {
      const first = stopResponse.data[0]; const second = stopResponse.data[1]
      try { const response = await tripsApi.options(current.id, first.stop_id, second.stop_id); setOptions(response.data.options); setActiveLeg([first.stop_id, second.stop_id]) } catch { setOptions([]) }
    } else { setOptions([]); setActiveLeg(null) }
  }, [])

  useEffect(() => { placesApi.list().then((response) => setPlaces(response.data)).catch(() => onNotice('Could not load places.')); tripsApi.list().then((response) => { if (response.data.length) loadTrip(response.data[0]) }).catch(() => onNotice('Could not load your trips.')) }, [loadTrip, onNotice])
  const candidates = places.filter((place) => !stops.some((stop) => stop.poi_id === place.id) && `${place.name} ${place.area} ${place.tags} ${place.category}`.toLowerCase().includes(search.toLowerCase())).slice(0, 5)
  const createTrip = async () => { setLoading(true); try { const response = await tripsApi.create({ name: 'A Pune day out', start_location: origin, budget: Number(budgetInput) || 1000 }); const startPlace = places.find((place) => place.name.toLowerCase() === origin.trim().toLowerCase()); if (startPlace) await tripsApi.addStop(response.data.id, startPlace.id); await loadTrip(response.data); onNotice(startPlace ? `${origin} is set as your start. Add the first stop.` : 'Your Pune day is ready. Add a couple of places to get started.') } catch { onNotice('Could not start a trip. Please try again.') } finally { setLoading(false) } }
  const addStop = async (place: Place) => { if (!trip) return; setLoading(true); try { await tripsApi.addStop(trip.id, place.id); await loadTrip(trip); onNotice(`${place.name} added to your day.`) } catch { onNotice('That place could not be added.') } finally { setLoading(false) } }
  const removeStop = async (stop: Stop) => { if (!trip) return; try { await tripsApi.removeStop(trip.id, stop.stop_id); await loadTrip(trip); onNotice(`${stop.poi_name} removed from your day.`) } catch { onNotice('That stop could not be removed.') } }
  const moveStop = async (index: number, direction: -1 | 1) => { if (!trip) return; const next = [...stops]; const target = index + direction; if (target < 0 || target >= next.length) return; [next[index], next[target]] = [next[target], next[index]]; try { await tripsApi.reorder(trip.id, next.map((stop) => stop.stop_id)); await loadTrip(trip) } catch { onNotice('Could not reorder those places.') } }
  const compare = async (from: Stop, to: Stop) => { if (!trip) return; setActiveLeg([from.stop_id, to.stop_id]); try { const response = await tripsApi.options(trip.id, from.stop_id, to.stop_id); setOptions(response.data.options) } catch { setOptions([]); onNotice('Transport choices are unavailable for that leg.') } }
  const chooseMode = async (option: TransportOption) => { if (!trip || !activeLeg) return; setSelectedMode(option.mode); try { await tripsApi.select(trip.id, activeLeg[0], activeLeg[1], { mode: option.mode, option_type: option.option_type }); await loadTrip(trip); onNotice(`${option.mode} saved for this leg.`) } catch { onNotice('Could not save that transport choice.') } }
  const share = async () => { if (!trip) return; try { const response = await tripsApi.share(trip.id); setShareUrl(response.data.share_url); await navigator.clipboard.writeText(response.data.share_url); onNotice('A share link is copied to your clipboard.') } catch { onNotice('Could not create a share link.') } }
  const saveTrip = async () => { if (!trip || trip.is_saved) { onNotice('This day is already in your saved trips.'); return } try { await tripsApi.save(trip.id); setTrip({ ...trip, is_saved: true }); onNotice('Your day is saved for later.') } catch { onNotice('Could not save your trip.') } }
  const exportPdf = async () => { if (!trip) return; try { const response = await tripsApi.pdf(trip.id); const url = URL.createObjectURL(response.data); const anchor = document.createElement('a'); anchor.href = url; anchor.download = `${trip.name.replaceAll(' ', '-')}.pdf`; anchor.click(); URL.revokeObjectURL(url); onNotice('Your itinerary PDF has downloaded.') } catch { onNotice('Could not export the itinerary.') } }

  if (!trip) return <div className="planner-page"><div className="eyebrow">MAKE A LITTLE ROOM FOR THE CITY</div><h1>Your Pune day starts here.</h1><p className="page-subtitle">Choose where you’re starting and what you’d like to spend. We’ll fill in the good bits together.</p><div className="trip-start-card"><div className="trip-start-icon"><Map size={21} /></div><h2>Plan a day out</h2><label className="field-label">Starting from<input value={origin} onChange={(event) => setOrigin(event.target.value)} placeholder="Swargate" /></label><label className="field-label">A comfortable budget<input type="number" min="0" value={budgetInput} onChange={(event) => setBudgetInput(event.target.value)} /></label><button className="button button-dark button-full" disabled={loading} onClick={createTrip}>{loading ? 'Getting things ready…' : 'Start planning'}<ArrowRight size={16} /></button></div><div className="planner-start-note"><Sparkles size={16} /> Your {profile.preferred_transport.toLowerCase()} preference and {profile.interests.slice(0, 2).join(' & ')} interests shape the suggestions you’ll see.</div></div>

  return <div className="planner-page"><div className="page-heading-row planner-heading"><div><div className="eyebrow">A DAY MADE A LITTLE MORE YOURS</div><h1>{trip.name}</h1><p className="page-subtitle">A few favourite places, connected at your own pace.</p></div><div className="planner-actions"><button className="button button-outline" onClick={share}><Share2 size={15} /> Share</button><button className="button button-outline" onClick={exportPdf}><ArrowDown size={15} /> Itinerary</button><button className="button button-dark" onClick={saveTrip}><Bookmark size={15} /> {trip.is_saved ? 'Saved' : 'Save day'}</button></div></div>{shareUrl && <div className="share-link-box"><a href={shareUrl} target="_blank" rel="noreferrer">{shareUrl}</a><button className="icon-button" onClick={() => setShareUrl('')} aria-label="Close"><X size={15} /></button></div>}<div className="route-banner"><div className="route-endpoint"><span className="route-pin origin-pin" /><div><span>STARTING AROUND</span><strong>{trip.start_location}</strong></div></div><div className="route-dotted"><i /><i /><i /><ArrowRight size={15} /></div><div className="route-destination"><MapPin size={16} /><span>{stops.length ? stops[stops.length - 1].poi_name : 'Where the day takes us'}</span></div><button className="route-weather" onClick={() => tripsApi.weather().then((response) => onNotice(`${Math.round(response.data.temperature_c)}° in Pune · ${response.data.description}`)).catch(() => onNotice('Live weather is temporarily unavailable.'))}><CloudSun size={17} /> Pune today</button></div><div className="planner-layout"><div className="planner-main-column"><section className="itinerary-section"><div className="section-label-row"><div><div className="eyebrow">A NICE, EASY ITINERARY</div><h2>Your day, stop by stop</h2></div><span className="stop-total">{stops.length} {stops.length === 1 ? 'place' : 'places'}</span></div><div className="itinerary-list">{!stops.length || stops[0].poi_name.toLowerCase() !== trip.start_location.toLowerCase() ? <div className="start-itinerary-row"><div className="timeline-node start-node"><MapPin size={14} /></div><div className="start-stop-card"><div><span className="eyebrow">START HERE</span><h3>{trip.start_location}</h3></div><span className="depart-time">A good place to begin</span></div></div> : null}{stops.length === 0 && <div className="empty-stops"><span className="empty-stops-icon"><Sparkles size={19} /></span><div><strong>Your day has room for something lovely.</strong><span>Add a place below to start shaping the route.</span></div></div>}{stops.map((stop, index) => <div key={stop.stop_id} className="itinerary-stop-wrap"><div className="itinerary-stop-row"><div className="timeline-node stop-node">{String(index + 1).padStart(2, '0')}</div><div className="itinerary-stop-card"><div className="stop-image-mini"><img src={coverImage(places.find((place) => place.id === stop.poi_id) || { name: stop.poi_name } as Place)} alt="" /></div><div className="stop-info"><span className="stop-area">{stop.area}</span><h3>{stop.poi_name}</h3><span><Clock3 size={12} /> {stop.duration_minutes} min <i /> {stop.entry_cost ? money(stop.entry_cost) : 'No entry fee'}</span></div><button className="icon-button reorder-stop" onClick={() => moveStop(index, -1)} disabled={index === 0} title="Move earlier" aria-label={`Move ${stop.poi_name} earlier`}><ArrowUp size={14} /></button><button className="icon-button reorder-stop" onClick={() => moveStop(index, 1)} disabled={index === stops.length - 1} title="Move later" aria-label={`Move ${stop.poi_name} later`}><ArrowDown size={14} /></button><button className="icon-button remove-stop" onClick={() => removeStop(stop)} title="Remove stop" aria-label={`Remove ${stop.poi_name}`}><Trash2 size={15} /></button></div></div>{index < stops.length - 1 && <button className={`leg-row ${activeLeg?.[0] === stop.stop_id ? 'selected' : ''}`} onClick={() => compare(stop, stops[index + 1])}><span className="leg-line" /><span className="leg-label"><Bus size={14} /> {activeLeg?.[0] === stop.stop_id ? 'Comparing this stretch' : 'Choose a way to get there'}</span><span className="leg-line" /><ArrowRight size={13} /></button>}</div>)}</div></section><section className="add-place-section"><div className="section-label-row"><div><div className="eyebrow">THE CITY’S OPEN DOOR</div><h2>Maybe stop by…</h2></div><span className="local-pick-label"><Sparkles size={13} /> PICKED FOR YOU</span></div><label className="search-box planner-search"><Search size={16} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Find a place, neighbourhood or feeling" /></label><div className="suggestion-list">{candidates.slice(0, 4).map((place) => <button key={place.id} className="suggestion-row" onClick={() => addStop(place)} disabled={loading}><img src={coverImage(place)} alt="" /><div className="suggestion-info"><strong>{place.name}</strong><span>{place.category} <i /> {place.area} <i /> {place.entry_fee ? money(place.entry_fee) : 'Free'}</span></div><span className="suggestion-rating"><Star size={13} fill="currentColor" /> {place.rating.toFixed(1)}</span><span className="suggestion-add"><Plus size={15} /></span></button>)}</div><Link to="/explore" className="browse-more-link">Browse all the good places <ArrowRight size={14} /></Link></section></div><aside className="planner-aside"><section className="budget-card"><div className="budget-top"><span className="mini-icon budget-icon"><Wallet size={17} /></span><span className="eyebrow">YOUR DAY, YOUR BUDGET</span></div><h3>{budget ? `${money(Math.max(0, budget.remaining_budget))}` : money(Number(budgetInput))}<small> to play with</small></h3><div className="budget-progress"><span style={{ width: `${Math.min(100, budget?.budget_used_percent || 0)}%` }} /></div><div className="budget-progress-label"><span>{budget ? money(budget.estimated_total) : '₹0'} spent so far</span><span>{money(budget?.budget || trip.budget)} total</span></div><div className="budget-line-items"><div><span>Getting around</span><span>{money(budget?.total_transport_cost || 0)}</span></div><div><span>Entry & experiences</span><span>{money(budget?.total_entry_cost || 0)}</span></div><div><span>Something lovely to eat</span><span>{money(budget?.total_food_cost || 0)}</span></div></div>{budget?.suggestion && <div className="budget-hint"><Sparkles size={14} />{budget.suggestion}</div>}</section><section className="transport-card"><div className="section-label-row"><div><div className="eyebrow">GETTING FROM A TO B</div><h3>{activeLeg ? 'A few ways to get there' : 'Your travel options'}</h3></div><ArrowUpRight size={16} /></div>{activeLeg && <p className="transport-leg-name">{stops.find((stop) => stop.stop_id === activeLeg[0])?.poi_name} <ArrowRight size={12} /> {stops.find((stop) => stop.stop_id === activeLeg[1])?.poi_name}</p>}{options.length ? <div className="transport-options">{options.map((option) => <button key={`${option.mode}-${option.option_type}`} className={`transport-option ${selectedMode === option.mode ? 'chosen' : ''}`} onClick={() => chooseMode(option)}><span className="transport-mode-icon">{option.mode.toLowerCase().includes('metro') ? <TrainFront size={16} /> : option.mode === 'Walk' ? <MapPin size={16} /> : <Bus size={16} />}</span><span className="transport-mode-name"><strong>{option.mode}</strong><small>{option.option_type}</small></span><span className="transport-mode-time">{option.duration_minutes} min<small>{option.walking_minutes} min walk</small></span><strong className="transport-fare">{money(option.fare)}</strong></button>)}</div> : <div className="transport-empty"><span className="transport-empty-icon"><TrainFront size={17} /></span><span>When your day has two places, compare ways to get between them here.</span></div>}<div className="estimate-caption"><CircleHelp size={13} /> Fare and timing are estimates, not live quotes.</div></section><div className="planner-aside-footer"><ShieldCheck size={15} /><span>Your preferences are saved to your profile.</span></div></aside></div></div>
}

function Saved({ onNotice }: { onNotice: (message: string) => void }) {
  const [trips, setTrips] = useState<Trip[]>([])
  const [stops, setStops] = useState<Record<number, Stop[]>>({})
  useEffect(() => { tripsApi.list().then(async (response) => { const saved = response.data.filter((trip) => trip.is_saved); setTrips(saved); const entries = await Promise.all(saved.map(async (trip) => [trip.id, (await tripsApi.stops(trip.id)).data] as const)); setStops(Object.fromEntries(entries)) }).catch(() => onNotice('Could not load saved trips.')) }, [onNotice])
  return <div className="saved-page"><div className="page-heading-row"><div><div className="eyebrow">A FEW DAYS WORTH REMEMBERING</div><h1>Saved for another day.</h1><p className="page-subtitle">Your little Pune plans, all in one place.</p></div><Link className="button button-dark" to="/planner">Plan a new day <ArrowRight size={15} /></Link></div>{trips.length ? <div className="saved-trip-grid">{trips.map((trip) => <article className="saved-trip-card" key={trip.id}><div className="saved-trip-cover"><img src={coverImage({ name: stops[trip.id]?.[0]?.poi_name || 'Pune' } as Place)} alt="" /><span className="saved-trip-badge"><Bookmark size={12} /> SAVED DAY</span><span className="saved-trip-price">{money(trip.budget)} budget</span></div><div className="saved-trip-body"><span className="eyebrow">STARTING FROM {trip.start_location.toUpperCase()}</span><h2>{trip.name}</h2><div className="saved-trip-meta"><span><MapPin size={13} /> {stops[trip.id]?.length || 0} places</span><span><Wallet size={13} /> {money(trip.total_entry_cost + trip.total_transport_cost)} so far</span></div><div className="saved-trip-places">{(stops[trip.id] || []).slice(0, 3).map((stop) => <span key={stop.stop_id}>{stop.poi_name}</span>)}</div><Link to="/planner" className="saved-trip-link">Pick this day back up <ArrowRight size={14} /></Link></div></article>)}</div> : <div className="saved-empty"><span className="empty-stops-icon"><Bookmark size={20} /></span><h2>Good days start as little lists.</h2><p>Put together a few places you love, then save them for whenever the city calls.</p><Link className="button button-dark" to="/planner">Plan your first day <ArrowRight size={15} /></Link></div>}</div>
}

function Friends({ onNotice }: { onNotice: (message: string) => void }) {
  const [suggestions, setSuggestions] = useState<{ user_id: number; name: string; email: string; interest_similarity: number }[]>([])
  const [requests, setRequests] = useState<{ friendship_id: number; user_id: number; name: string; email: string }[]>([])
  const [friends, setFriends] = useState<{ user_id: number; name: string; email: string; interests: string[] }[]>([])
  const [loading, setLoading] = useState(true)
  const refresh = useCallback(async () => {
    const [people, pending, connected] = await Promise.all([friendsApi.suggestions(), friendsApi.requests(), friendsApi.friends()])
    setSuggestions(people.data); setRequests(pending.data); setFriends(connected.data)
  }, [])
  useEffect(() => { refresh().catch(() => onNotice('Travel friends are unavailable right now.')).finally(() => setLoading(false)) }, [refresh, onNotice])
  const send = async (id: number) => { try { await friendsApi.sendRequest(id); await refresh(); onNotice('Friend request sent.') } catch (error) { const detail = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail; onNotice(detail || 'Could not send the request.') } }
  const accept = async (id: number) => { try { await friendsApi.acceptRequest(id); await refresh(); onNotice('You’re connected now.') } catch { onNotice('Could not accept the request.') } }
  const interestsOf = (items: string[]) => items.length ? items.map(pretty).join(' · ') : 'Still finding their Pune favourites'
  return <div className="friends-page"><div className="page-heading-row"><div><div className="eyebrow">GOOD DAYS GET BETTER SHARED</div><h1>Pune, in good company.</h1><p className="page-subtitle">Meet people who love the same corners of the city.</p></div><span className="place-count"><UsersRound size={15} /> {friends.length} travel friends</span></div>{requests.length > 0 && <section className="friends-section"><div className="section-label-row"><div><div className="eyebrow">A HELLO FROM SOMEONE</div><h2>Friend requests</h2></div><span className="stop-total">{requests.length} waiting</span></div><div className="friend-grid">{requests.map((person) => <article className="friend-card" key={person.friendship_id}><div className="avatar avatar-large">{initials(person.name)}</div><div className="friend-details"><strong>{person.name}</strong><span>{person.email}</span></div><button className="button button-dark" onClick={() => accept(person.friendship_id)}><Check size={14} /> Accept</button></article>)}</div></section>}{friends.length > 0 && <section className="friends-section"><div className="section-label-row"><div><div className="eyebrow">YOUR PEOPLE</div><h2>Friends around town</h2></div></div><div className="friend-grid">{friends.map((person) => <article className="friend-card friend-connected" key={person.user_id}><div className="avatar avatar-large">{initials(person.name)}</div><div className="friend-details"><strong>{person.name}</strong><span>{interestsOf(person.interests)}</span></div><span className="connected-mark"><Check size={13} /> Connected</span></article>)}</div></section>}<section className="friends-section"><div className="section-label-row"><div><div className="eyebrow">SIMILAR CURIOSITY, MAYBE?</div><h2>People to explore with</h2></div><span className="local-pick-label"><Sparkles size={13} /> MATCHED ON INTERESTS</span></div>{loading ? <div className="empty-state"><UsersRound className="spin-icon" size={22} /> Finding your kind of people…</div> : suggestions.length ? <div className="friend-grid">{suggestions.map((person) => <article className="friend-card" key={person.user_id}><div className="avatar avatar-large">{initials(person.name)}</div><div className="friend-details"><strong>{person.name}</strong><span>{person.email}</span><span className="match-note"><Sparkles size={11} /> {Math.round(person.interest_similarity * 100)}% interest match</span></div><button className="button button-outline" onClick={() => send(person.user_id)}>Say hello <ArrowRight size={14} /></button></article>)}</div> : <div className="empty-state friend-empty"><UsersRound size={24} /><h3>Your travel circle is just getting started.</h3><p>As more Pune explorers join RouteWise, we’ll introduce you to people with similar interests.</p></div>}</section><div className="friends-note"><ShieldCheck size={15} /> Your profile interests help us suggest people. Your private trip details stay yours.</div></div>
}

function ProfilePage({ profile, onSave, onNotice }: { profile: Profile; onSave: (data: Omit<Profile, 'id' | 'name' | 'email'>) => Promise<void>; onNotice: (message: string) => void }) {
  const [interestsValue, setInterestsValue] = useState(profile.interests)
  const [budget, setBudget] = useState(profile.budget_style)
  const [transport, setTransport] = useState(profile.preferred_transport)
  const [area, setArea] = useState(profile.home_area)
  const [sharing, setSharing] = useState(profile.share_checkins)
  const [busy, setBusy] = useState(false)
  useEffect(() => { setInterestsValue(profile.interests); setBudget(profile.budget_style); setTransport(profile.preferred_transport); setArea(profile.home_area); setSharing(profile.share_checkins) }, [profile])
  return <div className="profile-page"><div className="eyebrow">YOUR KIND OF PUNE</div><h1>Your preferences.</h1><p className="page-subtitle">A few helpful notes to make the city feel a little more like yours.</p><div className="profile-card"><div className="profile-identity"><div className="avatar avatar-large">{initials(profile.name)}</div><div><span className="eyebrow">TRAVELLER PROFILE</span><h2>{profile.name}</h2><p>{profile.email}</p></div></div><div className="profile-divider" /><div className="profile-setting"><div><h3>Things I love</h3><p>Places and experiences we should look out for.</p></div><div className="profile-interests">{interests.map((item) => <button type="button" key={item} onClick={() => setInterestsValue((current) => current.includes(item) ? current.filter((value) => value !== item) : [...current, item])} className={`interest-chip compact-chip ${interestsValue.includes(item) ? 'selected' : ''}`}>{pretty(item)}{interestsValue.includes(item) && <Check size={13} />}</button>)}</div></div><div className="profile-setting"><div><h3>My starting neighbourhood</h3><p>Your usual place to set off from.</p></div><select value={area} onChange={(event) => setArea(event.target.value)}><option>Pune Station</option><option>Swargate</option><option>Shivajinagar</option><option>Kothrud</option><option>Hinjawadi</option><option>Koregaon Park</option><option>Viman Nagar</option></select></div><div className="profile-setting"><div><h3>My way around town</h3><p>We’ll keep this in mind when planning.</p></div><select value={transport} onChange={(event) => setTransport(event.target.value as Profile['preferred_transport'])}><option>Bus</option><option>Metro</option><option>Auto</option><option>Walk</option></select></div><div className="profile-setting"><div><h3>My spending style</h3><p>How we should think about the day’s budget.</p></div><select value={budget} onChange={(event) => setBudget(event.target.value as Profile['budget_style'])}><option value="budget">Keep it easy</option><option value="mid">A little of both</option><option value="comfort">Here for the experience</option></select></div><div className="profile-setting"><div><h3>Share my check-ins</h3><p>Let friends see places you’ve visited.</p></div><button type="button" className={`toggle ${sharing ? 'on' : ''}`} onClick={() => setSharing(!sharing)} aria-label="Toggle check-in sharing"><span /></button></div><div className="profile-actions"><span><ShieldCheck size={15} /> Your details stay private.</span><button className="button button-dark" disabled={busy || !interestsValue.length} onClick={async () => { setBusy(true); try { await onSave({ interests: interestsValue, budget_style: budget, preferred_transport: transport, home_area: area, share_checkins: sharing }); onNotice('Your preferences are updated.') } catch { onNotice('Could not save preferences.') } finally { setBusy(false) } }}>{busy ? 'Saving…' : 'Save my preferences'}<ArrowRight size={15} /></button></div></div></div>
}

export default App
