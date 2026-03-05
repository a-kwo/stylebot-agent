'use client';

import { useState, useEffect, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import {
  submitOnboarding,
  getOnboardingQuestions,
  submitStyleQuiz,
} from '@/lib/api';

interface QuizOption {
  id: string;
  label: string;
  image_url: string;
  style_tags: string[];
}

interface QuizQuestion {
  category: string;
  prompt: string;
  options: QuizOption[];
}

export default function OnboardingPage() {
  const router = useRouter();
  const { authenticated, onboarded, refresh } = useAuth();
  const [phase, setPhase] = useState<'demographics' | 'quiz'>('demographics');

  // Demographics
  const [gender, setGender] = useState('');
  const [age, setAge] = useState('');
  const [climate, setClimate] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  // Quiz
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [currentQ, setCurrentQ] = useState(0);
  const [selectedOption, setSelectedOption] = useState<QuizOption | null>(null);
  const [answers, setAnswers] = useState<Array<{
    category: string;
    choice: string;
    style_tags: string[];
  }>>([]);

  useEffect(() => {
    if (!authenticated) {
      router.replace('/');
    } else if (onboarded) {
      router.replace('/chat');
    }
  }, [authenticated, onboarded, router]);

  if (!authenticated || onboarded) return null;

  const handleDemographics = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setSaving(true);
    try {
      await submitOnboarding(gender, parseInt(age), climate);
      // Load quiz questions
      const qs = await getOnboardingQuestions();
      setQuestions(qs);
      setPhase('quiz');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleNext = async () => {
    if (!selectedOption) return;

    const q = questions[currentQ];
    const newAnswers = [
      ...answers,
      {
        category: q.category,
        choice: selectedOption.id,
        style_tags: selectedOption.style_tags,
      },
    ];
    setAnswers(newAnswers);
    setSelectedOption(null);

    if (currentQ + 1 < questions.length) {
      setCurrentQ(currentQ + 1);
    } else {
      // Submit all answers
      setSaving(true);
      try {
        await submitStyleQuiz(newAnswers);
      } catch {}
      refresh();
      router.replace('/chat');
    }
  };

  if (phase === 'demographics') {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="w-full max-w-md">
          <h1 className="text-2xl font-bold text-center mb-2">
            Let&apos;s get to know you
          </h1>
          <p className="text-center text-muted mb-8">
            A few quick questions to personalize your experience
          </p>

          <form onSubmit={handleDemographics} className="card p-6 flex flex-col gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Gender</label>
              <select
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="input-field"
                required
              >
                <option value="">Select...</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="non-binary">Non-binary</option>
                <option value="prefer-not-to-say">Prefer not to say</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Age</label>
              <input
                type="number"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                className="input-field"
                required
                min={13}
                max={120}
                placeholder="e.g. 22"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Climate</label>
              <select
                value={climate}
                onChange={(e) => setClimate(e.target.value)}
                className="input-field"
                required
              >
                <option value="">Select...</option>
                <option value="hot">Hot / Tropical</option>
                <option value="warm">Warm / Mild</option>
                <option value="temperate">Temperate / 4 seasons</option>
                <option value="cold">Cold / Winter-heavy</option>
              </select>
            </div>

            {error && <p className="text-red-500 text-sm">{error}</p>}

            <button type="submit" disabled={saving} className="btn-primary">
              {saving ? 'Saving...' : 'Continue'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // Quiz phase
  const q = questions[currentQ];
  if (!q) return null;

  return (
    <div className="min-h-screen flex flex-col items-center px-4 py-8">
      <div className="w-full max-w-2xl">
        <div className="text-sm text-muted mb-2">
          Question {currentQ + 1} of {questions.length}
        </div>
        <div className="w-full bg-zinc-200 dark:bg-zinc-700 rounded-full h-1.5 mb-6">
          <div
            className="bg-ink dark:bg-cream h-1.5 rounded-full transition-all"
            style={{ width: `${((currentQ + 1) / questions.length) * 100}%` }}
          />
        </div>

        <h2 className="text-xl font-semibold mb-6">{q.prompt}</h2>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-8">
          {q.options.map((opt) => (
            <button
              key={opt.id}
              onClick={() => setSelectedOption(opt)}
              className={`card p-2 transition-all hover:scale-[1.02] ${
                selectedOption?.id === opt.id
                  ? 'ring-2 ring-ink dark:ring-cream scale-[1.02]'
                  : ''
              }`}
            >
              <img
                src={opt.image_url}
                alt={opt.label}
                className="w-full aspect-square object-cover rounded-xl mb-2"
                loading="lazy"
              />
              <div className="text-sm font-medium text-center">{opt.label}</div>
            </button>
          ))}
        </div>

        <button
          onClick={handleNext}
          disabled={!selectedOption || saving}
          className="btn-primary w-full"
        >
          {saving
            ? 'Saving...'
            : currentQ + 1 < questions.length
              ? 'Next'
              : 'Finish'}
        </button>
      </div>
    </div>
  );
}
