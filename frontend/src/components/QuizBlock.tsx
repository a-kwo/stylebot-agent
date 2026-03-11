'use client';

import { useState } from 'react';
import { submitQuizAnswer } from '@/lib/api';
import { Check } from 'lucide-react';
import { motion } from 'framer-motion';

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
    if (selected) return;
    setSelected(opt.id);
    submitQuizAnswer({
      category: quiz.category,
      choice: opt.id,
      style_tags: opt.style_tags,
    }).catch(() => {});
  };

  return (
    <div className="card p-4 max-w-lg">
      <div className="text-xs font-medium text-accent dark:text-accent-light mb-1">
        StyleBot has a question
      </div>
      <p className="text-sm font-medium mb-3">{quiz.prompt}</p>
      <div className="grid grid-cols-2 gap-2">
        {quiz.options.map((opt, i) => (
          <motion.button
            key={opt.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08, duration: 0.3 }}
            onClick={() => handleSelect(opt)}
            disabled={!!selected}
            className={`relative rounded-xl overflow-hidden border-2 transition-all duration-300 ${
              selected === opt.id
                ? 'border-accent dark:border-accent-light ring-2 ring-accent/20'
                : selected
                  ? 'border-transparent opacity-40'
                  : 'border-transparent hover:border-accent/30 hover:scale-[1.02]'
            }`}
          >
            <img
              src={opt.image_url}
              alt={opt.label}
              className="w-full aspect-square object-cover"
              loading="lazy"
            />
            {selected === opt.id && (
              <div className="absolute top-2 right-2 w-6 h-6 rounded-full bg-accent text-white flex items-center justify-center">
                <Check className="w-3.5 h-3.5" />
              </div>
            )}
            <div className="text-xs font-medium py-1.5">{opt.label}</div>
          </motion.button>
        ))}
      </div>
    </div>
  );
}
