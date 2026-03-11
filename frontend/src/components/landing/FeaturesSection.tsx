'use client';

import { MessageSquare, Shirt, Palette, Search } from 'lucide-react';
import { motion } from 'framer-motion';

const ease = [0.22, 1, 0.36, 1] as const;

const features = [
  {
    icon: MessageSquare,
    title: 'AI Styling Chat',
    description:
      'Converse naturally with an AI that learns your preferences and delivers personalized advice — from daily outfits to special occasions.',
  },
  {
    icon: Shirt,
    title: 'Wardrobe Management',
    description:
      'Catalog your entire closet with intelligent categorization. Know what you own, what pairs well, and what gaps remain.',
  },
  {
    icon: Palette,
    title: 'Outfit Builder',
    description:
      'Compose complete looks from your wardrobe with drag-and-drop simplicity. Save, revisit, and refine your favorite combinations.',
  },
  {
    icon: Search,
    title: 'Smart Product Search',
    description:
      'Discover pieces that complement your existing wardrobe. Real product results tailored to your style profile and budget.',
  },
];

const cardVariant = {
  hidden: { opacity: 0, y: 24 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, delay: i * 0.12, ease },
  }),
};

export default function FeaturesSection() {
  return (
    <section id="features" className="py-28 md:py-36">
      <div className="max-w-6xl mx-auto px-6">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.7, ease }}
          className="text-center mb-16"
        >
          <p className="text-[11px] font-medium uppercase tracking-[0.2em] text-accent dark:text-accent-light mb-4">
            What We Offer
          </p>
          <h2 className="font-display text-4xl md:text-5xl font-semibold tracking-tight">
            Style, Elevated
          </h2>
          <div className="w-12 h-[1.5px] bg-accent/30 dark:bg-accent-light/30 mx-auto mt-5" />
        </motion.div>

        {/* Feature grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {features.map((feature, i) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={feature.title}
                custom={i}
                variants={cardVariant}
                initial="hidden"
                whileInView="show"
                viewport={{ once: true, margin: '-60px' }}
                className="card-hover p-6 flex flex-col"
              >
                <div className="w-10 h-10 rounded-xl bg-accent/10 dark:bg-accent/15 flex items-center justify-center mb-4">
                  <Icon className="w-5 h-5 text-accent dark:text-accent-light" strokeWidth={1.5} />
                </div>
                <h3 className="font-display text-xl font-semibold mb-2 tracking-tight">
                  {feature.title}
                </h3>
                <p className="text-sm text-muted leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
