import { Model } from '../interface/interface';
import { getChat } from './wrapper';

describe('wrapper', () => {
  it('should get a valid chat for any api', async () => {
    const name = 'John';
    const openaiChat = getChat({ model: Model.GPT_4_TURBO });
    const replicateChat = getChat({ model: Model.LLAMA_2_70B_CHAT });
    const chats = [openaiChat, replicateChat];
    for (const chat of chats) {
      const chatFirstResponse = await chat.askQuestion(`Hello, my name in ${name}. What is your name?`);
      expect(chatFirstResponse.text.length).toBeGreaterThan(0);
      const chatSecondResponse = await chat.askQuestion('Do you remember what my name was?');
      expect(chatSecondResponse.text).toContain(name);
      console.log(chat.getChatMessageHistory(false));
    }
  }, {timeout: 60000});
});
