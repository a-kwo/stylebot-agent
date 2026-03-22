const API_BASE = '/api';

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('stylebot_token');
}

export function setToken(token: string) {
  localStorage.setItem('stylebot_token', token);
}

export function clearToken() {
  localStorage.removeItem('stylebot_token');
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

export async function apiFetch(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (options.body && typeof options.body === 'string') {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    clearToken();
    window.location.replace('/login');
    throw new Error('Session expired');
  }

  return res;
}

// Auth endpoints
export async function login(username: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Invalid credentials');
  }
  const data = await res.json();
  setToken(data.access_token);
  return data;
}

export async function register(username: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Registration failed');
  }
  const data = await res.json();
  setToken(data.access_token);
  return data;
}

export async function getOnboardingStatus(): Promise<boolean> {
  const res = await apiFetch('/profile/onboarding-status');
  const data = await res.json();
  return !!data.onboarded;
}

export async function submitOnboarding(gender: string, age: number, climate?: string) {
  const res = await apiFetch('/profile/onboard', {
    method: 'POST',
    body: JSON.stringify({ gender, age, climate: climate || '' }),
  });
  if (!res.ok) throw new Error('Failed to save');
  return res.json();
}

export async function getOnboardingQuestions() {
  const res = await apiFetch('/quiz/onboarding');
  return res.json();
}

export async function submitStyleQuiz(answers: Array<{
  category: string;
  choice: string;
  style_tags: string[];
}>) {
  const res = await apiFetch('/profile/style-quiz', {
    method: 'POST',
    body: JSON.stringify({ answers }),
  });
  if (!res.ok) throw new Error('Failed to save quiz');
  return res.json();
}

export async function submitQuizAnswer(answer: {
  category: string;
  choice: string;
  style_tags: string[];
}) {
  return apiFetch('/profile/quiz-answer', {
    method: 'POST',
    body: JSON.stringify(answer),
  });
}

// V2 Quiz
export async function getQuizV2() {
  const res = await apiFetch('/quiz/v2');
  return res.json();
}

export async function submitStyleQuizV2(
  answers: Array<{
    question_id: string;
    option_id: string;
    vector_scores: Record<string, number>;
  }>,
  selected_occasions: string[]
) {
  const res = await apiFetch('/profile/style-quiz-v2', {
    method: 'POST',
    body: JSON.stringify({ answers, selected_occasions }),
  });
  if (!res.ok) throw new Error('Failed to save quiz');
  return res.json();
}

export async function getConversations() {
  const res = await apiFetch('/conversations');
  return res.json();
}

export async function sendChat(message: string) {
  const res = await apiFetch('/chat', {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Chat failed');
  }
  return res.json();
}

export async function submitFeedback(
  productTitle: string,
  feedback: 'like' | 'dislike',
  meta?: { price?: string; seller?: string; color?: string; image_url?: string; search_query?: string },
) {
  return apiFetch('/feedback', {
    method: 'POST',
    body: JSON.stringify({ product_title: productTitle, feedback, ...meta }),
  });
}

// SSE streaming chat
export function streamChat(
  message: string,
  callbacks: {
    onToken?: (text: string) => void;
    onProducts?: (items: any[]) => void;
    onQuiz?: (quiz: any) => void;
    onToolStatus?: (tool: string, status: string) => void;
    onError?: (message: string) => void;
    onDone?: () => void;
  }
): AbortController {
  const controller = new AbortController();
  const token = getToken();
  const url = `${API_BASE}/chat/stream?message=${encodeURIComponent(message)}`;

  fetch(url, {
    headers: { Authorization: `Bearer ${token || ''}` },
    signal: controller.signal,
  }).then(async (res) => {
    if (!res.ok) {
      if (res.status === 401) {
        clearToken();
        window.location.replace('/login');
        return;
      }
      callbacks.onError?.(`Server error ${res.status}`);
      callbacks.onDone?.();
      return;
    }

    const reader = res.body?.getReader();
    if (!reader) return;

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      let eventType = '';
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          eventType = line.slice(7);
        } else if (line.startsWith('data: ') && eventType) {
          try {
            const data = JSON.parse(line.slice(6));
            switch (eventType) {
              case 'token':
                callbacks.onToken?.(data.text);
                break;
              case 'products':
                callbacks.onProducts?.(data.items);
                break;
              case 'quiz':
                callbacks.onQuiz?.(data);
                break;
              case 'tool_status':
                callbacks.onToolStatus?.(data.tool, data.status);
                break;
              case 'error':
                callbacks.onError?.(data.message);
                break;
              case 'done':
                callbacks.onDone?.();
                break;
            }
          } catch {}
          eventType = '';
        }
      }
    }

    callbacks.onDone?.();
  }).catch((err) => {
    if (err.name !== 'AbortError') {
      console.error('[StreamChat] Error:', err);
      callbacks.onError?.(err.message || 'Network error');
      callbacks.onDone?.();
    }
  });

  return controller;
}
