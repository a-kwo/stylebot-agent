'use client';

import { useState, useEffect, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import {
  submitOnboarding,
  getOnboardingQuestions,
  submitStyleQuiz,
} from '@/lib/api';
import { motion, AnimatePresence } from 'framer-motion';
import { Check } from 'lucide-react';

interface QuizOption {
  id: string;
  label: string;
  image_url: string;
  style_tags: string[];
  next: string | null;
}

interface QuizNode {
  prompt: string;
  options: QuizOption[];
}

interface QuizTree {
  start: string;
  nodes: Record<string, QuizNode>;
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
  const [quizTree, setQuizTree] = useState<QuizTree | null>(null);
  const [currentNodeId, setCurrentNodeId] = useState<string | null>(null);
  const [questionNumber, setQuestionNumber] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [selectedOption, setSelectedOption] = useState<QuizOption | null>(null);
  const [answers, setAnswers] = useState<Array<{
    category: string;
    choice: string;
    style_tags: string[];
  }>>([]);

  useEffect(() => {
    if (!authenticated) {
      router.replace('/login');
    } else if (onboarded) {
      router.replace('/chat');
    }
  }, [authenticated, onboarded, router]);

  useEffect(() => {
    if (quizTree) {
      setTotalQuestions(Object.keys(quizTree.nodes).length);
    }
  }, [quizTree]);

  if (!authenticated || onboarded) return null;

  const handleDemographics = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setSaving(true);
    try {
      await submitOnboarding(gender, parseInt(age), climate);
      const tree = await getOnboardingQuestions();
      setQuizTree(tree);
      setCurrentNodeId(tree.start);
      setQuestionNumber(1);
      setPhase('quiz');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleNext = async () => {
    if (!selectedOption || !currentNodeId) return;

    const newAnswers = [
      ...answers,
      {
        category: currentNodeId,
        choice: selectedOption.id,
        style_tags: selectedOption.style_tags,
      },
    ];
    setAnswers(newAnswers);

    const nextNodeId = selectedOption.next;
    setSelectedOption(null);

    if (nextNodeId && quizTree?.nodes[nextNodeId]) {
      setCurrentNodeId(nextNodeId);
      setQuestionNumber(questionNumber + 1);
    } else {
      setSaving(true);
      try {
        await submitStyleQuiz(newAnswers);
      } catch {}
      refresh();
      router.replace('/chat');
    }
  };

  const progress = totalQuestions > 0 ? (questionNumber / totalQuestions) * 100 : 0;

  if (phase === 'demographics') {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          <h1 className="font-display text-3xl font-semibold text-center mb-2">
            Let&apos;s get to know you
          </h1>
          <p className="text-center text-muted mb-8">
            A few quick questions to personalize your experience
          </p>

          <form onSubmit={handleDemographics} className="card backdrop-blur-md bg-white/70 dark:bg-surface-dark-1/70 p-6 flex flex-col gap-4">
            <div>
              <label className="block text-xs font-medium uppercase tracking-wider text-muted mb-1.5">Gender</label>
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
              <label className="block text-xs font-medium uppercase tracking-wider text-muted mb-1.5">Age</label>
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
              <label className="block text-xs font-medium uppercase tracking-wider text-muted mb-1.5">Climate</label>
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
        </motion.div>
      </div>
    );
  }

  // Quiz phase
  const q = currentNodeId ? quizTree?.nodes[currentNodeId] : null;
  if (!q) return null;

  const isTerminal = !selectedOption?.next || !quizTree?.nodes[selectedOption.next];

  return (
    <div className="min-h-screen flex flex-col items-center px-4 py-8">
      <div className="w-full max-w-2xl">
        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between text-sm text-muted mb-2">
            <span>Question {questionNumber}</span>
            <span>{questionNumber} of {totalQuestions || '?'}</span>
          </div>
          <div className="w-full h-1.5 bg-cream-dark dark:bg-surface-dark-2 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-accent dark:bg-accent-light rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
            />
          </div>
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={currentNodeId}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            <h2 className="font-display text-2xl font-semibold mb-6">{q.prompt}</h2>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-8">
              {q.options.map((opt, i) => (
                <motion.button
                  key={opt.id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.08, duration: 0.3 }}
                  onClick={() => setSelectedOption(opt)}
                  className={`relative card p-2 transition-all duration-200 hover:scale-[1.03] ${
                    selectedOption?.id === opt.id
                      ? 'ring-2 ring-accent dark:ring-accent-light scale-[1.02] shadow-lg'
                      : ''
                  }`}
                >
                  <img
                    src={opt.image_url}
                    alt={opt.label}
                    className="w-full aspect-square object-cover rounded-xl mb-2"
                    loading="lazy"
                  />
                  {selectedOption?.id === opt.id && (
                    <div className="absolute top-4 right-4 w-6 h-6 rounded-full bg-accent text-white flex items-center justify-center shadow-md">
                      <Check className="w-3.5 h-3.5" />
                    </div>
                  )}
                  <div className="text-sm font-medium text-center">{opt.label}</div>
                </motion.button>
              ))}
            </div>
          </motion.div>
        </AnimatePresence>

        <button
          onClick={handleNext}
          disabled={!selectedOption || saving}
          className="btn-primary w-full"
        >
          {saving
            ? 'Saving...'
            : isTerminal
              ? 'Finish'
              : 'Next'}
        </button>
      </div>
    </div>
  );
}
