find ./ -type f -name "*.py" -print0 | while IFS= read -r -d '' file; do
    mv "$file" "${file%.py}.md.text"
done
