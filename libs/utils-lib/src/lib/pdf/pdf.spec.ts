import { describe, it, expect } from 'vitest';
import { extractTextFromPdfFile } from './pdf';
import { getAbsolutePathFromRelativeRepoPath } from '../path/path';

describe('pdf', () => {
  it('should extract the text out of the pdf file', async () => {
    const pdfFilePath = getAbsolutePathFromRelativeRepoPath(
      './thesis/thesis.pdf'
    );
    const pdfFileText = await extractTextFromPdfFile(pdfFilePath);
    expect(pdfFileText).toContain('Hannes Brantner');
    expect(pdfFileText.length).toBeGreaterThan(10000);
  });
});
