import axios from 'axios';

const api = axios.create({
  baseURL: '/api'
});

export const getMetadata = () => api.get('/meta').then(res => res.data);
export const getStints = () => api.get('/stints').then(res => res.data);
export const getOverview = (stintId = 'stint_1') => api.get(`/overview?stintId=${stintId}`).then(res => res.data);
export const getDegradation = (stintId = 'stint_1') => api.get(`/degradation?stintId=${stintId}`).then(res => res.data);
export const getLaps = (stintId = null) => api.get(stintId ? `/laps?stintId=${stintId}` : '/laps').then(res => res.data);
export const getLapForensics = (lapNumber = 6) => api.get(`/lap-forensics?lapNumber=${lapNumber}`).then(res => res.data);
export const simulateStrategy = (stintId = 'stint_1', pitInNLaps = 5) => api.post('/strategy', { stint_id: stintId, pit_in_n_laps: pitInNLaps }).then(res => res.data);
export const askRaceEngineer = (query, stintId = 'stint_1', lapNumber = null) => api.post('/ask', { query, stint_id: stintId, lap_number: lapNumber }).then(res => res.data);
export const getAskExamples = () => api.get('/ask/examples').then(res => res.data);
