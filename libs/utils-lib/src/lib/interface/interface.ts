import { DateTime, Interval } from 'luxon';

export enum Author {
  USER,
  MODEL,
  SYSTEM,
}

export interface ChatMessage {
  readonly text: string;
  readonly author: Author;
  readonly creationDateTime: DateTime;
  readonly generationInterval: Interval;
}

export interface Chat {
  setContext(context: string): void;
  askQuestion(question: string): Promise<ChatMessage>;
  getChatMessageHistory(): ChatMessage[];
  getUserChatMessageHistory(): ChatMessage[];
  getModelChatMessageHistory(): ChatMessage[];
  getLastUserChatMessage(): ChatMessage | undefined;
  getLastModelChatMessage(): ChatMessage | undefined;
}

export enum Model {
  GPT_4_TURBO = 'gpt-4-1106-preview',
  LLAMA_2_70B_CHAT = '',
}

export interface ApiInterfaceOptions {
  model: Model;
  apiKey: string;
}

export interface ApiInterface {
  createChat(): Chat;
}
