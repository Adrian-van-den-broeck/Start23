"""Reference captures use the accepted 439 dpi setup above the focus breakpoint."""
from native_review_import import review
states = ['noPlan', 'selection', 'placement', 'pending', 'active', 'activePending', 'warning', 'rest', 'next', 'siblings']
for state in states: review.run_case(393, 1, 'nl', state)
review.run_case(393, 1, 'en', 'activePending')
