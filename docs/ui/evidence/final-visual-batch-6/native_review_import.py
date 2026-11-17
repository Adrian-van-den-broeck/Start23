from pathlib import Path
import importlib.util
spec = importlib.util.spec_from_file_location('week_review', Path(__file__).parent/'native-review.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
