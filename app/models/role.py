from enum import Enum

class Role(Enum):
    """ Role enumerator for Project Users """
    NO_ROLE = "No Role"
    MEMBER = "Member"
    REVIEWER = "Reviewer"
    OWNER = "Owner"

    @staticmethod
    def values() -> list:
        return list(map(lambda t: t.value, Role))
