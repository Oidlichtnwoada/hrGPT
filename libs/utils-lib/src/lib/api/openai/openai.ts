import {
  ApiInterface,
  ApiInterfaceOptions,
  Author,
  Chat,
  ChatMessage,
  Model,
} from '../../interface/interface';
import OpenAI from 'openai';
import { DateTime, Interval } from 'luxon';

export enum OpenaiRole {
  USER = 'user',
  ASSISTANT = 'assistant',
  SYSTEM = 'system',
}

export interface OpenaiChatMessage {
  role: OpenaiRole;
  content: string;
}

export class OpenaiChat implements Chat {
  private readonly options: ApiInterfaceOptions;
  private readonly openai: OpenAI;
  private chatMessageHistory: ChatMessage[];

  constructor(options: ApiInterfaceOptions, openai: OpenAI) {
    this.options = options;
    this.openai = openai;
    this.chatMessageHistory = [];
  }

  private transformChatMessageToOpenaiChatMessage(
    chatMessage: ChatMessage
  ): OpenaiChatMessage {
    return {
      role:
        chatMessage.author === Author.USER
          ? OpenaiRole.USER
          : chatMessage.author === Author.MODEL
          ? OpenaiRole.ASSISTANT
          : OpenaiRole.SYSTEM,
      content: chatMessage.text,
    };
  }

  setContext(context: string) {
    if (this.chatMessageHistory.length > 0) {
      throw new Error();
    }
    const currentTimestamp = DateTime.now().toUTC();
    const systemChatMessage: ChatMessage = {
      text: context,
      author: Author.SYSTEM,
      creationDateTime: currentTimestamp,
      generationInterval: Interval.fromDateTimes(
        currentTimestamp,
        currentTimestamp
      ),
    };
    this.chatMessageHistory.push(systemChatMessage);
  }

  async askQuestion(question: string): Promise<ChatMessage> {
    const beforeTimestamp = DateTime.now().toUTC();
    const userChatMessage: ChatMessage = {
      text: question,
      author: Author.USER,
      creationDateTime: beforeTimestamp,
      generationInterval: Interval.fromDateTimes(
        beforeTimestamp,
        beforeTimestamp
      ),
    };
    this.chatMessageHistory.push(userChatMessage);
    const modelResponse = await this.openai.chat.completions.create({
      model: this.options.model,
      messages: this.chatMessageHistory.map(
        this.transformChatMessageToOpenaiChatMessage
      ),
    });
    const afterTimestamp = DateTime.now().toUTC();
    const modelResponseChoice = modelResponse.choices[0];
    if (
      modelResponseChoice.message.content === null ||
      modelResponseChoice.finish_reason != 'stop'
    ) {
      throw new Error();
    }
    const modelChatMessage: ChatMessage = {
      text: modelResponseChoice.message.content,
      author: Author.MODEL,
      creationDateTime: DateTime.fromSeconds(modelResponse.created).toUTC(),
      generationInterval: Interval.fromDateTimes(
        beforeTimestamp,
        afterTimestamp
      ),
    };
    this.chatMessageHistory.push(modelChatMessage);
    return modelChatMessage;
  }

  getChatMessageHistory(): ChatMessage[] {
    return this.chatMessageHistory;
  }
  getUserChatMessageHistory(): ChatMessage[] {
    return this.chatMessageHistory.filter(
      (chatMessage) => chatMessage.author === Author.USER
    );
  }
  getModelChatMessageHistory(): ChatMessage[] {
    return this.chatMessageHistory.filter(
      (chatMessage) => chatMessage.author === Author.MODEL
    );
  }
  getLastUserChatMessage(): ChatMessage | undefined {
    return this.chatMessageHistory
      .filter((chatMessage) => chatMessage.author === Author.USER)
      .pop();
  }
  getLastModelChatMessage(): ChatMessage | undefined {
    return this.chatMessageHistory
      .filter((chatMessage) => chatMessage.author === Author.MODEL)
      .pop();
  }
}

export class OpenaiApiInterface implements ApiInterface {
  private readonly options: ApiInterfaceOptions;
  private readonly openai: OpenAI;

  constructor(options: ApiInterfaceOptions) {
    if (![Model.GPT_4_TURBO].includes(options.model)) {
      throw new Error();
    }
    this.options = options;
    this.openai = new OpenAI({ apiKey: options.apiKey });
  }

  createChat() {
    return new OpenaiChat(this.options, this.openai);
  }
}
