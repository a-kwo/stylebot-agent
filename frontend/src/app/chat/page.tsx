'use client';

import { useState, useEffect, useRef, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { getConversations, streamChat } from '@/lib/api';
import ProductCard from '@/components/ProductCard';
import QuizBlock from '@/components/QuizBlock';
import { ArrowUp, Loader2, MessageSquare } from 'lucide-react';
import { motion } from 'framer-motion';

interface Message {
  role: 'user' | 'assistant';
  text?: string;
  products?: any[];
  quizzes?: any[];
  toolStatus?: string;
  streaming?: boolean;
  actions?: { label: string; message: string }[];
}

function ThinkingDots() {
  return (
    <div className="flex items-center gap-1 px-4 py-3">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="w-2 h-2 rounded-full bg-accent/40 dark:bg-accent-light/40"
          animate={{ scale: [1, 1.3, 1], opacity: [0.4, 1, 0.4] }}
          transition={{
            duration: 1,
            repeat: Infinity,
            delay: i * 0.15,
          }}
        />
      ))}
    </div>
  );
}

export default function ChatPage() {
  const router = useRouter();
  const { authenticated, onboarded, loading: authLoading } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const tokenBufferRef = useRef('');
  const flushTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (authenticated === false) {
      router.replace('/login');
    } else if (onboarded === false) {
      router.replace('/onboarding');
    }
  }, [authenticated, onboarded, authLoading, router]);

  // Load history
  useEffect(() => {
    if (!authenticated || onboarded !== true) return;

    getConversations()
      .then((history: any[]) => {
        const turns = history.filter(
          (m: any) => m.role === 'user' || m.role === 'assistant'
        );

        if (turns.length === 0) {
          // First-time user — show welcome with action buttons
          setMessages([
            {
              role: 'assistant',
              text: "Hey! I'm StyleBot — your personal styling assistant. Ready to find some pieces that match your vibe?",
              actions: [
                { label: "Sure, let's get started!", message: "Show me some pieces you'd pick for me based on my style profile. No questions, just show me what you've got!" },
                { label: "No, let's chat first", message: "Let's just chat first" },
              ],
            },
          ]);
          setHistoryLoaded(true);
          return;
        }

        const loaded: Message[] = [];
        for (const msg of history) {
          if (msg.role === 'user' && typeof msg.content === 'string') {
            loaded.push({ role: 'user', text: msg.content });
          } else if (msg.role === 'assistant' && Array.isArray(msg.content)) {
            const texts = msg.content
              .filter((b: any) => b.type === 'text' && b.text)
              .map((b: any) => b.text)
              .join('\n\n');
            if (texts) loaded.push({ role: 'assistant', text: texts });
          } else if (msg.role === 'meta' && Array.isArray(msg.content)) {
            const products: any[] = [];
            const quizzes: any[] = [];
            for (const block of msg.content) {
              if (block.type === 'products' && block.products) {
                products.push(...block.products);
              } else if (block.type === 'quiz' && block.quiz) {
                quizzes.push(block.quiz);
              }
            }
            if (products.length > 0 || quizzes.length > 0) {
              const lastAssistant = [...loaded].reverse().find((m) => m.role === 'assistant');
              if (lastAssistant) {
                if (products.length > 0) lastAssistant.products = products;
                if (quizzes.length > 0) lastAssistant.quizzes = quizzes;
              } else {
                loaded.push({
                  role: 'assistant',
                  products: products.length > 0 ? products : undefined,
                  quizzes: quizzes.length > 0 ? quizzes : undefined,
                });
              }
            }
          }
        }
        if (loaded.length > 0) setMessages(loaded);
        setHistoryLoaded(true);
      })
      .catch(() => { setHistoryLoaded(true); });
  }, [authenticated, onboarded]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (!authenticated || onboarded !== true) return null;

  const sendMessage = (text: string) => {
    if (!text || sending) return;

    // Remove action buttons from all messages once user acts
    setMessages((prev) =>
      prev.map((m) => (m.actions ? { ...m, actions: undefined } : m))
    );

    setSending(true);

    setMessages((prev) => [
      ...prev,
      { role: 'user', text },
      { role: 'assistant', text: '', streaming: true },
    ]);

    const flushTokenBuffer = () => {
      const buffered = tokenBufferRef.current;
      if (!buffered) return;
      tokenBufferRef.current = '';
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last.role === 'assistant') {
          updated[updated.length - 1] = {
            ...last,
            text: (last.text || '') + buffered,
          };
        }
        return updated;
      });
    };

    abortRef.current = streamChat(text, {
      onToken(token) {
        tokenBufferRef.current += token;
        if (!flushTimerRef.current) {
          flushTimerRef.current = setTimeout(() => {
            flushTimerRef.current = null;
            flushTokenBuffer();
          }, 30);
        }
      },
      onProducts(items) {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === 'assistant') {
            updated[updated.length - 1] = {
              ...last,
              products: [...(last.products || []), ...items],
            };
          }
          return updated;
        });
      },
      onQuiz(quiz) {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === 'assistant') {
            updated[updated.length - 1] = {
              ...last,
              quizzes: [...(last.quizzes || []), quiz],
            };
          }
          return updated;
        });
      },
      onToolStatus(tool, status) {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === 'assistant') {
            const label =
              status === 'calling'
                ? `Calling ${tool}...`
                : status === 'executing'
                  ? `Running ${tool}...`
                  : '';
            updated[updated.length - 1] = { ...last, toolStatus: label };
          }
          return updated;
        });
      },
      onError(message) {
        flushTokenBuffer();
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === 'assistant') {
            updated[updated.length - 1] = {
              ...last,
              text: message || 'Something went wrong.',
              streaming: false,
            };
          }
          return updated;
        });
      },
      onDone() {
        flushTokenBuffer();
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === 'assistant') {
            updated[updated.length - 1] = {
              ...last,
              streaming: false,
              toolStatus: undefined,
            };
          }
          return updated;
        });
        setSending(false);
      },
    });
  };

  const handleSend = (e: FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;
    setInput('');
    sendMessage(text);
  };

  const handleAction = (action: { label: string; message: string }) => {
    sendMessage(action.message);
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-2xl mx-auto flex flex-col gap-4">
          {/* Hero for new users / single welcome message */}
          {historyLoaded && messages.length === 1 && messages[0].role === 'assistant' && messages[0].actions && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
              className="flex flex-col items-center justify-center py-16"
            >
              <div className="relative mb-6">
                <div className="w-16 h-16 rounded-2xl bg-accent/8 dark:bg-accent/10 flex items-center justify-center">
                  <MessageSquare className="w-7 h-7 text-accent/70 dark:text-accent-light/70" strokeWidth={1.5} />
                </div>
                <div className="absolute -inset-3 rounded-3xl border border-dashed border-accent/10 dark:border-accent-light/10" />
              </div>
              <h2 className="font-display text-3xl font-semibold mb-2 tracking-tight">What shall we style?</h2>
              <div className="w-10 h-[1.5px] bg-accent/40 mx-auto mb-3" />
              <p className="text-muted text-sm text-center max-w-xs leading-relaxed">
                Outfit ideas, wardrobe advice, or discovering new pieces — I&apos;m here to help curate your look.
              </p>
            </motion.div>
          )}

          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
            >
              {msg.role === 'user' ? (
                <div className="flex justify-end">
                  <div className="bg-gradient-to-r from-accent to-accent-dark text-white px-4 py-3 rounded-2xl rounded-br-md max-w-[80%] text-sm shadow-sm">
                    {msg.text}
                  </div>
                </div>
              ) : (
                <div className="flex flex-col gap-3 max-w-[85%]">
                  {/* Tool status indicator */}
                  {msg.streaming && msg.toolStatus && !msg.text && (
                    <div className="flex items-center gap-2 text-sm text-muted">
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-accent" />
                      {msg.toolStatus}
                    </div>
                  )}

                  {/* Text bubble */}
                  {msg.text && (
                    <div className="bg-white dark:bg-surface-dark-1 border-l-2 border-accent/30 dark:border-accent-light/30 px-4 py-3 rounded-2xl rounded-bl-md text-sm chat-markdown whitespace-pre-wrap shadow-sm">
                      {msg.text}
                      {msg.streaming && (
                        <span className="inline-block w-0.5 h-[1.1em] bg-ink/30 dark:bg-zinc-400/40 ml-0.5 animate-pulse rounded-full align-text-bottom" />
                      )}
                    </div>
                  )}

                  {/* Action buttons */}
                  {msg.actions && msg.actions.length > 0 && !sending && (
                    <div className="flex flex-wrap gap-2 mt-1">
                      {msg.actions.map((action, j) => (
                        <motion.button
                          key={j}
                          initial={{ opacity: 0, y: 6 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: 0.3 + j * 0.1, duration: 0.3 }}
                          onClick={() => handleAction(action)}
                          className={`text-sm font-medium px-4 py-2.5 rounded-xl transition-all duration-200 hover:scale-[1.02] active:scale-95 ${
                            j === 0
                              ? 'bg-gradient-to-r from-accent to-accent-dark text-white shadow-md shadow-accent/20 hover:shadow-lg hover:shadow-accent/30'
                              : 'border border-accent/30 dark:border-accent-light/30 text-accent dark:text-accent-light bg-accent/5 dark:bg-accent-light/5 hover:bg-accent/10 dark:hover:bg-accent-light/10'
                          }`}
                        >
                          {action.label}
                        </motion.button>
                      ))}
                    </div>
                  )}

                  {/* Streaming with no text yet */}
                  {msg.streaming && !msg.text && !msg.toolStatus && (
                    <div className="bg-white dark:bg-surface-dark-1 rounded-2xl rounded-bl-md shadow-sm">
                      <ThinkingDots />
                    </div>
                  )}

                  {/* Products */}
                  {msg.products && msg.products.length > 0 && (
                    <div>
                      <div className="text-xs text-muted mb-2">
                        {msg.products.length} result
                        {msg.products.length !== 1 ? 's' : ''} from Google
                        Shopping
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                        {msg.products.map((p: any, j: number) => (
                          <ProductCard key={j} item={p} index={j} />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Quizzes */}
                  {msg.quizzes?.map((q: any, j: number) => (
                    <QuizBlock key={j} quiz={q} />
                  ))}
                </div>
              )}
            </motion.div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input area */}
      <div className="border-t border-border dark:border-surface-dark-3 backdrop-blur-xl bg-white/80 dark:bg-surface-dark/80 px-4 py-3">
        <form
          onSubmit={handleSend}
          className="max-w-2xl mx-auto flex gap-3 items-end"
        >
          <textarea
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              e.target.style.height = 'auto';
              e.target.style.height =
                Math.min(e.target.scrollHeight, 160) + 'px';
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend(e);
              }
            }}
            placeholder="Ask StyleBot anything..."
            rows={1}
            className="input-field resize-none flex-1"
          />
          <button
            type="submit"
            disabled={sending || !input.trim()}
            className="w-10 h-10 rounded-full bg-accent text-white flex items-center justify-center shrink-0 hover:bg-accent-dark transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-accent/20"
          >
            <ArrowUp className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
}
