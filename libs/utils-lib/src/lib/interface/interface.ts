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
  getContext(): ChatMessage | undefined;
  askQuestion(question: string): Promise<ChatMessage>;
  getChatMessageHistory(includeContext: boolean): ChatMessage[];
  getUserChatMessageHistory(): ChatMessage[];
  getModelChatMessageHistory(): ChatMessage[];
  getLastUserChatMessage(): ChatMessage | undefined;
  getLastModelChatMessage(): ChatMessage | undefined;
}

export enum Model {
  GPT_4_TURBO = 'gpt-4-1106-preview',
  LLAMA_2_70B_CHAT = 'meta/llama-2-70b-chat:02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3',
}

export interface ApiInterfaceOptions {
  model: Model;
  apiKey: string;
  temperature?: number;
  stopSequences?: string[];
  seed?: number;
  topProbability?: number;
  topTokens?: number;
  maxTokens?: number;
  minTokens?: number;
  debug?: boolean;
  systemContext?: string;
  choices?: number;
  frequencyPenalty?: number;
  logitBias?: Record<string, number>;
  presencePenalty?: number;
}

export function getDefaultApiInterfaceOptions(
  options: ApiInterfaceOptions
): Required<ApiInterfaceOptions> {
  return {
    presencePenalty: 0,
    logitBias: {},
    frequencyPenalty: 0,
    choices: 1,
    systemContext: 'You are a helpful assistant.',
    debug: false,
    minTokens: 0,
    maxTokens: 1_000_000,
    topTokens: 50,
    topProbability: 1,
    seed: Math.round(Math.random() * Number.MAX_SAFE_INTEGER),
    stopSequences: [],
    temperature: 1,
    ...options,
  };
}

export interface ApiInterface {
  createChat(): Chat;
}
