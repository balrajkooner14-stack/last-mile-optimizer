# ortools must be imported before anything that loads Anaconda's system protobuf
# (e.g. pandas). On macOS the dynamic linker picks up the wrong libprotobuf.29
# if ortools' bundled .libs/ isn't loaded first, causing a symbol-not-found crash.
from ortools.constraint_solver import pywrapcp  # noqa: F401
import pandas  # noqa: F401
