import {
  ApiInterface,
  ApiInterfaceOptions,
  Author,
  Chat,
  ChatMessage,
  Model,
  getDefaultApiInterfaceOptions,
} from '../../interface/interface';
import Replicate from 'replicate';
import { DateTime, Interval } from 'luxon';

export interface ReplicateChatObject {
  prompt: string;
  system_prompt: string;
}

export class ReplicateChat implements Chat {
  private readonly options: Required<ApiInterfaceOptions>;
  private readonly replicate: Replicate;
  private chatMessageHistory: ChatMessage[];

  constructor(options: Required<ApiInterfaceOptions>, replicate: Replicate) {
    this.options = options;
    this.replicate = replicate;
    this.chatMessageHistory = [];
    this.setContext(this.options.systemContext);
  }

  private transformChatMessageToReplicateChatObject(): ReplicateChatObject {
    const prompts: string[] = this.getChatMessageHistory().map(
      (chatMessage) => {
        switch (chatMessage.author) {
          case Author.USER:
            return `[INST] ${chatMessage.text} [/INST]`;
          case Author.MODEL:
            return chatMessage.text;
          default:
            throw new Error();
        }
      }
    );
    return {
      system_prompt: this.getContext()?.text ?? '',
      prompt: prompts.join('\n'),
    };
  }

  setContext(context: string) {
    if (this.chatMessageHistory.length > 0) {
      throw new Error();
    }
    const currentTimestamp = DateTime.now().toUTC();
    const systemChatMessage: ChatMessage = {
      text: context.trim(),
      author: Author.SYSTEM,
      creationDateTime: currentTimestamp,
      generationInterval: Interval.fromDateTimes(
        currentTimestamp,
        currentTimestamp
      ),
    };
    this.chatMessageHistory.push(systemChatMessage);
  }

  getContext(): ChatMessage | undefined {
    return this.chatMessageHistory
      .filter((chatMessage) => chatMessage.author === Author.SYSTEM)
      .pop();
  }

  async sendPrompt(prompt: string): Promise<ChatMessage> {
    const beforeTimestamp = DateTime.now().toUTC();
    const userChatMessage: ChatMessage = {
      text: prompt.trim(),
      author: Author.USER,
      creationDateTime: beforeTimestamp,
      generationInterval: Interval.fromDateTimes(
        beforeTimestamp,
        beforeTimestamp
      ),
    };
    this.chatMessageHistory.push(userChatMessage);
    const outputParts: string[] = (await this.replicate.run(
      this.options.model as `${string}/${string}:${string}`,
      {
        input: {
          ...this.transformChatMessageToReplicateChatObject(),
          debug: this.options.debug,
          top_k: this.options.topTokens,
          top_p: this.options.topProbability,
          temperature: this.options.temperature,
          max_new_tokens: this.options.maxTokens,
          min_new_tokens: this.options.minTokens,
          seed: this.options.seed,
          stop_sequences: this.options.stopSequences
            ?.map((x) => `<${x}>`)
            .join(','),
        },
      }
    )) as string[];
    const afterTimestamp = DateTime.now().toUTC();
    const modelChatMessage: ChatMessage = {
      text: outputParts.join('').trim(),
      author: Author.MODEL,
      creationDateTime: afterTimestamp,
      generationInterval: Interval.fromDateTimes(
        beforeTimestamp,
        afterTimestamp
      ),
    };
    this.chatMessageHistory.push(modelChatMessage);
    return modelChatMessage;
  }

  getChatMessageHistory(includeContext: boolean = false): ChatMessage[] {
    return this.chatMessageHistory.filter(
      (x) => includeContext || x.author !== Author.SYSTEM
    );
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

export class ReplicateApiInterface implements ApiInterface {
  private readonly options: Required<ApiInterfaceOptions>;
  private readonly replicate: Replicate;

  constructor(options: ApiInterfaceOptions) {
    if (![Model.LLAMA_2_70B_CHAT].includes(options.model)) {
      throw new Error();
    }
    this.options = getDefaultApiInterfaceOptions(options);
    this.replicate = new Replicate({
      auth: options.apiKey,
    });
  }

  createChat() {
    return new ReplicateChat(this.options, this.replicate);
  }
}
