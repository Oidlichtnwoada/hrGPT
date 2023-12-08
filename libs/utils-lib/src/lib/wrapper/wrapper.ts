import { OpenaiApiInterface } from '../api/openai/openai';
import { ReplicateApiInterface } from '../api/replicate/replicate';
import {
  ApiInterface,
  ApiInterfaceOptions,
  Chat,
  Model,
} from '../interface/interface';
import * as dotenv from 'dotenv';

export function getChat(options: Omit<ApiInterfaceOptions, 'apiKey'>): Chat {
  dotenv.config();
  let apiInterface: ApiInterface;
  switch (options.model) {
    case Model.GPT_4_TURBO:
      apiInterface = new OpenaiApiInterface({ apiKey: '', ...options });
      break;
    case Model.LLAMA_2_70B_CHAT:
      apiInterface = new ReplicateApiInterface({ apiKey: '', ...options });
      break;
    default:
      throw new Error();
  }
  return apiInterface.createChat();
}
