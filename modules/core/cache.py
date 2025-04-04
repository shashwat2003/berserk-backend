from modules.core.models import Role
from modules.core.types import CachedRolesType

CACHED_ROLES: CachedRolesType

try:
    CACHED_ROLES = {
        role["label"].replace(" ", "_").lower(): role["id"]
        for role in Role.objects.only("label", "id").values("label", "id")
    }
except:
    CACHED_ROLES = None
