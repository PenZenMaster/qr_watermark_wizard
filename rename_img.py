import os


def seo_friendly_name(original_name):
    # Example logic to extract keywords from the filename
    parts = original_name.lower().replace("_", "-").split("-")
    # Remove irrelevant parts like "img", dates, or generic terms
    keywords = [part for part in parts if part not in ["img", "highres", "2024", "08", "penzenmaster"]]
    # Join the remaining keywords into a new filename
    return "-".join(keywords) + ".jpg"


def rename_images(directory):
    for filename in os.listdir(directory):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            new_name = seo_friendly_name(filename)
            original_path = os.path.join(directory, filename)
            new_path = os.path.join(directory, new_name)
            os.rename(original_path, new_path)
            print(f'Renamed "{filename}" to "{new_name}"')


# Usage example
if __name__ == "__main__":
    directory_path = "path/to/your/images"  # Replace with your image folder path
    rename_images(directory_path)
