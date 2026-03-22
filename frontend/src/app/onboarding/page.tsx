'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import {
  submitOnboarding,
  getQuizV2,
  submitStyleQuizV2,
} from '@/lib/api';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Briefcase, Coffee, Music, Heart, Sparkles, Zap, Plane, ChevronRight } from 'lucide-react';

// ── Types ────────────────────────────────────────────────────────────────────

interface QuizOption {
  id: string;
  label: string;
  image_url: string;
  vector_scores: Record<string, number>;
}

interface QuizQuestion {
  id: string;
  stage: number;
  prompt: string;
  subtitle?: string;
  options?: QuizOption[];
  branch_on?: string;
  variants?: Record<string, QuizOption[]>;
  occasion_template?: boolean;
}

interface OccasionItem {
  id: string;
  label: string;
  icon: string;
}

interface QuizData {
  occasions: OccasionItem[];
  questions: Record<string, QuizQuestion>;
  question_order: string[];
  occasion_labels: Record<string, string>;
  stages: { id: number; label: string; question_count: number }[];
}

interface Answer {
  question_id: string;
  option_id: string;
  vector_scores: Record<string, number>;
}

// ── Icon map ─────────────────────────────────────────────────────────────────

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  briefcase: Briefcase,
  coffee: Coffee,
  music: Music,
  heart: Heart,
  sparkles: Sparkles,
  zap: Zap,
  plane: Plane,
};

// ── Gender icons (SVG) ───────────────────────────────────────────────────────

function MaleIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" className={className} fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="26" cy="38" r="16" />
      <line x1="38" y1="26" x2="54" y2="10" />
      <polyline points="42,10 54,10 54,22" />
    </svg>
  );
}

function FemaleIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" className={className} fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="32" cy="24" r="16" />
      <line x1="32" y1="40" x2="32" y2="58" />
      <line x1="22" y1="50" x2="42" y2="50" />
    </svg>
  );
}

function NonBinaryIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" className={className} fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="32" cy="36" r="14" />
      <line x1="32" y1="22" x2="32" y2="6" />
      <line x1="24" y1="12" x2="32" y2="6" />
      <line x1="40" y1="12" x2="32" y2="6" />
      <line x1="32" y1="50" x2="32" y2="60" />
    </svg>
  );
}

// ── Age scroller ─────────────────────────────────────────────────────────────

const MIN_AGE = 13;
const MAX_AGE = 80;
const ITEM_HEIGHT = 56;

function AgeScroller({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const ages = Array.from({ length: MAX_AGE - MIN_AGE + 1 }, (_, i) => MIN_AGE + i);
  const isScrollingRef = useRef(false);
  const scrollTimeoutRef = useRef<ReturnType<typeof setTimeout>>();

  // Scroll to selected value on mount
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const idx = value - MIN_AGE;
    el.scrollTop = idx * ITEM_HEIGHT;
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleScroll = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;

    isScrollingRef.current = true;
    if (scrollTimeoutRef.current) clearTimeout(scrollTimeoutRef.current);

    scrollTimeoutRef.current = setTimeout(() => {
      isScrollingRef.current = false;
      const idx = Math.round(el.scrollTop / ITEM_HEIGHT);
      const snappedAge = Math.min(Math.max(MIN_AGE + idx, MIN_AGE), MAX_AGE);
      onChange(snappedAge);
      el.scrollTo({ top: idx * ITEM_HEIGHT, behavior: 'smooth' });
    }, 80);
  }, [onChange]);

  const selectAge = (age: number) => {
    onChange(age);
    const el = containerRef.current;
    if (el) {
      el.scrollTo({ top: (age - MIN_AGE) * ITEM_HEIGHT, behavior: 'smooth' });
    }
  };

  return (
    <div className="relative flex flex-col items-center">
      {/* Selection highlight band */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-[56px] rounded-2xl border-2 border-accent/30 dark:border-accent-light/30 bg-accent/5 dark:bg-accent-light/5 pointer-events-none z-10" />

      {/* Fade masks */}
      <div className="absolute top-0 left-0 right-0 h-20 bg-gradient-to-b from-white dark:from-surface-dark-1 to-transparent z-20 pointer-events-none rounded-t-2xl" />
      <div className="absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-white dark:from-surface-dark-1 to-transparent z-20 pointer-events-none rounded-b-2xl" />

      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="h-[280px] w-full overflow-y-auto scrollbar-none scroll-smooth"
        style={{
          scrollSnapType: 'y mandatory',
          paddingTop: `${ITEM_HEIGHT * 2}px`,
          paddingBottom: `${ITEM_HEIGHT * 2}px`,
        }}
      >
        {ages.map((age) => {
          const isSelected = age === value;
          const distance = Math.abs(age - value);
          const opacity = distance === 0 ? 1 : distance === 1 ? 0.5 : distance === 2 ? 0.3 : 0.15;
          const scale = distance === 0 ? 1 : distance === 1 ? 0.9 : 0.8;

          return (
            <div
              key={age}
              onClick={() => selectAge(age)}
              className="flex items-center justify-center cursor-pointer select-none transition-all duration-200"
              style={{
                height: `${ITEM_HEIGHT}px`,
                scrollSnapAlign: 'center',
                opacity,
                transform: `scale(${scale})`,
              }}
            >
              <span
                className={`font-display text-4xl transition-colors duration-200 ${
                  isSelected
                    ? 'text-accent dark:text-accent-light font-semibold'
                    : 'text-ink/50 dark:text-zinc-400'
                }`}
              >
                {age}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Scrollbar-none utility (inline style fallback) ───────────────────────────

const scrollbarNoneCSS = `
  .scrollbar-none::-webkit-scrollbar { display: none; }
  .scrollbar-none { -ms-overflow-style: none; scrollbar-width: none; }
`;

// ── Component ────────────────────────────────────────────────────────────────

export default function OnboardingPage() {
  const router = useRouter();
  const { authenticated, onboarded, refresh } = useAuth();

  // Phase: gender → age → occasions → quiz
  const [phase, setPhase] = useState<'gender' | 'age' | 'occasions' | 'quiz'>('gender');

  // Demographics
  const [gender, setGender] = useState('');
  const [age, setAge] = useState(25);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  // Quiz data
  const [quizData, setQuizData] = useState<QuizData | null>(null);

  // Stage 0: Occasions
  const [selectedOccasions, setSelectedOccasions] = useState<string[]>([]);

  // Quiz questions
  const [questionIndex, setQuestionIndex] = useState(0);
  const [allQuestions, setAllQuestions] = useState<string[]>([]);
  const [selectedOption, setSelectedOption] = useState<QuizOption | null>(null);
  const [answers, setAnswers] = useState<Answer[]>([]);
  const [currentStage, setCurrentStage] = useState(0);

  // Auth guards
  useEffect(() => {
    if (!authenticated) {
      router.replace('/login');
    } else if (onboarded) {
      router.replace('/chat');
    }
  }, [authenticated, onboarded, router]);

  if (!authenticated || onboarded) return null;

  // ── Gender selection handler ───────────────────────────────────────────────

  const selectGender = (g: string) => {
    setGender(g);
    // Auto-advance after a brief pause so the selection registers visually
    setTimeout(() => setPhase('age'), 400);
  };

  // ── Age confirmation handler ───────────────────────────────────────────────

  const handleAgeConfirm = async () => {
    setError('');
    setSaving(true);
    try {
      await submitOnboarding(gender, age);
      const data = await getQuizV2();
      setQuizData(data);
      setPhase('occasions');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  // ── Occasion toggle ──────────────────────────────────────────────────────

  const toggleOccasion = (id: string) => {
    setSelectedOccasions((prev) =>
      prev.includes(id) ? prev.filter((o) => o !== id) : [...prev, id]
    );
  };

  // ── Start quiz from occasions ────────────────────────────────────────────

  const handleStartQuiz = () => {
    if (!quizData || selectedOccasions.length === 0) return;

    setAllQuestions([...quizData.question_order]);
    setQuestionIndex(0);
    setCurrentStage(1);
    setPhase('quiz');
  };

  // ── Get current question data ────────────────────────────────────────────

  const getCurrentQuestion = (): { prompt: string; subtitle?: string; options: QuizOption[] } | null => {
    if (!quizData || allQuestions.length === 0) return null;
    const qId = allQuestions[questionIndex];

    const question = quizData.questions[qId];
    if (!question) return null;

    if (question.branch_on && question.variants) {
      const branchAnswer = answers.find((a) => a.question_id === question.branch_on);
      const branchKey = branchAnswer?.option_id || Object.keys(question.variants)[0];
      const options = question.variants[branchKey] || Object.values(question.variants)[0];
      return { prompt: question.prompt, subtitle: question.subtitle, options };
    }

    if (question.occasion_template) {
      const topOccasion = selectedOccasions[0];
      const occasionLabel = quizData.occasion_labels[topOccasion] || topOccasion;
      return {
        prompt: question.prompt.replace('{occasion}', occasionLabel),
        subtitle: question.subtitle,
        options: question.options || [],
      };
    }

    return {
      prompt: question.prompt,
      subtitle: question.subtitle,
      options: question.options || [],
    };
  };

  // ── Handle next question ─────────────────────────────────────────────────

  const handleNext = async () => {
    if (!selectedOption) return;

    const qId = allQuestions[questionIndex];
    const newAnswer: Answer = {
      question_id: qId,
      option_id: selectedOption.id,
      vector_scores: selectedOption.vector_scores,
    };
    const newAnswers = [...answers, newAnswer];
    setAnswers(newAnswers);
    setSelectedOption(null);

    const nextIndex = questionIndex + 1;

    if (nextIndex >= allQuestions.length) {
      setSaving(true);
      try {
        await submitStyleQuizV2(newAnswers, selectedOccasions);
      } catch {}
      refresh();
      router.replace('/chat');
      return;
    }

    setQuestionIndex(nextIndex);

    const nextQId = allQuestions[nextIndex];
    if (quizData) {
      const nextQ = quizData.questions[nextQId];
      if (nextQ) setCurrentStage(nextQ.stage);
    }
  };

  // ── Progress calculation ─────────────────────────────────────────────────

  const totalQuestions = allQuestions.length;
  const progress = totalQuestions > 0 ? ((questionIndex + 1) / totalQuestions) * 100 : 0;

  const stageLabels = quizData?.stages || [];
  const currentStageLabel = stageLabels.find((s) => s.id === currentStage)?.label || '';

  // ── Shared step counter for demographics ───────────────────────────────────

  const demoStep = phase === 'gender' ? 1 : 2;

  // ── Render: Gender Selection ───────────────────────────────────────────────

  if (phase === 'gender') {
    const genderOptions = [
      {
        id: 'male',
        label: 'Man',
        Icon: MaleIcon,
        color: 'from-blue-500/20 to-blue-600/10 border-blue-400/40 hover:border-blue-400/70',
        iconColor: 'text-blue-500',
        selectedRing: 'ring-blue-500',
        selectedBg: 'bg-blue-500/10',
      },
      {
        id: 'female',
        label: 'Woman',
        Icon: FemaleIcon,
        color: 'from-pink-500/20 to-pink-600/10 border-pink-400/40 hover:border-pink-400/70',
        iconColor: 'text-pink-500',
        selectedRing: 'ring-pink-500',
        selectedBg: 'bg-pink-500/10',
      },
      {
        id: 'non-binary',
        label: 'Non-binary',
        Icon: NonBinaryIcon,
        color: 'from-violet-500/20 to-violet-600/10 border-violet-400/40 hover:border-violet-400/70',
        iconColor: 'text-violet-500',
        selectedRing: 'ring-violet-500',
        selectedBg: 'bg-violet-500/10',
      },
    ];

    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <style>{scrollbarNoneCSS}</style>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          className="w-full max-w-lg text-center"
        >
          {/* Step indicator */}
          <div className="flex items-center justify-center gap-2 mb-10">
            <div className="w-8 h-1 rounded-full bg-accent dark:bg-accent-light" />
            <div className="w-8 h-1 rounded-full bg-cream-dark dark:bg-surface-dark-2" />
          </div>

          <h1 className="font-display text-4xl font-semibold mb-3">
            How do you identify?
          </h1>
          <p className="text-muted mb-12 text-lg">
            This helps us tailor recommendations for you
          </p>

          <div className="flex items-center justify-center gap-6">
            {genderOptions.map((opt, i) => (
              <motion.button
                key={opt.id}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 + i * 0.1, duration: 0.4 }}
                onClick={() => selectGender(opt.id)}
                className={`group relative flex flex-col items-center gap-4 p-6 rounded-3xl border bg-gradient-to-b transition-all duration-300 hover:scale-105 active:scale-95 ${opt.color} ${
                  gender === opt.id
                    ? `ring-2 ${opt.selectedRing} ${opt.selectedBg} scale-105`
                    : ''
                }`}
              >
                <div className={`w-16 h-16 ${opt.iconColor} transition-transform duration-300 group-hover:scale-110`}>
                  <opt.Icon className="w-full h-full" />
                </div>
                <span className="text-sm font-medium tracking-wide">{opt.label}</span>

                {gender === opt.id && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-accent dark:bg-accent-light text-white flex items-center justify-center shadow-md"
                  >
                    <Check className="w-3.5 h-3.5" />
                  </motion.div>
                )}
              </motion.button>
            ))}
          </div>

          {error && <p className="text-red-500 text-sm mt-6">{error}</p>}
        </motion.div>
      </div>
    );
  }

  // ── Render: Age Selection ──────────────────────────────────────────────────

  if (phase === 'age') {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <style>{scrollbarNoneCSS}</style>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          className="w-full max-w-sm text-center"
        >
          {/* Step indicator */}
          <div className="flex items-center justify-center gap-2 mb-10">
            <div className="w-8 h-1 rounded-full bg-accent/40 dark:bg-accent-light/40" />
            <div className="w-8 h-1 rounded-full bg-accent dark:bg-accent-light" />
          </div>

          <h1 className="font-display text-4xl font-semibold mb-3">
            How old are you?
          </h1>
          <p className="text-muted mb-10 text-lg">
            Style evolves with age — we&apos;ll keep that in mind
          </p>

          <div className="card backdrop-blur-md bg-white/80 dark:bg-surface-dark-1/80 p-6 mb-8">
            <AgeScroller value={age} onChange={setAge} />
          </div>

          <button
            onClick={handleAgeConfirm}
            disabled={saving}
            className="btn-primary w-full text-lg py-4 flex items-center justify-center gap-2"
          >
            {saving ? 'Setting up...' : 'Continue'}
            {!saving && <ChevronRight className="w-5 h-5" />}
          </button>

          <button
            onClick={() => setPhase('gender')}
            className="btn-ghost mt-3 w-full text-sm"
          >
            Back
          </button>

          {error && <p className="text-red-500 text-sm mt-4">{error}</p>}
        </motion.div>
      </div>
    );
  }

  // ── Render: Occasion Selection (Stage 0) ─────────────────────────────────

  if (phase === 'occasions') {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-lg"
        >
          <h1 className="font-display text-3xl font-semibold text-center mb-2">
            What do you dress for?
          </h1>
          <p className="text-center text-muted mb-8">
            Select all that apply — this helps us tailor the quiz to your life
          </p>

          <div className="grid grid-cols-2 gap-3 mb-8">
            {quizData?.occasions.map((occ, i) => {
              const Icon = ICON_MAP[occ.icon] || Coffee;
              const isSelected = selectedOccasions.includes(occ.id);
              return (
                <motion.button
                  key={occ.id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.06, duration: 0.3 }}
                  onClick={() => toggleOccasion(occ.id)}
                  className={`relative card p-4 flex items-center gap-3 transition-all duration-200 hover:scale-[1.02] ${
                    isSelected
                      ? 'ring-2 ring-accent dark:ring-accent-light bg-accent/5 dark:bg-accent-light/5'
                      : ''
                  }`}
                >
                  <Icon className={`w-5 h-5 flex-shrink-0 ${isSelected ? 'text-accent dark:text-accent-light' : 'text-muted'}`} />
                  <span className="text-sm font-medium">{occ.label}</span>
                  {isSelected && (
                    <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-accent text-white flex items-center justify-center">
                      <Check className="w-3 h-3" />
                    </div>
                  )}
                </motion.button>
              );
            })}
          </div>

          <button
            onClick={handleStartQuiz}
            disabled={selectedOccasions.length === 0}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            Start Style Quiz
            <ChevronRight className="w-4 h-4" />
          </button>

          {selectedOccasions.length === 0 && (
            <p className="text-center text-muted text-sm mt-3">
              Select at least one occasion to continue
            </p>
          )}
        </motion.div>
      </div>
    );
  }

  // ── Render: Quiz Questions ───────────────────────────────────────────────

  const currentQ = getCurrentQuestion();
  if (!currentQ) return null;

  const isLastQuestion = questionIndex === allQuestions.length - 1;

  return (
    <div className="min-h-screen flex flex-col items-center px-4 py-8">
      <div className="w-full max-w-2xl">
        {/* Stage indicator + progress bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-accent dark:text-accent-light font-medium">
              {currentStageLabel}
            </span>
            <span className="text-muted">
              {questionIndex + 1} of {totalQuestions}
            </span>
          </div>
          <div className="w-full h-1.5 bg-cream-dark dark:bg-surface-dark-2 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-accent dark:bg-accent-light rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
            />
          </div>
          {/* Stage dots */}
          <div className="flex items-center justify-center gap-2 mt-3">
            {stageLabels.filter((s) => s.id > 0).map((stage) => (
              <div
                key={stage.id}
                className={`w-2 h-2 rounded-full transition-colors duration-300 ${
                  stage.id === currentStage
                    ? 'bg-accent dark:bg-accent-light'
                    : stage.id < currentStage
                      ? 'bg-accent/40 dark:bg-accent-light/40'
                      : 'bg-cream-dark dark:bg-surface-dark-2'
                }`}
                title={stage.label}
              />
            ))}
          </div>
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={allQuestions[questionIndex]}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className=""
          >
            <h2 className="font-display text-2xl font-semibold mb-1">{currentQ.prompt}</h2>
            {currentQ.subtitle && (
              <p className="text-muted text-sm mb-6">{currentQ.subtitle}</p>
            )}
            {!currentQ.subtitle && <div className="mb-6" />}

            <div className={`grid gap-4 mb-8 ${
              currentQ.options.length === 4 ? 'grid-cols-2' : 'grid-cols-3'
            }`}>
              {currentQ.options.map((opt, i) => (
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
                    className={`w-full object-cover rounded-xl mb-2 ${
                      currentQ.options.length === 4
                        ? 'aspect-[3/2]'
                        : 'aspect-[3/4]'
                    }`}
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
            ? 'Finishing up...'
            : isLastQuestion
              ? 'See My Style Profile'
              : 'Next'}
        </button>
      </div>
    </div>
  );
}
