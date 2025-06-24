aider  --lint-cmd 'python: black' \
  --architect \
  --model openrouter/google/gemini-2.5-pro-preview-06-05 \
  --watch-files --notifications \
  --read AIDER_PROMPT.md \
  --test-cmd 'opensafely exec ehrql:v1 generate-dataset dataset_definition.py --output dataset.csv' \
  --auto-test

