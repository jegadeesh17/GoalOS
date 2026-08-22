import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface LifeSummary {
  birth_date: string;
  target_age: number;
  today: string;
  age_years: number;
  total_weeks: number;
  weeks_lived: number;
  weeks_remaining: number;
  percentage_lived: number;
  target_date: string;
}

export interface WeekBlock {
  year: number;
  week_of_year: number;
  global_week: number;
  status: 'past' | 'current' | 'future';
}

export interface YearGridRow {
  age: number;
  weeks: WeekBlock[];
}

export interface TaskItem {
  id?: string;
  text: string;
  priority: number;
  completed: boolean;
  goal_id?: number | null;
  milestone_id?: number | null;
}

export interface DailyLog {
  id?: number;
  date: string;
  morning_completed: boolean;
  sleep_hours?: number | null;
  sleep_quality?: number | null;
  energy_level?: number | null;
  mood_morning?: number | null;
  expected_focus?: number | null;
  available_hours?: number | null;
  calendar_constraints?: string | null;
  free_write?: string | null;
  intention?: string | null;
  anxiety?: string | null;
  anticipation?: string | null;
  top_priority?: string | null;
  supporting_task_1?: string | null;
  supporting_task_2?: string | null;
  gratitude?: string | null;
  time_blocks?: string | null;
  planned_tasks?: string | null;
  evening_completed: boolean;
  journal_entry?: string | null;
  tasks_completed?: string | null;
  task_completion_rate?: number | null;
  deep_work_hours?: number | null;
  workout_completed?: boolean | null;
  workout_notes?: string | null;
  biggest_distraction?: string | null;
  mood_evening?: number | null;
  one_win?: string | null;
  one_lesson?: string | null;
  takeaway?: string | null;
  morning_ai_output?: string | null;
  evening_ai_output?: string | null;
}

export interface Milestone {
  id: number;
  goal_id: number;
  title: string;
  success_criteria?: string | null;
  deadline?: string | null;
  progress: number;
  status: string;
}

export interface Goal {
  id: number;
  title: string;
  description?: string | null;
  category: string;
  horizon: string;
  deadline?: string | null;
  priority: number;
  progress: number;
  status: string;
  reason?: string | null;
  success_criteria?: string | null;
  milestones?: Milestone[];
}

export interface Memory {
  id: number;
  text: string;
  memory_type: string;
  importance: number;
  source_date?: string | null;
  goal_id?: number | null;
  access_count?: number;
}

export interface UserSettings {
  id?: number;
  name?: string;
  birth_date?: string;
  target_age?: number;
  life_vision?: string;
  one_year_vision?: string;
  five_year_vision?: string;
  remote_ai_consent?: boolean;
  openrouter_configured?: boolean;
  environment?: string;
}

export interface AnalyticsDashboardData {
  total_logs: number;
  avg_sleep_hours: number;
  avg_deep_work_hours: number;
  avg_morning_mood: number;
  patterns: any[];
  recent_scores: any[];
}

export const goalOSApi = {
  // Calendar
  getCalendarSummary: async (): Promise<LifeSummary> => {
    const res = await api.get<LifeSummary>('/calendar/summary');
    return res.data;
  },
  getCalendarGrid: async (): Promise<YearGridRow[]> => {
    const res = await api.get<YearGridRow[]>('/calendar/grid');
    return res.data;
  },

  // Journal
  getTodayJournal: async (): Promise<DailyLog> => {
    const res = await api.get<DailyLog>('/journal/today');
    return res.data;
  },
  getJournalByDate: async (dateStr: string): Promise<DailyLog> => {
    const res = await api.get<DailyLog>(`/journal/date/${dateStr}`);
    return res.data;
  },
  upsertJournal: async (payload: Partial<DailyLog> & { date: string }): Promise<DailyLog> => {
    const res = await api.post<DailyLog>('/journal/upsert', payload);
    return res.data;
  },
  getJournalHistory: async (limit = 30): Promise<DailyLog[]> => {
    const res = await api.get<DailyLog[]>(`/journal/history?limit=${limit}`);
    return res.data;
  },

  // Goals
  getGoals: async (params?: { status?: string; category?: string; horizon?: string }): Promise<Goal[]> => {
    const res = await api.get<Goal[]>('/goals', { params });
    return res.data;
  },
  getGoalsHorizons: async (): Promise<Record<string, Goal[]>> => {
    const res = await api.get<Record<string, Goal[]>>('/goals/horizons');
    return res.data;
  },
  createGoal: async (goal: Partial<Goal>): Promise<Goal> => {
    const res = await api.post<Goal>('/goals', goal);
    return res.data;
  },
  updateGoal: async (id: number, goal: Partial<Goal>): Promise<Goal> => {
    const res = await api.put<Goal>(`/goals/${id}`, goal);
    return res.data;
  },
  deleteGoal: async (id: number): Promise<{ success: boolean }> => {
    const res = await api.delete<{ success: boolean }>(`/goals/${id}`);
    return res.data;
  },
  createMilestone: async (goalId: number, milestone: Partial<Milestone>): Promise<Milestone> => {
    const res = await api.post<Milestone>(`/goals/${goalId}/milestones`, milestone);
    return res.data;
  },
  updateMilestone: async (id: number, milestone: Partial<Milestone>): Promise<Milestone> => {
    const res = await api.put<Milestone>(`/milestones/${id}`, milestone);
    return res.data;
  },
  deleteMilestone: async (id: number): Promise<{ success: boolean }> => {
    const res = await api.delete<{ success: boolean }>(`/milestones/${id}`);
    return res.data;
  },

  // AI Coaching
  morningCoach: async (payload: {
    target_date?: string;
    gratitude?: string;
    plans_text?: string;
    tasks: TaskItem[];
    sleep_hours?: number;
    sleep_quality?: number;
    mood_morning?: number;
    energy_level?: number;
    intention?: string;
    top_priority?: string;
  }): Promise<any> => {
    const res = await api.post('/coach/morning', payload);
    return res.data;
  },
  eveningCoach: async (payload: {
    target_date?: string;
    journal_entry?: string;
    deep_work_hours?: number;
    mood_evening?: number;
    one_win?: string;
    one_lesson?: string;
    takeaway?: string;
    biggest_distraction?: string;
  }): Promise<any> => {
    const res = await api.post('/coach/evening', payload);
    return res.data;
  },
  weeklyCoach: async (weekStartDate?: string): Promise<any> => {
    const res = await api.post('/coach/weekly', { week_start_date: weekStartDate });
    return res.data;
  },
  futureSelfCoach: async (dateStr?: string): Promise<any> => {
    const res = await api.post('/coach/future-self', { date: dateStr });
    return res.data;
  },
  goalAlignmentCoach: async (goalId: number): Promise<any> => {
    const res = await api.post('/coach/goal-alignment', { goal_id: goalId });
    return res.data;
  },

  // Memories
  searchMemories: async (q: string, limit = 10): Promise<any[]> => {
    const res = await api.get<any[]>(`/memories/search?q=${encodeURIComponent(q)}&limit=${limit}`);
    return res.data;
  },
  listMemories: async (limit = 50, memoryType?: string): Promise<Memory[]> => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (memoryType) params.append('memory_type', memoryType);
    const res = await api.get<Memory[]>(`/memories?${params.toString()}`);
    return res.data;
  },
  createMemory: async (payload: Partial<Memory>): Promise<Memory> => {
    const res = await api.post<Memory>('/memories', payload);
    return res.data;
  },
  deleteMemory: async (id: number): Promise<{ success: boolean }> => {
    const res = await api.delete<{ success: boolean }>(`/memories/${id}`);
    return res.data;
  },

  // Analytics
  getAnalyticsDashboard: async (): Promise<AnalyticsDashboardData> => {
    const res = await api.get<AnalyticsDashboardData>('/analytics/dashboard');
    return res.data;
  },
  getScores: async (limit = 30): Promise<any[]> => {
    const res = await api.get<any[]>(`/analytics/scores?limit=${limit}`);
    return res.data;
  },

  // Settings
  getSettings: async (): Promise<UserSettings> => {
    const res = await api.get<UserSettings>('/settings');
    return res.data;
  },
  updateSettings: async (settings: Partial<UserSettings>): Promise<UserSettings> => {
    const res = await api.post<UserSettings>('/settings', settings);
    return res.data;
  },
  exportData: async (): Promise<any> => {
    const res = await api.get('/export');
    return res.data;
  },
  factoryReset: async (): Promise<{ success: boolean; backup_created: string }> => {
    const res = await api.post('/export/reset', { confirmation: 'RESET' });
    return res.data;
  },
};
