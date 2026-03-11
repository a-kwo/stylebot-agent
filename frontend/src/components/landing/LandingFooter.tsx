'use client';

const footerLinks = [
  { href: '#features', label: 'Features' },
  { href: '#how-it-works', label: 'How It Works' },
  { href: '#about', label: 'About' },
];

export default function LandingFooter() {
  return (
    <footer className="py-10 border-t border-border/60 dark:border-surface-dark-3/60">
      <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <a href="/" className="font-display text-lg font-semibold text-accent dark:text-accent-light">
            StyleBot
          </a>
          <span className="text-xs text-muted/50">
            &copy; {new Date().getFullYear()}
          </span>
        </div>

        <nav className="flex items-center gap-6">
          {footerLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-xs text-muted hover:text-ink dark:hover:text-zinc-300 transition-colors"
            >
              {link.label}
            </a>
          ))}
        </nav>
      </div>
    </footer>
  );
}
