import openai
import json

# Set your OpenAI API key here
openai.api_key = ""  # Replace with your actual API key

def summarize_with_llm(metadata):
    return f"""
You are a senior software architect. Analyze this complete project structure and code base.
Based on the following data, please summarize:

1. What the project does (purpose/goal)
2. Key modules, classes, and functions
3. Technologies and dependencies used
4. Any architectural or design observations
5. Potential areas for improvement or refactoring
6. Any PHI or sensitive data found , any secrets detected stored in code or configuration files

Here is the complete project metadata and full file contents:

```json
{json.dumps(metadata, indent=2)}
```

Respond with a helpful, concise, and technical project summary.
"""

def chat_with_gpt(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=500,
        temperature=0.7,
    )
    return response.choices[0].message["content"].strip()

def summary_handler(data):
    prompt = summarize_with_llm(data)
    summary = chat_with_gpt(prompt)
    return summary

# Example usage
if __name__ == "__main__":
    with open("repo_metadata.json") as f:
        repo_model = json.load(f)

    for file in range(0,len(repo_model["files"])):
        repo_model['files'][file].pop('imports')


    prompt = summarize_with_llm(repo_model)
    summary = chat_with_gpt(prompt)

    print(summary)

    if summary:
        with open("repo_summary.json", "w") as f:
            json.dump({"summary": summary}, f, indent=2)
