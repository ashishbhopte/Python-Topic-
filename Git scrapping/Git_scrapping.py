import requests
import re,json

def get_repos(username):
    url = f"https://api.github.com/users/{username}/repos"
    response = requests.get(url)
    response.raise_for_status()
    repos = response.json()
    return [repo['name'] for repo in repos]

def get_files(repo_name, username):
    url = f"https://api.github.com/repos/{username}/{repo_name}/git/trees/main?recursive=1"
    response = requests.get(url)
    if response.status_code == 404:
        url = f"https://api.github.com/repos/{username}/{repo_name}/git/trees/master?recursive=1"
        response = requests.get(url)
    response.raise_for_status()
    files = response.json()
    return [file['path'] for file in files['tree'] if file['type'] == 'blob']

def get_file_content(repo_name, username, file_path):
    url = f"https://raw.githubusercontent.com/{username}/{repo_name}/main/{file_path}"
    response = requests.get(url)
    if response.status_code == 404:
        url = f"https://raw.githubusercontent.com/{username}/{repo_name}/master/{file_path}"
        response = requests.get(url)
    response.raise_for_status()
    return response.text



def find_patterns(content, patterns):
    matches = {}
    for pattern_name, pattern in patterns.items():
        matches[pattern_name] = re.findall(pattern, content)
    return matches

import time
from tqdm import tqdm

def main(username, patterns):
    start_time = time.time()
    print("\033[94m" + "="*50)
    print(" " * 15 + "GitHub Scraper")
    print("="*50 + "\033[0m")
    print("\033[92mDeveloped by: sahwe, smoke-wolf, JDX-50S\033[0m")
    print("\033[94m" + "="*50 + "\033[0m")

    repos = get_repos(username)
    all_matches = {pattern_name: {} for pattern_name in patterns.keys()}

    files_to_scan = []
    total_lines_scanned = 0

    for repo in repos:
        try:
            files = get_files(repo, username)
            files_to_scan.extend([(repo, file) for file in files])
        except Exception as e:
            print(f"Failed to retrieve files for repo {repo}: {e}")

    with tqdm(total=len(files_to_scan), desc="Scanning files") as pbar:
        for repo, file in files_to_scan:
            try:
                content = get_file_content(repo, username, file)
                total_lines_scanned += len(content.split('\n'))
                matches = find_patterns(content, patterns)
                for pattern_name, match_list in matches.items():
                    if match_list:
                        if repo not in all_matches[pattern_name]:
                            all_matches[pattern_name][repo] = []
                        all_matches[pattern_name][repo].extend(match_list)
            except Exception as e:
                print(f"Failed to process file {file} in repo {repo}: {e}")
            pbar.update(1)

    end_time = time.time()
    elapsed_time = end_time - start_time
    avg_time_per_100_lines = (elapsed_time / total_lines_scanned) * 100 if total_lines_scanned else 0

    print("\033[94m" + "="*50 + "\033[0m")
    for pattern_name, repos in all_matches.items():
        print(f"\033[93mPattern: {pattern_name}\033[0m")
        for repo, matches in repos.items():
            print(f"\033[96mRepository: {repo}\033[0m")
            for match in matches:
                print(f"\033[96m{match}\033[0m")
            print("\033[94m" + "-"*50 + "\033[0m")
        print("\033[94m" + "="*50 + "\033[0m")

    print(f"\033[92mTotal time taken: {elapsed_time:.2f} seconds\033[0m")
    print(f"\033[92mTotal lines scanned: {total_lines_scanned}\033[0m")
    print(f"\033[92mAverage time per 100 lines: {avg_time_per_100_lines:.2f} seconds\033[0m")

    while True:
        print("\033[91mMenu:\033[0m")
        print("1. Export data as JSON")
        print("2. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            with open(f"{username}_matches.json", "w") as f:
                json.dump(all_matches, f, indent=4)
            print(f"Data exported to {username}_matches.json")
        elif choice == '2':
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    username = input("Enter the GitHub username: ")
    patterns = {
        "URLs": r'(https?://\S+)',
        "Emails": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        "Phone Numbers": r'\+?\d[\d -]{8,}\d',
        "API Keys": r'(?:api[_-]?key|api[_-]?token)[\'\"]?[:=][\'\"]?([a-zA-Z0-9-_]+)[\'\"]?',
        "Usernames": r'\buser(?:name)?[\'\"]?[:=][\'\"]?([a-zA-Z0-9-_]+)[\'\"]?',
        "Passwords": r'\bpass(?:word)?[\'\"]?[:=][\'\"]?([a-zA-Z0-9!@#$%^&*()_+={}[\]:;"\'<>.,?/`~\\-]+)[\'\"]?'
    }
    print("Select patterns to search for (comma separated):")
    for idx, pattern_name in enumerate(patterns.keys(), 1):
        print(f"{idx}. {pattern_name}")
    selected_indices = input("Enter your choices: ").split(",")
    selected_patterns = {name: pattern for idx, (name, pattern) in enumerate(patterns.items(), 1) if str(idx) in selected_indices}
    main(username, selected_patterns)