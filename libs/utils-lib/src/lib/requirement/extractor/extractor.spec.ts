import { Model } from '../../chat/interface/interface';
import { getRequirementsFromJobDescriptionPdfFile } from './extractor';
import { getAbsolutePathFromRelativeRepoPath } from '../../path/path';

describe('extractor', () => {
  it(
    'should extract the job requirements',
    async () => {
      const jobPdfFilePath = getAbsolutePathFromRelativeRepoPath(
        './libs/utils-lib/src/lib/requirement/extractor/pdf-examples/sample-job-description.pdf'
      );
      const jobRequirements = getRequirementsFromJobDescriptionPdfFile(
        jobPdfFilePath,
        Model.GPT_4_TURBO
      );
      expect((await jobRequirements).workExperience.length).toStrictEqual(0);
      expect((await jobRequirements).education.length).toStrictEqual(0);
      expect((await jobRequirements).otherQualifications.length).toStrictEqual(
        0
      );
      expect((await jobRequirements).hardSkills.length).toStrictEqual(0);
      expect((await jobRequirements).softSkills.length).toStrictEqual(0);
      expect((await jobRequirements).specificKnowledge.length).toStrictEqual(0);
      expect((await jobRequirements).personalTraits.length).toStrictEqual(0);
      expect((await jobRequirements).languages.length).toStrictEqual(0);
      expect((await jobRequirements).travel.length).toStrictEqual(0);
      expect((await jobRequirements).jobLocation.length).toStrictEqual(0);
      expect((await jobRequirements).workingHours.length).toStrictEqual(0);
      expect((await jobRequirements).physicalAbility.length).toStrictEqual(0);
    },
    { timeout: 60000 }
  );
});
