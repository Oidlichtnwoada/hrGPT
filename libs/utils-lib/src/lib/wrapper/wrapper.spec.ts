import { Model } from '../interface/interface';
import { getChat } from './wrapper';

describe('wrapper', () => {
  it('should get a valid chat for any api', async () => {
    const name = 'John Doe';
    const age = 42;
    const openaiChat = getChat({ model: Model.GPT_4_TURBO });
    const replicateChat = getChat({ model: Model.LLAMA_2_70B_CHAT });
    const chats = [openaiChat, replicateChat];
    for (const chat of chats) {
      const chatFirstResponse = await chat.askQuestion(`Hello, my name is ${name} and I am ${age} years old. What is your name?`);
      expect(chatFirstResponse.text.length).toBeGreaterThan(0);
      const chatSecondResponse = await chat.askQuestion('Ok, I understand. Do you remember what my name was?');
      expect(chatSecondResponse.text).toContain(name);
      const chatThirdResponse = await chat.askQuestion('Ok, I understand. Do you remember what my age was?');
      expect(chatThirdResponse.text).toContain(`${age}`);
      console.log(chat.getChatMessageHistory(false));
    }
  }, {timeout: 60000});
});
