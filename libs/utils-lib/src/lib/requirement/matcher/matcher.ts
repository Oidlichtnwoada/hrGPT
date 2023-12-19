import { Model } from '../../chat/interface/interface';
import {
  getRequirementsFromJobDescriptionPdfFile,
  Requirements,
  RequirementTypeDefinitions
} from '../extractor/extractor';
import { extractTextFromPdfFile } from '../../pdf/pdf';
import { getChat } from '../../chat/wrapper/wrapper';
import extract from '@airthium/extract-json-from-string';

export interface RequirementScore {
  requirement: string;
  score: number;
  explanation: string;
}

export const EmptyRequirementScore = {
  requirement: '',
  score: 0,
  explanation: ''
};

export interface MatchResult {
  readonly score: number;
  readonly promising: boolean;
  readonly workExperience: RequirementScore[];
  readonly education: RequirementScore[];
  readonly otherQualifications: RequirementScore[];
  readonly hardSkills: RequirementScore[];
  readonly softSkills: RequirementScore[];
  readonly specificKnowledge: RequirementScore[];
  readonly personalTraits: RequirementScore[];
  readonly languages: RequirementScore[];
  readonly travel: RequirementScore[];
  readonly location: RequirementScore[];
  readonly workingHours: RequirementScore[];
  readonly physicalAbility: RequirementScore[];
}

export const EmptyMatchResult: MatchResult = {
  score: 0,
  promising: false,
  workExperience: [],
  education: [],
  otherQualifications: [],
  hardSkills: [],
  softSkills: [],
  specificKnowledge: [],
  personalTraits: [],
  languages: [],
  travel: [],
  location: [],
  workingHours: [],
  physicalAbility: []
};

export function getPromptToMatchRequirement(requirement: string, requirementType: keyof Requirements, resumeText: string | undefined, coverLetterText: string | undefined): string {
  let prompt = `Please match the requirement from the following JSON object ${JSON.stringify({
    ...EmptyRequirementScore,
    requirement: requirement
  })} with the provided application documents and fill the score and the explanation in the JSON object. The score should be 0 if the requirement is completely unfulfilled and 100 if the requirement is fully covered. Assign a score between 0 and 100 if the requirement is only partially covered and a higher score means a higher degree of coverage. A description of the type of requirement is provided here: ${JSON.stringify(RequirementTypeDefinitions[requirementType])}. Explain the chosen score with the explanation field in the JSON object. `;
  if (resumeText) {
    prompt += `Here is the resume for which the described requirement should be scored and explained: ${resumeText}. `;
  }
  if (coverLetterText) {
    prompt += `Here is the cover letter for which the described requirement should be scored and explained: ${coverLetterText}. `;
  }
  return prompt.trim();
}

export async function matchJobDescriptionToResumeOrCoverLetter(
  model: Model,
  jobDescriptionPdfFilePath: string,
  resumePdfFilePath?: string,
  coverLetterPdfFilePath?: string
): Promise<MatchResult> {
  if (!resumePdfFilePath && !coverLetterPdfFilePath) {
    throw Error();
  }
  const jobRequirements = await getRequirementsFromJobDescriptionPdfFile(model, jobDescriptionPdfFilePath);
  const resumeText = resumePdfFilePath ? await extractTextFromPdfFile(resumePdfFilePath) : undefined;
  const coverLetterText = coverLetterPdfFilePath ? await extractTextFromPdfFile(coverLetterPdfFilePath) : undefined;
  const matchResult = { ...EmptyMatchResult };
  for (const requirementType of Object.keys(RequirementTypeDefinitions)) {
    for (const requirement of jobRequirements[requirementType as keyof Requirements]) {
      const prompt = getPromptToMatchRequirement(requirement, requirementType as keyof Requirements, resumeText, coverLetterText);
      const chat = getChat({ model: model });
      const answer = await chat.sendPrompt(prompt);
      const extractedJsonObjects: object[] = extract(answer.text).filter(
        (x: unknown) => !Array.isArray(x)
      );
      const firstExtractedJsonObject: object = extractedJsonObjects.at(0) ?? {};
      const requirementScore = { ...EmptyRequirementScore, ...firstExtractedJsonObject, requirement: requirement };
      requirementScore.score = Math.min(Math.max(requirementScore.score, 0), 100);
      matchResult[requirementType as keyof Requirements].push(requirementScore);
    }
  }
  return matchResult;
}
