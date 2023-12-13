import { describe, it, expect } from 'vitest';
import { extractTextFromPdfFile } from './pdf';

describe('pdf', () => {
  it('should extract the text out of the pdf file', async () => {
    const pdfFilePath = '/Users/hannes.brantner/Downloads/thesis.pdf';
    const pdfFileText = await extractTextFromPdfFile(pdfFilePath);
    expect(pdfFileText).toContain('LLM');
  });
});
