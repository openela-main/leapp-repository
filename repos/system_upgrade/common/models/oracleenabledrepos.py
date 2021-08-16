from leapp.models import Model, fields
from leapp.topics import SystemFactsTopic


class OracleEnabledRepos(Model):
    """
    The model represents information about repos to enable

    """

    topic = SystemFactsTopic

    """
    This field initially will contain repos enabled on the
    leapp upgrade command line

    """

    enabled_repos = fields.String()
