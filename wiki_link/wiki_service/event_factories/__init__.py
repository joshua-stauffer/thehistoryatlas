"""Event factories for the wiki service."""

from .person_died import PersonDied
from .person_education_began import PersonEducationBegan
from .person_education_ended import PersonEducationEnded
from .person_left_position import PersonLeftPosition
from .person_moved_away_from import PersonMovedAwayFrom
from .person_moved_to import PersonMovedTo
from .person_participated_in import PersonParticipatedIn
from .person_received_academic_degree import PersonReceivedAcademicDegree
from .person_started_working_for import PersonStartedWorkingFor
from .person_stopped_working_for import PersonStoppedWorkingFor
from .person_took_position import PersonTookPosition
from .person_was_born import PersonWasBorn
from .work_of_art_created import WorkOfArtCreated
from .book_was_published import BookWasPublished
from wiki_service.event_factories.person_received_award import PersonReceivedAward
from .person_nominated_for import PersonNominatedFor
