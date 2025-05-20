from ducktools.lazyimporter import LazyImporter
from ducktools.lazyimporter.capture import capture_imports


laz = LazyImporter()

# These are actually imported lazily and do not exist within this module
with capture_imports(laz):
    import zipfile as zipfile
