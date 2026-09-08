import { FinancialResponseData } from './financial';

export type MessageRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  createdAt?: string;
  status?: 'sending' | 'sent' | 'error';
  financialResponse?: FinancialResponseData;
  financialData?: FinancialResponseData;
}

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: string;
  updatedAt: string;
  activeCompany?: string;
  activeTicker?: string;
}


