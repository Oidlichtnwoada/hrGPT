import * as fs from 'fs';
import * as pdf from 'pdf-parse';

export async function convertPdfFileToText(pdfFilePath: string): Promise<string> {
  const pdfFileBuffer = fs.readFileSync(pdfFilePath);
  const pdfFileResult = await pdf(pdfFileBuffer);
  return pdfFileResult.text;
}
