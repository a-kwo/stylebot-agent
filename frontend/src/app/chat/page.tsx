'use client';

import { useState, useEffect, useRef, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { getConversations, streamChat } from '@/lib/api';
import ProductCard from '@/components/ProductCard';
import QuizBlock from '@/components/QuizBlock';

interface Message {
  role: 'user' | 'assistant';
  text?: string;
  products?: any[];
  quizzes?: any[];
  toolStatus?: string;
  streaming?: boolean;
}

export default function ChatPage() {
  const router = useRouter();
  const { authenticated, onboarded, loading: authLoading } = useAuth();
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      text: "Hey! I'm StyleBot, your personal styling assistant. What can I help you with today?",
    },
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (authenticated === false) {
      router.replace('/');
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
        if (turns.length === 0) return;

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
            // Meta records hold products/quizzes persisted separately
            const products: any[] = [];
            const quizzes: any[] = [];
            for (const block of msg.content) {
              if (block.type === 'products' && block.products) {
                products.push(...block.products);
              } else if (block.type === 'quiz' && block.quiz) {
                quizzes.push(block.quiz);
              }
            }
            // Attach to the last assistant message
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
      })
      .catch(() => {});
  }, [authenticated, onboarded]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (!authenticated || onboarded !== true) return null;

  const handleSend = (e: FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || sending) return;

    setInput('');
    setSending(true);

    // Add user message + placeholder assistant message
    setMessages((prev) => [
      ...prev,
      { role: 'user', text },
      { role: 'assistant', text: '', streaming: true },
    ]);

    abortRef.current = streamChat(text, {
      onToken(token) {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === 'assistant') {
            updated[updated.length - 1] = {
              ...last,
              text: (last.text || '') + token,
            };
          }
          return updated;
        });
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

  return (
    <div className="flex flex-col h-screen">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-2xl mx-auto flex flex-col gap-4">
          {messages.map((msg, i) => (
            <div key={i}>
              {msg.role === 'user' ? (
                <div className="flex justify-end">
                  <div className="bg-ink text-cream dark:bg-cream dark:text-ink px-4 py-3 rounded-2xl rounded-br-md max-w-[80%] text-sm">
                    {msg.text}
                  </div>
                </div>
              ) : (
                <div className="flex flex-col gap-3 max-w-[85%]">
                  {/* Tool status indicator */}
                  {msg.streaming && msg.toolStatus && !msg.text && (
                    <div className="text-sm text-muted animate-pulse">
                      {msg.toolStatus}
                    </div>
                  )}

                  {/* Text bubble */}
                  {msg.text && (
                    <div className="bg-zinc-100 dark:bg-zinc-800 px-4 py-3 rounded-2xl rounded-bl-md text-sm chat-markdown whitespace-pre-wrap">
                      {msg.text}
                      {msg.streaming && (
                        <span className="inline-block w-1.5 h-4 bg-ink dark:bg-cream ml-0.5 animate-pulse" />
                      )}
                    </div>
                  )}

                  {/* Streaming with no text yet */}
                  {msg.streaming && !msg.text && !msg.toolStatus && (
                    <div className="bg-zinc-100 dark:bg-zinc-800 px-4 py-3 rounded-2xl rounded-bl-md text-sm text-muted animate-pulse">
                      StyleBot is thinking...
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
                          <ProductCard key={j} item={p} />
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
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input area */}
      <div className="border-t border-border dark:border-border-dark bg-white dark:bg-zinc-900 px-4 py-3">
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
            className="btn-primary shrink-0"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
