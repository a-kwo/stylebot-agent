'use client';

import { motion } from 'framer-motion';

const ease = [0.22, 1, 0.36, 1] as const;

export default function CTASection() {
  return (
    <section className="py-24 md:py-32 bg-gradient-to-r from-accent to-accent-dark relative overflow-hidden">
      {/* Subtle decorative glow */}
      <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-white/[0.04] rounded-full blur-3xl translate-x-1/3 -translate-y-1/3" />
      <div className="absolute bottom-0 left-0 w-[300px] h-[300px] bg-gold/[0.06] rounded-full blur-3xl -translate-x-1/3 translate-y-1/3" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-80px' }}
        transition={{ duration: 0.7, ease }}
        className="relative z-10 max-w-2xl mx-auto px-6 text-center"
      >
        <h2 className="font-display text-4xl md:text-5xl font-semibold tracking-tight text-white mb-4">
          Ready to Transform
          <br />
          <span className="italic">Your Style?</span>
        </h2>
        <p className="text-white/70 text-base md:text-lg mb-10 max-w-md mx-auto leading-relaxed">
          Join StyleBot and discover a wardrobe that works as
          beautifully as you do.
        </p>
        <a
          href="/login"
          className="inline-block px-10 py-4 rounded-xl font-medium text-accent bg-white shadow-lg shadow-black/10 hover:shadow-xl hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 text-base"
        >
          Get Started &mdash; It&apos;s Free
        </a>
      </motion.div>
    </section>
  );
}
