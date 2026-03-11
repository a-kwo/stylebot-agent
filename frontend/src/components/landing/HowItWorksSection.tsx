'use client';

import { UserPlus, ShirtIcon, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';

const ease = [0.22, 1, 0.36, 1] as const;

const steps = [
  {
    number: '01',
    icon: UserPlus,
    title: 'Create Your Profile',
    description: 'Take our style quiz to share your preferences, lifestyle, and aesthetic vision.',
  },
  {
    number: '02',
    icon: ShirtIcon,
    title: 'Build Your Wardrobe',
    description: 'Add your existing pieces so StyleBot understands what you already own and love.',
  },
  {
    number: '03',
    icon: Sparkles,
    title: 'Get Styled',
    description: 'Receive AI-powered outfit recommendations and discover pieces that complete your look.',
  },
];

const stepVariant = {
  hidden: { opacity: 0, y: 24 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.7, delay: i * 0.18, ease },
  }),
};

export default function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-28 md:py-36 bg-cream-dark/50 dark:bg-surface-dark-1/50">
      <div className="max-w-5xl mx-auto px-6">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.7, ease }}
          className="text-center mb-20"
        >
          <p className="text-[11px] font-medium uppercase tracking-[0.2em] text-accent dark:text-accent-light mb-4">
            The Process
          </p>
          <h2 className="font-display text-4xl md:text-5xl font-semibold tracking-tight">
            Three Simple Steps
          </h2>
          <div className="w-12 h-[1.5px] bg-accent/30 dark:bg-accent-light/30 mx-auto mt-5" />
        </motion.div>

        {/* Steps */}
        <div className="relative grid grid-cols-1 md:grid-cols-3 gap-12 md:gap-8">
          {/* Connecting line — desktop horizontal */}
          <div className="hidden md:block absolute top-8 left-[16.67%] right-[16.67%] h-px bg-gradient-to-r from-transparent via-border dark:via-surface-dark-3 to-transparent" />

          {/* Connecting line — mobile vertical */}
          <div className="md:hidden absolute top-0 bottom-0 left-8 w-px bg-gradient-to-b from-transparent via-border dark:via-surface-dark-3 to-transparent" />

          {steps.map((step, i) => {
            const Icon = step.icon;
            return (
              <motion.div
                key={step.number}
                custom={i}
                variants={stepVariant}
                initial="hidden"
                whileInView="show"
                viewport={{ once: true, margin: '-60px' }}
                className="relative flex md:flex-col items-start md:items-center md:text-center gap-5 md:gap-0"
              >
                {/* Number circle */}
                <div className="relative z-10 flex-shrink-0 w-16 h-16 rounded-full bg-white dark:bg-surface-dark-2 border border-border/80 dark:border-surface-dark-3/80 shadow-sm flex items-center justify-center md:mb-6">
                  <Icon className="w-6 h-6 text-accent dark:text-accent-light" strokeWidth={1.5} />
                </div>

                <div>
                  <span className="font-display text-sm italic text-accent/60 dark:text-accent-light/60 tracking-wide">
                    Step {step.number}
                  </span>
                  <h3 className="font-display text-xl font-semibold tracking-tight mt-1 mb-2">
                    {step.title}
                  </h3>
                  <p className="text-sm text-muted leading-relaxed max-w-xs">
                    {step.description}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
