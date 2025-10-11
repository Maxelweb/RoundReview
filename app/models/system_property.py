from enum import Enum

class SystemProperty(Enum):
    PROJECT_CREATE_DISABLED = "PROJECT_CREATE_DISABLED"
    OBJECT_DELETE_DISABLED = "OBJECT_DELETE_DISABLED"
    USER_LOGIN_DISABLED = "USER_LOGIN_DISABLED"
    OBJECT_MAX_UPLOAD_SIZE_MB = "OBJECT_MAX_UPLOAD_SIZE_MB"
    WEBHOOKS_DISABLED = "WEBHOOKS_DISABLED"

    def description(self) -> str:
        return SystemPropertyInfo[self.name].value
    
    def check_value(self, value:str) -> bool:
        """ Check if the value is valid for the property """
        if self in [SystemProperty.PROJECT_CREATE_DISABLED, SystemProperty.OBJECT_DELETE_DISABLED, SystemProperty.USER_LOGIN_DISABLED, SystemProperty.WEBHOOKS_DISABLED]:
            return value in ["TRUE", "FALSE"]
        elif self == SystemProperty.OBJECT_MAX_UPLOAD_SIZE_MB:
            try:
                size = int(value)
                return 0 <= size <= 16
            except ValueError:
                return False
        return False

class SystemPropertyInfo(Enum):
    PROJECT_CREATE_DISABLED = "If TRUE, project creation is disabled for any user, FALSE by default."
    OBJECT_DELETE_DISABLED = "If TRUE, object delete is disabled for any user. FALSE by default"
    USER_LOGIN_DISABLED = "If TRUE, only admins can sign in. FALSE by default"
    OBJECT_MAX_UPLOAD_SIZE_MB = "Set the max upload size for objects in Megabytes. Maximum size: 16 (MB)."
    WEBHOOKS_DISABLED = "If TRUE, webhooks are disabled for any user, FALSE by default."
