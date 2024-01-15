import dataclasses
import enum
import json

import fitz

from hrgpt.chat.chat_factory import get_answer_message
from hrgpt.utils import dumps


class RequirementType(enum.Enum):
    MANDATORY = 'mandatory'
    OPTIONAL = 'optional'


@dataclasses.dataclass(order=True, frozen=True, kw_only=True)
class Requirement:
    type: str
    specification: str


DEFAULT_REQUIREMENT_TYPE_DEFINITIONS: dict[str, str] = {
    'work_experience':
        'Work experience requirements relate to the previous roles you have worked and the amount of time you have spent in each role. Employers use this job requirement to attract candidates with a certain amount or type of work experience and may seek employees who have worked in similar positions. Other employers may not require candidates to have previous experience, making the role it suitable for candidates who are just entering the workforce, recently graduated, or changing careers. If you have unrelated work experience, you can include the transferable skills gained in those roles to help demonstrate your suitability for the position on your CV or resume.',
    'education':
        'Some positions require candidates to have a certain level of education, such as a high school diploma, a bachelor\'s degree, or a graduate degree. Depending on the employer and the position, some educational requirements may outline vocational training, especially for hands-on and manual roles such as plumbing or electrician jobs. Employers may also specify the areas of study required of prospective candidates, such as the major they prefer. In other instances, employers may substitute some or all the educational requirements with the length of work experience in a particular industry or role.',
    'other_qualifications':
        'Some roles require candidates to be licensed before qualifying for paid positions. Employers hiring for such positions typically state that candidates need licensing to operate in a specific jurisdiction. For instance, to work as a counselling psychologist, you require licensing by the respective provincial licensing body. Some positions also require candidates to undergo certification. Certification shows that a candidate has the requisite work experience and skills to perform in a role. Maintaining certifications shows a candidate\'s commitment to the profession, an aspect that\'s likely to further impress the employer. This point also included accreditations.',
    'hard_skills':
        'When employers look for candidates to fill open positions, they typically outline the hard skills required. Every position requires unique hard skills. Hard skills are technical skills necessary to perform the job. For example, hard skills for a nursing position include knowledge of medical terminologies or the ability to execute doctor\'s instructions.',
    'soft_skills':
        'When employers look for candidates to fill open positions, they typically outline the soft skills required. Every position requires unique soft skills. Soft skills entail the ability of a candidate to relate well to others. For example, soft skills can involve teamwork and communication skills.',
    'specific_knowledge':
        'Some roles require a candidate to possess more knowledge of specific areas relevant to the open position. Employers may specify these knowledge areas to attract candidates with a certain knowledge base and skill set. For instance, employers looking to hire an electric car mechanic may require candidates to have knowledge of high voltage batteries.',
    'personal_traits':
        'A candidate\'s personality is a key job requirement for some positions. Having the desired personality traits can make a candidate more suitable for a position and complements their skills, education, and work experience. Employers may consider personality traits as critical in enabling a candidate to fit into the company\'s culture, values, and ability to work harmoniously with others. Some desirable personality traits employers may look for include attention to detail, reliability, creativity, general intelligence and a desire to learn.',
    'languages':
        'Employers looking to hire for a role that involves working with a diverse population may require job candidates to be proficient in certain languages. Employers may also specify the level of language proficiency, such as the ability to write and speak fluently. In some cases, basic knowledge of the language may be sufficient to perform the role, while other roles may have no language requirement at all.',
    'travel':
        'Some positions require a lot of travelling apart from commuting. Regular commute should be no part of this requirement type. This requirement type is typical for organizations with field operations, companies with offices in multiple locations, or those undertaking geographically dispersed projects. Employers hiring for such positions can state these requirements in the job posting to help attract candidates willing to travel outside their usual location. If the applicant does not list preferences for travelling, consider their travelling preferences to be fully matched with the job.',
    'location':
        'Employers hiring for open positions typically intend for the successful candidate to work in a specific location such as the head office, regional offices, or international subsidiaries. Job location is an important job requirement, as stating it can help find candidates able to work in certain places. For instance, candidates with young families may reconsider applying for international positions because of the potential disruption to their lives. Job positions may be on-site, remote or hybrid. If the applicant does not list preferences for the job location, consider their preferences to be fully matched with the job.',
    'working_hours':
        'Sometimes a job entails working very long hours or working on weekends. This is often the case for people in the medical or law field, but also for positions in business administration, like a sales manager or C-suite role. This point also considers the total work amount which can be part-time, full-time or contract work, for example. If the applicant does not list preferences for working hours, consider them fully matching for the job.',
    'physical_ability':
        'Some positions may involve a high physical demand. For example, these include positions in the army, machine operator, or nursing assistant as they typically involve spending long periods of time standing, moving, or lifting heavy objects. Employers hiring for such positions usually specify that candidates be physically fit so they can effectively complete their tasks. If the applicant does not list physical abilities, assume they are fully sufficient for this position.',
}


def get_sample_requirement() -> Requirement:
    return Requirement(type=RequirementType.MANDATORY.value, specification='Here should stand the specification text of the requirement')


def get_empty_requirements(requirement_type_definitions: dict[str, str]) -> dict[str, list[Requirement, ...]]:
    result_dict = {}
    for key in requirement_type_definitions.keys():
        result_dict[key] = []
    return result_dict


def get_prettify_prompt(text: str):
    return f'Please format the following text more nicely but do not change its contents. Group lines that belong together in a paragraph and format it to improve readability. This is the text:\n{text}'


def get_pdf_document_text(pdf_document_path: str,
                          replacements: tuple[tuple[str, str]] = ((chr(160), ' '),),
                          prettify: bool = True) -> str:
    with fitz.open(pdf_document_path) as pdf_document:
        page_texts = []
        for page in pdf_document:
            page_text = page.get_text().strip()
            for search_string, replacement_string in replacements:
                page_text = page_text.replace(search_string, replacement_string)
            page_texts.append(page_text)
        text = '\n'.join(page_texts)
    if prettify:
        answer = get_answer_message(get_prettify_prompt(text))
        text = answer.text
    return text


def extract_json_object_from_string(text: str) -> dict:
    json_start_string = text.find('{')
    json_end_string = text.rfind('}')
    if json_start_string != -1 and json_end_string != -1:
        try:
            return json.loads(text[json_start_string:json_end_string + 1])
        except json.JSONDecodeError:
            pass
    return {}


def get_prompt_to_extract_requirements(job_description: str, requirement_type_definitions: dict[str, str]) -> str:
    return f'Please extract the job requirements from the following job description as a JSON object and fill the requirements into the arrays in {get_empty_requirements(requirement_type_definitions)}. Please respect the type of the requirement. An explanation how to fill the arrays with the requirements of the correct type is provided here:\n{dumps(requirement_type_definitions)}.\nIf there are no suitable requirements for this category, the arrays can stay empty. All requirements must be unique. The JSON objects in the array must have the following structure {dumps(get_sample_requirement())} and the type must be either "{RequirementType.MANDATORY.value}" or "{RequirementType.OPTIONAL.value}". Here is the job description from which the described JSON object should be extracted: ${job_description.strip()}'


def get_requirements_from_job_description(
    job_description_pdf_file_path: str,
    requirement_type_definitions: dict[str, str],
) -> dict[str, list[Requirement, ...]]:
    # generate the extraction prompt
    job_description_text = get_pdf_document_text(job_description_pdf_file_path)
    prompt = get_prompt_to_extract_requirements(job_description_text, requirement_type_definitions)
    # send the prompt to the model
    answer = get_answer_message(prompt)
    # extract the JSON object from the answer
    extracted_json_object = extract_json_object_from_string(answer.text)
    # validate the structure and transform the JSON object from the answer
    job_requirements = get_empty_requirements(requirement_type_definitions)
    for requirement_type, requirements in extracted_json_object.items():
        if requirement_type not in job_requirements:
            # do not add unspecified requirement types
            continue
        if not isinstance(requirements, list):
            # the requirements should be given as a list
            continue
        for requirement in requirements:
            if not isinstance(requirement, dict):
                # each requirement should be an object
                continue
            if 'type' not in requirement or requirement['type'] not in [x.value for x in RequirementType]:
                # each requirement should have a suitable type and must be present
                continue
            if 'specification' not in requirement or not isinstance(requirement['specification'], str):
                # each requirement should have a specification which must be present
                continue
            # add the requirement
            job_requirements[requirement_type].append(Requirement(type=RequirementType(requirement['type']).value, specification=requirement['specification']))
    return job_requirements
