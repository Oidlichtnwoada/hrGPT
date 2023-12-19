import { describe, it, expect } from 'vitest';
import { Model } from '../../chat/interface/interface';
import { matchJobDescriptionToResumeOrCoverLetter } from './matcher';
import { getAbsolutePathFromRelativeRepoPath } from '../../path/path';

describe('matcher', () => {
  it(
    'should match the applicant documents to the job',
    async () => {
      const jobPdfFilePath = getAbsolutePathFromRelativeRepoPath(
        './libs/utils-lib/src/lib/examples/sample-job-description.pdf'
      );
      const resumePdfFilePath = getAbsolutePathFromRelativeRepoPath(
        './libs/utils-lib/src/lib/examples/sample-job-description.pdf'
      );
      const coverLetterPdfFilePath = getAbsolutePathFromRelativeRepoPath(
        './libs/utils-lib/src/lib/examples/sample-job-description.pdf'
      );
      const matchResult = await matchJobDescriptionToResumeOrCoverLetter(Model.GPT_4_TURBO, jobPdfFilePath, resumePdfFilePath, coverLetterPdfFilePath);
      expect(matchResult).toBeDefined();
      console.log(matchResult);
    },
    { timeout: 60000 }
  );
});
