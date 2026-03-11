'use client';

import { motion } from 'framer-motion';

const ease = [0.22, 1, 0.36, 1] as const;

const stagger = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.15, delayChildren: 0.2 },
  },
};

const fadeUp = {
  hidden: { opacity: 0, y: 28 },
  show: { opacity: 1, y: 0, transition: { duration: 0.8, ease } },
};

export default function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Decorative gradient blobs */}
      <div className="absolute top-0 right-0 w-[700px] h-[700px] bg-accent/[0.03] dark:bg-accent/[0.06] rounded-full blur-3xl -translate-y-1/4 translate-x-1/4" />
      <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-gold/[0.04] dark:bg-gold/[0.05] rounded-full blur-3xl translate-y-1/4 -translate-x-1/4" />
      <div className="absolute top-1/2 left-1/2 w-[300px] h-[300px] bg-accent/[0.02] dark:bg-accent/[0.04] rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2" />

      <motion.div
        variants={stagger}
        initial="hidden"
        animate="show"
        className="relative z-10 max-w-3xl mx-auto px-6 text-center"
      >
        {/* Overline */}
        <motion.p
          variants={fadeUp}
          className="text-[11px] font-medium uppercase tracking-[0.2em] text-accent dark:text-accent-light mb-6"
        >
          AI-Powered Personal Styling
        </motion.p>

        {/* Headline */}
        <motion.h1
          variants={fadeUp}
          className="font-display text-6xl sm:text-7xl md:text-8xl font-semibold tracking-tight leading-[0.92] mb-6"
        >
          Your Personal
          <br />
          <span className="italic text-accent dark:text-accent-light">AI Stylist</span>
        </motion.h1>

        {/* Decorative rule */}
        <motion.div
          variants={fadeUp}
          className="w-20 h-[1.5px] bg-accent/40 dark:bg-accent-light/40 mx-auto mb-6"
        />

        {/* Subtitle */}
        <motion.p
          variants={fadeUp}
          className="text-lg md:text-xl text-muted max-w-lg mx-auto leading-relaxed mb-10"
        >
          Curated recommendations that understand your taste, your wardrobe,
          and the way you want to be seen.
        </motion.p>

        {/* CTAs */}
        <motion.div
          variants={fadeUp}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <a href="/login" className="btn-primary text-base px-8 py-3.5">
            Get Started
          </a>
          <a href="#features" className="btn-secondary text-base px-8 py-3.5">
            Learn More
          </a>
        </motion.div>
      </motion.div>
    </section>
  );
}
