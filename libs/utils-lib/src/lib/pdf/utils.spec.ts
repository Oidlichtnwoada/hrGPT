import { extractTextFromPdfFile } from './utils';

describe('pdf', () => {
  it('should extract the text out of the pdf file', async () => {
    const pdfFilePath = 'thesisddd.pdf';
    const pdfFileText = await extractTextFromPdfFile(pdfFilePath);
    expect(pdfFileText).toContain('This is the title of my thesis');
  });
});
