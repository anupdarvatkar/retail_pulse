import requests
from bs4 import BeautifulSoup

def main():

    URL = "https://www.amazon.in/ASUS-3050-4GB-Keyboard-Graphite-FA506NCG-HN199W/dp/B0FM3C4L2F/?_encoding=UTF8&pd_rd_w=Qptth&content-id=amzn1.sym.aea64848-3ab9-4698-b7eb-c51ed2480b56&pf_rd_p=aea64848-3ab9-4698-b7eb-c51ed2480b56&pf_rd_r=CWSQR61Y5G9M17YHG2RD&pd_rd_wg=STWeY&pd_rd_r=43033c74-df5b-4e09-a4f0-87a5adbf4a75&ref_=pd_hp_d_btf_CEPC_Smartwatches&th=1"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.content, "html.parser")
    #print(soup.prettify())

    reviews = soup.find_all("div", {"a-expander-content reviewText review-text-content a-expander-partial-collapse-content"})
    #print(reviews)
    for review in reviews:
        print(f"---------------------{review.text.strip()}")


if __name__ == "__main__":
    main()
