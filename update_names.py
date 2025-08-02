import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Here we set the website link where we collect the data
BASE_URL = "https://example-website.com"

def get_company_info_by_code(code):
    # This is the search URL for a company code
    search_url = f"{BASE_URL}/otsing/{code}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None, None

        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.find_all("a", href=True)

        company_links = []
        for a in results:
            href = a['href']
            # Looking for the link that starts with / and matches the company code
            if href.startswith("/") and href[1:].split("-")[0] == str(code):
                company_links.append(href)

        if not company_links:
            return None, None

        # Open the first matching company link
        company_url = BASE_URL + company_links[0]
        company_resp = requests.get(company_url, headers=headers, timeout=10)
        if company_resp.status_code != 200:
            return None, None

        company_soup = BeautifulSoup(company_resp.text, "html.parser")

        # Get the company name from the page
        h1_tag = company_soup.find("h1")
        company_name = h1_tag.text.strip() if h1_tag else None

        # Try to find the company status
        status_tag = None
        possible_status_classes = ["status", "company-status", "company__status", "state"]
        for cls in possible_status_classes:
            status_tag = company_soup.find(class_=cls)
            if status_tag:
                break

        if status_tag:
            company_status = status_tag.text.strip()
        else:
            # If not found by class, try to find keywords in the page text
            text = company_soup.get_text(separator="\n")
            lines = text.split("\n")
            company_status = None
            for line in lines:
                line = line.strip()
                if any(keyword in line.lower() for keyword in ["kustutatud", "registrisse kantud", "pankrotis", "aktiivne"]):
                    company_status = line
                    break

        return company_name, company_status

    except Exception as e:
        print(f"[!] Code {code}: exception — {e}")
        return None, None

def main():
    df = pd.read_excel("test_fars.xlsx")

    new_names = []
    new_statuses = []
    total = len(df)
    for idx, row in df.iterrows():
        raw_codes = str(row['code'])
        codes = [c.strip() for c in raw_codes.split(';') if c.strip()]
        names = []
        statuses = []

        print(f"[{idx+1}/{total}] Processing: {raw_codes}")
        for code in codes:
            name, status = get_company_info_by_code(code)
            names.append(name if name else "")
            statuses.append(status if status else "")
            time.sleep(1)  # wait between requests

        new_names.append(";".join(names))
        new_statuses.append(";".join(statuses))

    df['new_name'] = new_names
    df['status'] = new_statuses
    df.to_excel("test_fars_updated.xlsx", index=False)
    print("Done! Results saved to test_fars_updated.xlsx")

if __name__ == "__main__":
    main()
