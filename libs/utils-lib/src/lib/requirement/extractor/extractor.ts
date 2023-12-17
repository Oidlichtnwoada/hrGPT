import { Model } from '../../chat/interface/interface';
import { getChat } from '../../chat/wrapper/wrapper';
import { extractTextFromPdfFile } from '../../pdf/pdf';
import extract from 'extract-json-from-string';

export interface Requirements {
  readonly workExperience: string[];
  readonly education: string[];
  readonly otherQualifications: string[];
  readonly hardSkills: string[];
  readonly softSkills: string[];
  readonly specificKnowledge: string[];
  readonly personalTraits: string[];
  readonly languages: string[];
  readonly travel: string[];
  readonly jobLocation: string[];
  readonly workingHours: string[];
  readonly physicalAbility: string[];
}

const RequirementTypeDefinitions: Record<keyof Requirements, string> = {
  workExperience:
    'Work experience requirements relate to the previous roles you have worked and the amount of time you have spent in each role. Employers use this job requirement to attract candidates with a certain amount or type of work experience and may seek employees who have worked in similar positions. Other employers may not require candidates to have previous experience, making the role it suitable for candidates who are just entering the workforce, recently graduated, or changing careers. If you have unrelated work experience, you can include the transferable skills gained in those roles to help demonstrate your suitability for the position on your resume.',
  education:
    "Some positions require candidates to have a certain level of education, such as a high school diploma, a bachelor's degree, or a graduate degree. Depending on the employer and the position, some educational requirements may outline vocational training, especially for hands-on and manual roles such as plumbing or electrician jobs. Employers may also specify the areas of study required of prospective candidates, such as the major they prefer. In other instances, employers may substitute some or all the educational requirements with the length of work experience in a particular industry or role.",
  otherQualifications:
    "Some roles require candidates to be licensed before qualifying for paid positions. Employers hiring for such positions typically state that candidates need licensing to operate in a specific jurisdiction. For instance, to work as a counselling psychologist, you require licensing by the respective provincial licensing body. Some positions also require candidates to undergo certification. Certification shows that a candidate has the requisite work experience and skills to perform in a role. Maintaining certifications shows a candidate's commitment to the profession, an aspect that's likely to further impress the employer. This point also included accreditations.",
  hardSkills:
    "When employers look for candidates to fill open positions, they typically outline the hard skills required. Every position requires unique hard skills. Hard skills are technical skills necessary to perform the job. For example, hard skills for a nursing position include knowledge of medical terminologies or the ability to execute doctor's instructions.",
  softSkills:
    'When employers look for candidates to fill open positions, they typically outline the soft skills required. Every position requires unique soft skills. Soft skills entail the ability of a candidate to relate well to others. For example, soft skills can involve teamwork and communication skills.',
  specificKnowledge:
    'Some roles require a candidate to possess more knowledge of specific areas relevant to the open position. Employers may specify these knowledge areas to attract candidates with a certain knowledge base and skill set. For instance, employers looking to hire a phlebotomist may require candidates to have knowledge of venipuncture.',
  personalTraits:
    "A candidate's personality is a key job requirement for some positions. Having the desired personality traits can make a candidate more suitable for a position and complements their skills, education, and work experience. Employers may consider personality traits as critical in enabling a candidate to fit into the company's culture, values, and ability to work harmoniously with others. Some desirable personality traits employers may look for include attention to detail, reliability, creativity, general intelligence and a desire to learn.",
  languages:
    'Employers looking to hire for a role that involves working with a diverse population may require job candidates to be proficient in certain languages. Employers may also specify the level of language proficiency, such as the ability to write and speak fluently. In some cases, basic knowledge of the language may be sufficient to perform the role, while other roles may have no language requirement at all.',
  travel:
    'Some positions require a lot of travelling apart from commuting. This requirement is typical for organizations with field operations, companies with offices in multiple locations, or those undertaking geographically dispersed projects. Employers hiring for such positions can state these requirements in the job posting to help attract candidates willing to travel outside their usual location.',
  jobLocation:
    'Employers hiring for open positions typically intend for the successful candidate to work in a specific location such as the head office, regional offices, or international subsidiaries. Job location is an important job requirement, as stating it can help find candidates able to work in certain places. For instance, candidates with young families may reconsider applying for international positions because of the potential disruption to their lives. Job positions may be on-site, remote or hybrid.',
  workingHours:
    'Sometimes a job entails working very long hours or working on weekends. This is often the case for people in the medical or law field, but also for positions in business administration, like a sales manager or C-suite role. This point also considers the total work amount which can either be part-time, full-time or contract work',
  physicalAbility:
    'Some positions may involve a high physical demand. These include positions in the army, machine operator, or nursing assistant as they typically involve spending long periods of time standing, moving, or lifting heavy objects. Employers hiring for such positions usually specify that candidates be physically fit so they can effectively complete their tasks.',
};

export const EmptyRequirements: Requirements = {
  workExperience: [],
  education: [],
  otherQualifications: [],
  hardSkills: [],
  softSkills: [],
  specificKnowledge: [],
  personalTraits: [],
  languages: [],
  travel: [],
  jobLocation: [],
  workingHours: [],
  physicalAbility: [],
};

export function getPromptToExtractRequirements(jobDescription: string): string {
  return `Please extract the job requirements from the following job description as a JSON object and fill the requirements into the arrays in ${EmptyRequirements} but respect the type of the requirement. An explanation how to fill the arrays with the requirements of the correct type is provided in ${RequirementTypeDefinitions}, but if there are no suitable requirements for this category, the arrays can stay empty. Here is the job description from which the described JSON object should be extracted: ${jobDescription.trim()}`;
}

export async function getRequirementsFromJobDescriptionPdfFile(
  pdfFilePath: string,
  model: Model
): Promise<Requirements> {
  const jobDescriptionText = await extractTextFromPdfFile(pdfFilePath);
  const prompt = getPromptToExtractRequirements(jobDescriptionText);
  const chat = getChat({ model: model });
  const answer = await chat.sendPrompt(prompt);
  const extractedJsonObjects: object[] = extract(answer.text).filter(
    (x: unknown) => !Array.isArray(x)
  );
  const firstExtractedJsonObject: object = extractedJsonObjects.at(0) ?? {};
  return {
    ...EmptyRequirements,
    ...firstExtractedJsonObject,
  };
}
