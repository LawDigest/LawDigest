"""elections ORM 모델 패키지.

모든 모델을 임포트하여 Base.metadata에 등록한다.
"""

from lawdigest_data.elections.models.candidates import (  # noqa: F401
    Candidate,
    CandidateType,
    Winner,
)
from lawdigest_data.elections.models.codes import (  # noqa: F401
    DistrictCode,
    EduCode,
    ElectionCode,
    GusigunCode,
    JobCode,
    PartyCode,
    SgTypecode,
)
from lawdigest_data.elections.models.pledges import (  # noqa: F401
    ElectionPledge,
    PartyPolicy,
)
