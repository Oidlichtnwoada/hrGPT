from hrgpt.utils.score_utils import compute_total_score
from hrgpt.utils.type_utils import (
    JobRequirementType,
    RequirementMatch,
    Score,
    Requirement,
    RequirementType,
)


def test_compute_total_score() -> None:
    sample_requirement_matches: dict[JobRequirementType, list[RequirementMatch]] = {
        "work_experience": [
            RequirementMatch(
                score=Score(value=60, explanation=""),
                requirement=Requirement(
                    specification="", type=RequirementType.MANDATORY
                ),
            ),
            RequirementMatch(
                score=Score(value=40, explanation=""),
                requirement=Requirement(
                    specification="", type=RequirementType.MANDATORY
                ),
            ),
        ],
        "education": [
            RequirementMatch(
                score=Score(value=70, explanation=""),
                requirement=Requirement(
                    specification="", type=RequirementType.MANDATORY
                ),
            )
        ],
    }
    computed_total_score_value = compute_total_score(sample_requirement_matches)
    expected_total_score_value = 57.5
    assert computed_total_score_value == expected_total_score_value
