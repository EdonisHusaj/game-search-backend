from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

def is_exact_match(query, title):
    """
    Check if the query is an exact or close match to the title.
    """
    # Normalize both query and title by removing special characters and converting to lowercase
    query_normalized = re.sub(r'[^a-zA-Z0-9\s]', '', query).lower().strip()
    title_normalized = re.sub(r'[^a-zA-Z0-9\s]', '', title).lower().strip()

    # Split the query and title into words
    query_words = query_normalized.split()
    title_words = title_normalized.split()

    # Check if all query words are present in the title
    return all(word in title_words for word in query_words)

def scrape_website(query, site):
    if site == "skidrowreloaded.com":
        search_url = f"https://www.skidrowreloaded.com/?s={query}"
    elif site == "fitgirl-repacks.site":
        search_url = f"https://fitgirl-repacks.site/?s={query}"
    else:
        return []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        results = []
        if site == "skidrowreloaded.com":
            for item in soup.select("div.post"):
                title = item.find("h2").text.strip() if item.find("h2") else "No title"
                link = item.find("a")["href"] if item.find("a") else "#"
                # Filter results to match the exact query
                if is_exact_match(query, title) and link != "#":
                    results.append({"title": title, "link": link})
        elif site == "fitgirl-repacks.site":
            for item in soup.select("article.post"):
                title_element = item.find("h1", class_="entry-title")
                if title_element:
                    title = title_element.text.strip()
                    link = title_element.find("a")["href"]
                    if not link.startswith("http"):
                        link = f"https://fitgirl-repacks.site{link}"
                else:
                    title = "No title"
                    link = "#"
                # Filter results to match the exact query
                if is_exact_match(query, title) and link != "#":
                    results.append({"title": title, "link": link})
        
        return results
    except Exception as e:
        print(f"Error scraping {site}: {e}")
        return []

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/search")
def search():
    query = request.args.get("query")
    if query:
        skidrow_results = scrape_website(query, "skidrowreloaded.com")
        fitgirl_results = scrape_website(query, "fitgirl-repacks.site")
        return jsonify({
            "skidrow": skidrow_results,
            "fitgirl": fitgirl_results
        })
    return jsonify({"skidrow": [], "fitgirl": []})

if __name__ == "__main__":
    app.run(debug=True)