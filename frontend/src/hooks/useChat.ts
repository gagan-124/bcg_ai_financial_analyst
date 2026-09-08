import { useState, useCallback, useMemo, useRef } from 'react';
import { Conversation, ChatMessage } from '../types';
import {
  analyzeCompany,
  askFinancialQuestion,
  classifyQueryIntent,
  detectKnownCompany,
  mapBackendToFrontendResponse,
  mapBackendQuestionToFrontendVisuals,
} from '../services/analysis';

export const STATIC_SHORTCUT_IDS = ['conv-apple', 'conv-msft', 'conv-tsla'] as const;

const STATIC_COMPANY_PROMPTS: Record<string, string> = {
  'conv-apple': 'Analyze Apple',
  'conv-msft': 'Analyze Microsoft',
  'conv-tsla': 'Analyze Tesla',
};

const INITIAL_CONVERSATIONS: Conversation[] = [
  {
    id: 'conv-apple',
    title: 'Apple Analysis',
    messages: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    activeCompany: 'Apple',
    activeTicker: 'AAPL',
  },
  {
    id: 'conv-msft',
    title: 'Microsoft Analysis',
    messages: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    activeCompany: 'Microsoft',
    activeTicker: 'MSFT',
  },
  {
    id: 'conv-tsla',
    title: 'Tesla Analysis',
    messages: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    activeCompany: 'Tesla',
    activeTicker: 'TSLA',
  },
];

const generateTitle = (text: string): string => {
  const cleaned = text
    .replace(/^(analyze|what are|compare|show|explain)\s+/i, '')
    .trim();
  const capitalized = cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
  return capitalized.length > 28 ? capitalized.slice(0, 28) + '...' : capitalized;
};

export interface UseChatReturn {
  conversations: Conversation[];
  activeConversationId: string | null;
  activeConversation: Conversation | null;
  currentMessages: ChatMessage[];
  isSubmitting: boolean;
  createNewChat: () => void;
  selectConversation: (id: string) => void;
  sendMessage: (content: string, overrideTargetId?: string) => Promise<void>;
  deleteConversation: (id: string) => void;
}

export const useChat = (): UseChatReturn => {
  const [conversations, setConversations] = useState<Conversation[]>(INITIAL_CONVERSATIONS);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  // Maintain ref to ensure async handlers always access latest conversation state
  const conversationsRef = useRef<Conversation[]>(conversations);
  conversationsRef.current = conversations;

  const activeConversation = useMemo(() => {
    if (!activeConversationId) return null;
    return conversations.find((c) => c.id === activeConversationId) ?? null;
  }, [conversations, activeConversationId]);

  const currentMessages = useMemo(() => {
    return activeConversation ? activeConversation.messages : [];
  }, [activeConversation]);

  const createNewChat = useCallback(() => {
    setActiveConversationId(null);
  }, []);

  const sendMessage = useCallback(
    async (content: string, overrideTargetId?: string): Promise<void> => {
      const timestamp = new Date().toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      });

      const userMessage: ChatMessage = {
        id: `msg-${Date.now()}-user`,
        role: 'user',
        content,
        createdAt: timestamp,
        status: 'sent',
      };

      let targetId = overrideTargetId || activeConversationId;
      const targetConv = targetId
        ? conversationsRef.current.find((c) => c.id === targetId)
        : undefined;

      // Determine active company from conversation metadata or prior financial messages
      let currentActiveCompany = targetConv?.activeCompany;
      if (!currentActiveCompany && targetConv) {
        for (let i = targetConv.messages.length - 1; i >= 0; i--) {
          const msg = targetConv.messages[i];
          if (msg.financialResponse?.title) {
            const found = detectKnownCompany(msg.financialResponse.title);
            if (found) {
              currentActiveCompany = found;
              break;
            }
          }
        }
      }

      if (!targetId) {
        // Create new local conversation on first message in a fresh chat
        targetId = `conv-${Date.now()}`;
        const newConversation: Conversation = {
          id: targetId,
          title: generateTitle(content) || 'Financial Analysis',
          messages: [userMessage],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };

        setConversations((prev) => [newConversation, ...prev]);
        setActiveConversationId(targetId);
      } else {
        // Append user message to existing active conversation
        setConversations((prev) =>
          prev.map((conv) => {
            if (conv.id === targetId) {
              return {
                ...conv,
                messages: [...conv.messages, userMessage],
                updatedAt: new Date().toISOString(),
              };
            }
            return conv;
          })
        );
      }

      setIsSubmitting(true);

      try {
        const classification = classifyQueryIntent(content, currentActiveCompany);

        if (classification.intent === 'question') {
          const tFollowUpStart = performance.now();
          console.log(`[FRONTEND CHAT] Question flow started: "${content}" for ${classification.company}`);

          // Route follow-up financial questions to the Gemini question layer
          const questionResponse = await askFinancialQuestion(
            classification.company,
            content
          );

          // Build structured visuals (chart/table/metrics) if returned by backend
          const questionVisuals = mapBackendQuestionToFrontendVisuals(questionResponse);

          const assistantMessage: ChatMessage = {
            id: `msg-${Date.now()}-assistant`,
            role: 'assistant',
            content: questionResponse.answer,
            financialResponse: questionVisuals,
            financialData: questionVisuals,
            createdAt: new Date().toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            }),
            status: 'sent',
          };

          setConversations((prev) =>
            prev.map((conv) => {
              if (conv.id === targetId) {
                return {
                  ...conv,
                  activeCompany: conv.activeCompany || questionResponse.company.name,
                  activeTicker: conv.activeTicker || questionResponse.company.ticker,
                  messages: [...conv.messages, assistantMessage],
                  updatedAt: new Date().toISOString(),
                };
              }
              return conv;
            })
          );
          const tFollowUpEnd = performance.now();
          console.log(
            `[FRONTEND CHAT] Question flow rendered in ${(tFollowUpEnd - tFollowUpStart).toFixed(1)} ms`
          );
        } else {
          // Route company analysis requests to /api/analysis and render full overview
          const backendData = await analyzeCompany(classification.company, content);
          const financialResponse = mapBackendToFrontendResponse(backendData);

          const assistantMessage: ChatMessage = {
            id: `msg-${Date.now()}-assistant`,
            role: 'assistant',
            content: backendData.summary,
            financialResponse,
            financialData: financialResponse,
            createdAt: new Date().toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            }),
            status: 'sent',
          };

          setConversations((prev) =>
            prev.map((conv) => {
              if (conv.id === targetId) {
                return {
                  ...conv,
                  activeCompany: backendData.company.name,
                  activeTicker: backendData.company.ticker,
                  messages: [...conv.messages, assistantMessage],
                  updatedAt: new Date().toISOString(),
                };
              }
              return conv;
            })
          );
        }
      } catch (err: unknown) {
        const errorMsg =
          err instanceof Error ? err.message : 'Failed to process financial query.';
        const isUnsupported = errorMsg.includes('Unsupported company');
        const isNetworkError =
          errorMsg.toLowerCase().includes('failed to fetch') ||
          errorMsg.toLowerCase().includes('networkerror');

        const displayContent = isUnsupported
          ? `${errorMsg}\n\nSupported companies: Apple (AAPL), Microsoft (MSFT), and Tesla (TSLA).`
          : isNetworkError
          ? 'Unable to connect to the BCG financial backend server. Please verify that the backend is running.'
          : errorMsg;

        const assistantErrorMessage: ChatMessage = {
          id: `msg-${Date.now()}-error`,
          role: 'assistant',
          content: displayContent,
          createdAt: new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          }),
          status: 'error',
        };

        setConversations((prev) =>
          prev.map((conv) => {
            if (conv.id === targetId) {
              return {
                ...conv,
                messages: [...conv.messages, assistantErrorMessage],
                updatedAt: new Date().toISOString(),
              };
            }
            return conv;
          })
        );
      } finally {
        setIsSubmitting(false);
      }
    },
    [activeConversationId]
  );

  const selectConversation = useCallback(
    (id: string) => {
      setActiveConversationId(id);
      const target = conversations.find((c) => c.id === id);
      // If a static shortcut is selected and has no messages, run analysis through the single pipeline
      if (target && target.messages.length === 0) {
        const prompt = STATIC_COMPANY_PROMPTS[id];
        if (prompt) {
          void sendMessage(prompt, id);
        }
      }
    },
    [conversations, sendMessage]
  );

  const deleteConversation = useCallback((id: string) => {
    // Protect static analysis shortcuts from deletion
    if ((STATIC_SHORTCUT_IDS as readonly string[]).includes(id)) {
      return;
    }

    setConversations((prev) => prev.filter((conv) => conv.id !== id));
    setActiveConversationId((prevActive) => (prevActive === id ? null : prevActive));
  }, []);

  return {
    conversations,
    activeConversationId,
    activeConversation,
    currentMessages,
    isSubmitting,
    createNewChat,
    selectConversation,
    sendMessage,
    deleteConversation,
  };
};

export default useChat;
