import { describe, it, expect } from 'vitest';
import { extractTextFromPdfFile } from './pdf';
import { getAbsolutePathFromRelativeRepoPath } from '../path/path';

describe('pdf', () => {
  it('should extract the text out of the pdf file', async () => {
    const pdfFilePath = getAbsolutePathFromRelativeRepoPath(
      './libs/utils-lib/src/lib/examples/sample-job-description.pdf'
    );
    const pdfFileText = await extractTextFromPdfFile(pdfFilePath);
    expect(pdfFileText).toContain('Human Resources Assistant');
    expect(pdfFileText.length).toBeGreaterThan(1000);
  });
});
