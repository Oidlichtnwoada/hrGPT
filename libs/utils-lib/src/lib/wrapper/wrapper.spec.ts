import { Model } from '../interface/interface';
import { getChat } from './wrapper';

describe('wrapper', () => {
  it('should get a valid chat', () => {
    const openaiChat = getChat({ model: Model.GPT_4_TURBO });
    const replicateChat = getChat({ model: Model.LLAMA_2_70B_CHAT });
    expect(openaiChat).toBeDefined();
    expect(replicateChat).toBeDefined();
  });
});
