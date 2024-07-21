import json

def main():
    # Set the base path to your scrapers directory

    base_directory = 'src/scrapers'
    generate_json_from_structure(base_directory)

    json_file_path = 'src/github/scraper_status.json'
    status_table = generate_markdown_table(json_file_path)

    update_readme_with_status_table(status_table)


import os
from datetime import datetime



def generate_json_from_structure(base_path):
    # Define the structure of the JSON data
    data = []
    current_date = datetime.now().isoformat()

    json_metadata = {}
    with open(f"src/utils/legislation_metadata.json", "r") as read_file:
        text = read_file.read()
    json_metadata = json.loads(text)

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
                parent_directory = root  # Parent directory of the scrape.py file
                
                # Newly added country found in file path, update metadata
                if country not in json_metadata:
                    json_metadata[country] = {"description": "PLACEHOLDER!"}
                
                # Newly added jurisdiction found in file path
                if jurisdiction not in json_metadata[country]:
                    json_metadata[country][jurisdiction] = {"description": "PLACEHOLDER!"}
                
                # Newly added corpus (and scraper!)
                if corpus not in json_metadata[country][jurisdiction]:
                    json_metadata[country][jurisdiction][corpus] = {
                        "description": "PLACEHOLDER!", 
                        "download_link_available": False,
                        "status": "Planning",
                        "status_description": "Initial planning - new corpus found",
                        "last_updated": current_date,
                        "file_path": parent_directory
                    }
                # Update old schema, temporary
                if "file_path" not in json_metadata[country][jurisdiction][corpus]:
                    json_metadata[country][jurisdiction][corpus]["file_path"] = parent_directory

                print(f"Country: {country}, Jurisdiction: {jurisdiction}, Corpus: {corpus}")
                print(f"Test", json_metadata[country][jurisdiction])


                if json_metadata[country][jurisdiction][corpus]["download_link_available"]:
                    download_link = f"[download](https://jwscgsmkadanioyopaef.supabase.co/storage/v1/object/public/open-source-legislation/{country}/{jurisdiction}/{corpus}/{country}_{jurisdiction}_{corpus}.sql)"
                else:
                    download_link = "N/A"

                # Append the new entry to the data list
                data.append({
                    "Country": country,
                    "Country_description": json_metadata[country]['description'],
                    "Jurisdiction": jurisdiction,
                    "Jurisdiction_description": json_metadata[country][jurisdiction]['description'],
                    "Corpus": corpus,
                    "Corpus_description": json_metadata[country][jurisdiction][corpus]['description'],
                    "FilePath": parent_directory,  # Add parent directory path to the JSON entry
                    "Status": json_metadata[country][jurisdiction][corpus]["status"] ,
                    "DevComment": json_metadata[country][jurisdiction][corpus]["status_description"],
                    "LastUpdated": json_metadata[country][jurisdiction][corpus]["last_updated"],
                    "DownloadLink": download_link
                })
                break  # Assuming only one scrape.py per directory as mentioned

    # Sort the data by country and then by jurisdiction
    data_sorted = sorted(data, key=lambda x: (x['Country'], x['Jurisdiction']))

    # Write the sorted data to a JSON file
    with open("src/github/scraper_status.json", 'w') as json_file:
        json.dump(data_sorted, json_file, indent=4)
    
    # Write updated metadata to JSON file
    with open("src/utils/legislation_metadata.json", "w") as write_file:
        json.dump(json_metadata, write_file, indent=4) 

    print("JSON files updated successfully.")


def generate_markdown_table(json_filepath):
    try:
        # Load the data from the JSON file
        with open(json_filepath, 'r') as file:
            data = json.load(file)
        
        # Base URL for GitHub repository where the files are hosted
        base_url = "https://github.com/spartypkp/open-source-legislation/blob/main/"

        # Markdown table header
        

        header = "| Country | Jurisdiction | Corpus | | Status   |  Download | Source Code |\n"
        divider = "|-------------|--------------|------------------|---|-------------|--------------|-------------|\n"

        # Start the markdown output with the header and divider
        markdown_output = header + divider

        # Iterate through each entry in the JSON data
        for entry in data:
            country = f"{entry['Country']} - {entry['Country_description']}"
            jurisdiction = f"{entry['Jurisdiction']} - {entry['Jurisdiction_description']}"
            corpus = f"{entry['Corpus_description']}"
            status = entry['Status']
            dev_comment = entry['DevComment']
            last_updated = entry['LastUpdated']
            file_path = entry['FilePath']
            download_link = entry['DownloadLink']

            # I think this breaks the table :( Remove for now
            if status == "Complete":
                status_emoji = "🟢"
            elif status == "Refactoring":
                status_emoji = "🟠"
            elif status == "In Progress":
                status_emoji = "🔵"
            elif status == "Testing":
                status_emoji = "🟡"
            else:
                status_emoji = "🔴"
            


            # Convert the file path to a clickable URL, assuming the path starts within the GitHub repo
            relative_path = file_path.split('open-source-legislation/')[-1]
            clickable_path = f"[view]({base_url + relative_path})"
            

            # Append each row to the markdown output
            markdown_output += f"| {country} | {jurisdiction} | {corpus} | {status_emoji} | {status} | {download_link} |  {clickable_path} |\n"

        # Write the complete markdown table to a file
        with open("src/github/status_table.md", "w") as write_file:
            write_file.write(markdown_output)
        return markdown_output

    except Exception as e:
        raise Exception(f"Error reading the JSON file or generating the table: {str(e)}")


def update_readme_with_status_table(status_table):
    # Read the status table content from its Markdown file
    

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
