import axios from 'axios'

export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000' })
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('routewise_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
api.interceptors.response.use((response) => response, (error) => {
  if (error.response?.status === 401 && localStorage.getItem('routewise_token')) {
    localStorage.removeItem('routewise_token')
    window.dispatchEvent(new Event('routewise:logout'))
  }
  return Promise.reject(error)
})

export type User = { id: number; name: string; email: string }
export type Profile = User & { interests: string[]; budget_style: 'budget' | 'mid' | 'comfort'; preferred_transport: 'Bus' | 'Metro' | 'Auto' | 'Walk'; home_area: string; share_checkins: boolean }
export type Place = { id: number; name: string; description: string; category: string; latitude: number; longitude: number; address: string; area: string; rating: number; popularity: number; entry_fee: number; recommended_duration: number; tags: string; near_metro: boolean }
export type Recommendation = { poi_id: number; name: string; category: string; area: string; description: string; rating: number; popularity: number; entry_fee: number; recommended_duration: number; tags: string; near_metro: boolean; recommendation_score: number; interest_match: number }
export type Trip = { id: number; name: string; start_location: string; budget: number; total_transport_cost: number; total_entry_cost: number; total_food_cost: number; buffer_cost: number; is_saved: boolean }
export type Stop = { stop_id: number; poi_id: number; poi_name: string; area: string; sequence: number; duration_minutes: number; locked: boolean; entry_cost: number }
export type Budget = { budget: number; total_transport_cost: number; total_entry_cost: number; total_food_cost: number; buffer_cost: number; estimated_total: number; remaining_budget: number; budget_used_percent: number; budget_status: string; suggestion: string | null }
export type TransportOption = { mode: string; option_type: string; duration_minutes: number; walking_minutes: number; distance_km: number; fare: number; boarding_stop?: string; alighting_stop?: string; intermediate_stops: string[]; reliability_score: number }

export const authApi = {
  register: (data: { name: string; email: string; password: string }) => api.post<User>('/auth/register', data),
  login: (data: { email: string; password: string }) => api.post<{ access_token: string; user: User }>('/auth/login', data),
  me: () => api.get<User>('/auth/me'),
}
export const profileApi = {
  get: () => api.get<Profile>('/me/profile'),
  save: (data: Omit<Profile, 'id' | 'name' | 'email'>) => api.put<Profile>('/me/profile', data),
}
export const placesApi = {
  list: (params?: Record<string, string>) => api.get<Place[]>('/pois', { params }),
  recommendations: () => api.get<Recommendation[]>('/recommendations'),
}
export const tripsApi = {
  list: () => api.get<Trip[]>('/trips'),
  create: (data: { name: string; start_location: string; budget: number }) => api.post<Trip>('/trips', data),
  stops: (id: number) => api.get<Stop[]>(`/trips/${id}/stops`),
  addStop: (id: number, poi_id: number) => api.post(`/trips/${id}/stops`, { poi_id }),
  removeStop: (id: number, stopId: number) => api.delete(`/trips/${id}/stops/${stopId}`),
  budget: (id: number) => api.get<Budget>(`/trips/${id}/budget`),
  options: (id: number, from: number, to: number) => api.get<{ options: TransportOption[] }>(`/trips/${id}/stops/${from}/${to}/transport`),
  select: (id: number, from: number, to: number, data: Pick<TransportOption, 'mode' | 'option_type'>) => api.post(`/trips/${id}/stops/${from}/${to}/transport/select`, data),
  save: (id: number) => api.patch(`/trips/${id}/save`),
  reorder: (id: number, stop_ids: number[]) => api.put(`/trips/${id}/reorder`, { stop_ids }),
  share: (id: number) => api.post<{ share_url: string }>(`/trips/${id}/share`),
  pdf: (id: number) => api.get(`/trips/${id}/export/pdf`, { responseType: 'blob' }),
  weather: () => api.get('/weather/pune'),
}
export const friendsApi = {
  suggestions: () => api.get<{ user_id: number; name: string; email: string; interest_similarity: number }[]>('/friends/suggestions'),
  requests: () => api.get<{ friendship_id: number; user_id: number; name: string; email: string }[]>('/friends/requests'),
  friends: () => api.get<{ user_id: number; name: string; email: string; interests: string[] }[]>('/friends'),
  sendRequest: (user_id: number) => api.post('/friends/request', { user_id }),
  acceptRequest: (id: number) => api.post(`/friends/accept/${id}`),
}
