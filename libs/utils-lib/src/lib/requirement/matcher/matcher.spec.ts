import { describe, it, expect } from 'vitest';
import { Model } from '../../chat/interface/interface';
import { matchJobDescriptionToResumeOrCoverLetter } from './matcher';
import { getAbsolutePathFromRelativeRepoPath } from '../../path/path';

describe('matcher', () => {
  it(
    'should match the applicant documents to the job',
    async () => {
      const jobDescriptionPdfFilePath = getAbsolutePathFromRelativeRepoPath(
        './libs/utils-lib/src/lib/examples/sample-software-job-description.pdf'
      );
      const resumePdfFilePath = getAbsolutePathFromRelativeRepoPath(
        './libs/utils-lib/src/lib/examples/sample-software-resume.pdf'
      );
      const matchResult = await matchJobDescriptionToResumeOrCoverLetter(Model.GPT_4_TURBO, jobDescriptionPdfFilePath, resumePdfFilePath, undefined);
      expect(matchResult).toBeDefined();
      console.log(matchResult);
    },
    { timeout: 60000 }
  );
});
