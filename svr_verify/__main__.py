# svr_verify/__main__.py
# Allows: python -m svr_verify receipt.svr.json

import sys
from svr_verify.cli import main

sys.exit(main())
