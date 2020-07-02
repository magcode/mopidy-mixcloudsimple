import logging
import pathlib

import pkg_resources

from mopidy import config, ext

__version__ = pkg_resources.get_distribution("Mopidy-Mixcloudsimple").version

class Extension(ext.Extension):

    dist_name = "Mopidy-Mixcloudsimple"
    ext_name = "mixcloudsimple"
    version = __version__

    def get_default_config(self):
        return config.read(pathlib.Path(__file__).parent / "ext.conf")

    def get_config_schema(self):
        schema = super().get_config_schema()
        schema["account"] = config.String()
        return schema

    def setup(self, registry):
        
        from mopidy_mixcloudsimple.backend import MixcloudSimpleBackend
        registry.add("backend", MixcloudSimpleBackend)