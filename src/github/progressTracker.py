import json

def main():
    # Set the base path to your scrapers directory

    base_directory = 'src/scrapers'
    generate_json_from_structure(base_directory)

    json_file_path = 'src/github/scraper_status.json'
    generate_markdown_table(json_file_path)

    update_readme_with_status_table()


import os
from datetime import datetime

def generate_json_from_structure(base_path):
    # Define the structure of the JSON data
    data = []
    current_date = datetime.now().isoformat()

    for root, dirs, files in os.walk(base_path):
        # Use full path for file tracking
        full_path = root.split(os.sep)

        # Filter out organizing directories for country, jurisdiction, corpus identification
        effective_path = [dir for dir in full_path if not (dir.startswith("(") and dir.endswith(")"))]
        

        for file in files:
            if 'scrape' in file and len(effective_path) >= 4:
                # Parse the path to get country, jurisdiction, and corpus
                country = effective_path[-3]
                jurisdiction = effective_path[-2]
                corpus = effective_path[-1]
                file_path = os.path.join(root, file)  # Full path to the scrape.py file including organizational dirs

                # Append the new entry to the data list
                data.append({
                    "Country": country,
                    "Jurisdiction": jurisdiction,
                    "Corpus": corpus,
                    "FilePath": file_path,  # Add full file path to the JSON entry
                    "Status": "Refactoring",
                    "LastUpdated": current_date
                })
                break  # Assuming only one scrape.py per directory as mentioned

    # Sort the data by country and then by jurisdiction
    data_sorted = sorted(data, key=lambda x: (x['Country'], x['Jurisdiction']))

    # Write the sorted data to a JSON file
    with open("src/github/scraper_status.json", 'w') as json_file:
        json.dump(data_sorted, json_file, indent=4)

    print("JSON file generated successfully.")




def generate_markdown_table(json_filepath):
    try:
        # Load the data from the JSON file
        with open(json_filepath, 'r') as file:
            data = json.load(file)
        
        # Base URL for GitHub repository where the files are hosted
        base_url = "https://github.com/spartypkp/open-source-legislation/blob/main/"

        # Markdown table header
        header = "| Country | Jurisdiction | Corpus | Status | Last Updated | File Path |\n"
        divider = "|---------|--------------|--------|--------|--------------|-----------|\n"

        # Start the markdown output with the header and divider
        markdown_output = header + divider

        # Iterate through each entry in the JSON data
        for entry in data:
            country = entry['Country']
            jurisdiction = entry['Jurisdiction']
            corpus = entry['Corpus']
            status = entry['Status']
            last_updated = entry['LastUpdated']
            file_path = entry['FilePath']

            # Convert the file path to a clickable URL, assuming the path starts within the GitHub repo
            relative_path = file_path.split('open-source-legislation/')[-1]
            clickable_path = f"[view]({base_url + relative_path})"

            # Append each row to the markdown output
            markdown_output += f"| {country} | {jurisdiction} | {corpus} | {status} | {last_updated} | {clickable_path} |\n"

        # Write the complete markdown table to a file
        with open("src/github/status_table.md", "w") as write_file:
            write_file.write(markdown_output)

    except Exception as e:
        raise Exception(f"Error reading the JSON file or generating the table: {str(e)}")


def update_readme_with_status_table():
    # Read the status table content from its Markdown file
    with open('src/github/status_table.md', 'r') as table_file:
        status_table = table_file.read()

    # Read the current README content
    with open('README.md', 'r') as readme_file:
        readme_content = readme_file.readlines()

    # Identify the start index right after the "## Supported Legislation" header
    start_index = readme_content.index('## Supported Legislation\n') + 1

    # Identify the end index right before the "Legislation status tracked in real time." sentence
    end_index = readme_content.index('Legislation status tracked in real time.\n')

    # Replace the old table or placeholder with the new table
    updated_readme = readme_content[:start_index] + [status_table + '\n'] + readme_content[end_index:]

    # Write the updated content back to the README file
    with open('README.md', 'w') as readme_file:
        readme_file.writelines(updated_readme)




if __name__ == "__main__":
    # Example of using the function with a JSON file path
    main()
