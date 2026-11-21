from native_review_import import review
states=['noPlan','selection','placement','pending','active','activePending','warning','rest','next','siblings']
for state in states: review.run_case(393,1,'nl',state)
for width,font,language,state in [(320,2,'en','siblings'),(320,2,'nl','siblings'),(393,1,'en','reminder'),(320,2,'nl','reminder')]:
 review.run_case(width,font,language,state)
print('Final scroll correction: reference family and affected cases recaptured.',flush=True)
