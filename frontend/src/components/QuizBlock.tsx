'use client';

import { useState } from 'react';
import { submitQuizAnswer } from '@/lib/api';

interface QuizOption {
  id: string;
  label: string;
  image_url: string;
  style_tags: string[];
}

interface QuizData {
  category: string;
  prompt: string;
  options: QuizOption[];
}

export default function QuizBlock({ quiz }: { quiz: QuizData }) {
  const [selected, setSelected] = useState<string | null>(null);

  const handleSelect = (opt: QuizOption) => {
    if (selected) return; // prevent re-selection
    setSelected(opt.id);
    submitQuizAnswer({
      category: quiz.category,
      choice: opt.id,
      style_tags: opt.style_tags,
    }).catch(() => {});
  };

  return (
    <div className="card p-4 max-w-lg">
      <div className="text-xs font-medium text-muted mb-1">
        StyleBot has a question
      </div>
      <p className="text-sm font-medium mb-3">{quiz.prompt}</p>
      <div className="grid grid-cols-2 gap-2">
        {quiz.options.map((opt) => (
          <button
            key={opt.id}
            onClick={() => handleSelect(opt)}
            disabled={!!selected}
            className={`rounded-xl overflow-hidden border-2 transition-all ${
              selected === opt.id
                ? 'border-ink dark:border-cream'
                : selected
                  ? 'border-transparent opacity-50'
                  : 'border-transparent hover:border-zinc-300'
            }`}
          >
            <img
              src={opt.image_url}
              alt={opt.label}
              className="w-full aspect-square object-cover"
              loading="lazy"
            />
            <div className="text-xs font-medium py-1">{opt.label}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
