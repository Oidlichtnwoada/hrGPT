import { describe, it, expect } from 'vitest';
import { Model } from '../../chat/interface/interface';
import { getRequirementsFromJobDescriptionPdfFile } from './extractor';
import { getAbsolutePathFromRelativeRepoPath } from '../../path/path';

describe('extractor', () => {
  it(
    'should extract the job requirements',
    async () => {
      const jobDescriptionPdfFilePath = getAbsolutePathFromRelativeRepoPath(
        './libs/utils-lib/src/lib/examples/sample-hr-job-description.pdf'
      );
      const jobRequirements = await getRequirementsFromJobDescriptionPdfFile(
        Model.GPT_4_TURBO,
        jobDescriptionPdfFilePath
      );
      expect(jobRequirements.workExperience.length).toStrictEqual(0);
      expect(jobRequirements.education.length).toStrictEqual(0);
      expect(jobRequirements.otherQualifications.length).toStrictEqual(0);
      expect(jobRequirements.hardSkills.length).toBeGreaterThan(0);
      expect(jobRequirements.hardSkills.join(' ').toLowerCase()).toContain(
        'excel'
      );
      expect(jobRequirements.softSkills.length).toBeGreaterThan(0);
      expect(jobRequirements.softSkills.join(' ').toLowerCase()).toContain(
        'communication skills'
      );
      expect(jobRequirements.specificKnowledge.length).toBeGreaterThan(0);
      expect(
        jobRequirements.specificKnowledge.join(' ').toLowerCase()
      ).toContain('employment law');
      expect(jobRequirements.personalTraits.length).toBeGreaterThan(0);
      expect(jobRequirements.personalTraits.join(' ').toLowerCase()).toContain(
        'confidentiality'
      );
      expect(jobRequirements.languages.length).toStrictEqual(0);
      expect(jobRequirements.travel.length).toStrictEqual(0);
      expect(jobRequirements.location.length).toStrictEqual(0);
      expect(jobRequirements.workingHours.length).toStrictEqual(0);
      expect(jobRequirements.physicalAbility.length).toStrictEqual(0);
      console.log(jobRequirements);
    },
    { timeout: 6000000 }
  );
});
