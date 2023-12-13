import PDFParser from 'pdf2json';

export async function extractTextFromPdfFile(pdfFilePath: string): Promise<string> {
  const pdfParser = new PDFParser(undefined, 1);
  const textPromise = new Promise<string>((resolve, reject) => {
    pdfParser.on('pdfParser_dataError', () => reject(new Error()));
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    pdfParser.on('pdfParser_dataReady', () => resolve((pdfParser as any).getRawTextContent() as string));
  });
  await pdfParser.loadPDF(pdfFilePath);
  return textPromise;
}
