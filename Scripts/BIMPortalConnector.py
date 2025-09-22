import requests

BASE_URL = "https://via.bund.de/bim/aia/api/v1/public/domainSpecificModel"

def fetch_domain_specific_models():
    """Fetch all domain specific models with a POST request."""
    response = requests.post(
        BASE_URL,
        headers={"accept": "application/json", "Content-Type": "application/json"},
        json={}  # empty JSON body as required
    )
    response.raise_for_status()
    return response.json()

def download_ids_xml(guid: str, filename: str = "first_domain_model.ids"):
    """Download XML IDS data for the given guid and save to a file."""
    url = f"{BASE_URL}/{guid}/IDS"
    response = requests.get(
        url,
        headers={"accept": "*/*"}
    )
    response.raise_for_status()
    with open(filename, "wb") as f:
        f.write(response.content)
    print(f"✅ IDS XML saved as {filename}")

def main():
    # Step 1: Fetch all models
    models = fetch_domain_specific_models()
    if not models:
        print("No domainSpecificModels found.")
        return

    # Step 2: Pick the first model's guid
    # TODO: select from list of domain models in BonsaiBIM
    print("Wähle aus folgenden Fachmodellen aus:")
    for model in models:
        print(model["name"] + " (" + model["guid"] + ")")

    first_model = models[0]
    guid = first_model.get("guid") or first_model.get("id")  # adapt depending on API response
    name = first_model.get("name")
    if not guid:
        print("Could not find GUID in the first model:", first_model)
        return

    print(f"Fetching IDS for guid: {guid}")

    # Step 3: Download IDS XML
    download_ids_xml(guid, name + ".ids")

if __name__ == "__main__":
    main()
