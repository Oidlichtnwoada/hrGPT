import { describe, it, expect } from 'vitest';
import { Model } from '../../chat/interface/interface';
import { getRequirementsFromJobDescriptionPdfFile } from './extractor';
import { getAbsolutePathFromRelativeRepoPath } from '../../path/path';

describe('extractor', () => {
  it(
    'should extract the job requirements',
    async () => {
      const jobPdfFilePath = getAbsolutePathFromRelativeRepoPath(
        './libs/utils-lib/src/lib/examples/sample-job-description.pdf'
      );
      const jobRequirements = await getRequirementsFromJobDescriptionPdfFile(
        jobPdfFilePath,
        Model.GPT_4_TURBO
      );
      expect(jobRequirements.workExperience.length).toStrictEqual(0);
      expect(jobRequirements.education.length).toStrictEqual(0);
      expect(jobRequirements.otherQualifications.length).toStrictEqual(0);
      expect(jobRequirements.hardSkills.length).toBeGreaterThan(0);
      expect(jobRequirements.softSkills.length).toBeGreaterThan(0)
      expect(jobRequirements.specificKnowledge.length).toBeGreaterThan(0)
      expect(jobRequirements.personalTraits.length).toBeGreaterThan(0)
      expect(jobRequirements.languages.length).toStrictEqual(0);
      expect(jobRequirements.travel.length).toStrictEqual(0);
      expect(jobRequirements.jobLocation.length).toStrictEqual(0);
      expect(jobRequirements.workingHours.length).toStrictEqual(0);
      expect(jobRequirements.physicalAbility.length).toStrictEqual(0);
    },
    { timeout: 60000 }
  );
});
