'use client';

import { motion } from 'framer-motion';

const ease = [0.22, 1, 0.36, 1] as const;

export default function AboutSection() {
  return (
    <section id="about" className="py-28 md:py-36">
      <div className="max-w-3xl mx-auto px-6 text-center">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.8, ease }}
        >
          <p className="text-[11px] font-medium uppercase tracking-[0.2em] text-accent dark:text-accent-light mb-4">
            Our Philosophy
          </p>
          <h2 className="font-display text-4xl md:text-5xl font-semibold tracking-tight mb-8">
            Dressing Well Is a Form
            <br className="hidden sm:block" />
            <span className="italic"> of Self-Respect</span>
          </h2>
          <div className="w-12 h-[1.5px] bg-accent/30 dark:bg-accent-light/30 mx-auto mb-8" />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-60px' }}
          transition={{ duration: 0.7, delay: 0.15, ease }}
          className="space-y-5 text-muted leading-relaxed text-base md:text-lg"
        >
          <p>
            StyleBot was born from a simple conviction: everyone deserves access to
            thoughtful, personalized styling — not just those with a stylist on
            speed dial. We pair the nuance of human taste with the intelligence
            of AI to help you build a wardrobe that feels unmistakably yours.
          </p>
          <p>
            No trends for trends' sake. No algorithmic sameness. Just considered
            guidance that respects your individuality, understands your closet, and
            evolves with your sense of self.
          </p>
        </motion.div>
      </div>
    </section>
  );
}
